# routes/documents.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timezone
import os
import uuid
import threading
import logging

from models.document import create_document, document_to_dict, create_chunk
from utils.chunker import extract_text, chunk_text
from utils.embeddings import generate_embeddings_batch
from config import config

documents_bp = Blueprint('documents', __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_document_async(app, document_id, file_path, file_type, user_id):
    """Process document in background thread."""
    with app.app_context():
        db = app.db
        try:
            # Extract text
            logger.info(f"Extracting text from {file_path}")
            text = extract_text(file_path, file_type)
            
            if not text:
                raise Exception("No text could be extracted from document")
            
            # Chunk text
            chunks = chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from document")
            
            if not chunks:
                raise Exception("Document produced no chunks")
            
            # Generate embeddings in batch
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = generate_embeddings_batch(chunks)
            
            # Store chunks
            chunk_docs = []
            for i, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_docs.append(create_chunk(
                    document_id=document_id,
                    user_id=user_id,
                    content=chunk_content,
                    chunk_index=i,
                    embedding=embedding
                ))
            
            if chunk_docs:
                db.document_chunks.insert_many(chunk_docs)
            
            # Update document status
            db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {
                    "status": "ready",
                    "chunk_count": len(chunks),
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
        finally:
            # Clean up file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and TXT files are allowed"}), 400
    
    # Save file
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(config.UPLOAD_FOLDER, unique_filename)
    
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    
    db = current_app.db
    doc = create_document(
        user_id=user_id,
        filename=unique_filename,
        original_name=file.filename,
        file_type=file_ext,
        file_size=file_size
    )
    result = db.documents.insert_one(doc)
    doc['_id'] = result.inserted_id
    document_id = str(result.inserted_id)
    
    # Process async
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=process_document_async,
        args=(app, document_id, file_path, file_ext, user_id)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": "Document uploaded. Processing in background.",
        "document": document_to_dict(doc)
    }), 201

@documents_bp.route('/list', methods=['GET'])
@jwt_required()
def list_documents():
    user_id = get_jwt_identity()
    db = current_app.db
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    skip = (page - 1) * limit
    
    docs = list(db.documents.find(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    ).skip(skip).limit(limit))
    
    total = db.documents.count_documents({"user_id": user_id})
    
    return jsonify({
        "documents": [document_to_dict(d) for d in docs],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    })

@documents_bp.route('/<document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    user_id = get_jwt_identity()
    db = current_app.db
    
    try:
        doc = db.documents.find_one({
            "_id": ObjectId(document_id),
            "user_id": user_id
        })
    except:
        return jsonify({"error": "Invalid document ID"}), 400
    
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify({"document": document_to_dict(doc)})

@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    user_id = get_jwt_identity()
    db = current_app.db
    
    try:
        doc = db.documents.find_one({
            "_id": ObjectId(document_id),
            "user_id": user_id
        })
    except:
        return jsonify({"error": "Invalid document ID"}), 400
    
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    
    # Delete chunks
    db.document_chunks.delete_many({"document_id": document_id})
    # Delete document
    db.documents.delete_one({"_id": ObjectId(document_id)})
    
    return jsonify({"message": "Document deleted successfully"})

@documents_bp.route('/<document_id>/status', methods=['GET'])
@jwt_required()
def check_status(document_id):
    user_id = get_jwt_identity()
    db = current_app.db
    
    try:
        doc = db.documents.find_one({
            "_id": ObjectId(document_id),
            "user_id": user_id
        }, {"status": 1, "chunk_count": 1, "error_message": 1})
    except:
        return jsonify({"error": "Invalid document ID"}), 400
    
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify({
        "status": doc.get("status"),
        "chunk_count": doc.get("chunk_count", 0),
        "error_message": doc.get("error_message")
    })