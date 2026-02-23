# # routes/chat.py
# from flask import Blueprint, request, jsonify, current_app
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from bson import ObjectId
# from datetime import datetime, timezone
# import logging

# from models.chat import create_session, create_message, message_to_dict, session_to_dict
# from utils.rag import retrieve_relevant_chunks, generate_answer, generate_session_title

# chat_bp = Blueprint('chat', __name__)
# logger = logging.getLogger(__name__)

# @chat_bp.route('/ask', methods=['POST'])
# @jwt_required()
# def ask():
#     user_id = get_jwt_identity()
#     data = request.get_json()
    
#     if not data:
#         return jsonify({"error": "No data provided"}), 400
    
#     question = data.get('question', '').strip()
#     session_id = data.get('session_id')
    
#     if not question:
#         return jsonify({"error": "Question is required"}), 400
    
#     if len(question) > 2000:
#         return jsonify({"error": "Question too long (max 2000 characters)"}), 400
    
#     db = current_app.db
    
#     # Get or create session
#     if session_id:
#         try:
#             session = db.chat_sessions.find_one({
#                 "_id": ObjectId(session_id),
#                 "user_id": user_id
#             })
#         except:
#             session = None
        
#         if not session:
#             return jsonify({"error": "Session not found"}), 404
#     else:
#         # Create new session
#         title = generate_session_title(question)
#         session_doc = create_session(user_id, title)
#         result = db.chat_sessions.insert_one(session_doc)
#         session_id = str(result.inserted_id)
#         session_doc['_id'] = result.inserted_id
#         session = session_doc
    
#     # Get chat history for context
#     history_msgs = list(db.messages.find(
#         {"session_id": str(session["_id"])},
#         sort=[("created_at", 1)]
#     ).limit(10))
    
#     history = [{"role": m["role"], "content": m["content"]} for m in history_msgs]
    
#     # Save user message
#     user_msg = create_message(
#         session_id=str(session["_id"]),
#         user_id=user_id,
#         role="user",
#         content=question
#     )
#     user_msg_result = db.messages.insert_one(user_msg)
#     user_msg['_id'] = user_msg_result.inserted_id
    
#     # RAG pipeline
#     try:
#         logger.info(f"Retrieving chunks for question: {question[:100]}")
#         context_chunks = retrieve_relevant_chunks(db, question, user_id=user_id)
        
#         logger.info(f"Generating answer with {len(context_chunks)} context chunks")
#         result = generate_answer(question, context_chunks, history)
        
#         answer = result["answer"]
#         sources = result["sources"]
#         tokens_used = result["tokens_used"]
        
#     except Exception as e:
#         logger.error(f"RAG pipeline error: {e}")
#         answer = f"An error occurred while generating the answer: {str(e)}"
#         sources = []
#         tokens_used = 0
    
#     # Save assistant message
#     assistant_msg = create_message(
#         session_id=str(session["_id"]),
#         user_id=user_id,
#         role="assistant",
#         content=answer,
#         sources=sources,
#         tokens_used=tokens_used
#     )
#     assistant_msg_result = db.messages.insert_one(assistant_msg)
#     assistant_msg['_id'] = assistant_msg_result.inserted_id
    
#     # Update session
#     db.chat_sessions.update_one(
#         {"_id": session["_id"]},
#         {"$set": {
#             "updated_at": datetime.now(timezone.utc)
#         },
#         "$inc": {"message_count": 2}}
#     )
    
#     # Update user token usage
#     db.users.update_one(
#         {"_id": ObjectId(user_id)},
#         {"$inc": {
#             "total_queries": 1,
#             "total_tokens_used": tokens_used
#         }}
#     )
    
#     return jsonify({
#         "session_id": str(session["_id"]),
#         "session_title": session.get("title", "Conversation"),
#         "user_message": message_to_dict(user_msg),
#         "assistant_message": message_to_dict(assistant_msg),
#         "sources": sources,
#         "tokens_used": tokens_used
#     })

# @chat_bp.route('/sessions', methods=['GET'])
# @jwt_required()
# def list_sessions():
#     user_id = get_jwt_identity()
#     db = current_app.db
    
#     page = int(request.args.get('page', 1))
#     limit = int(request.args.get('limit', 20))
#     skip = (page - 1) * limit
    
#     sessions = list(db.chat_sessions.find(
#         {"user_id": user_id},
#         sort=[("updated_at", -1)]
#     ).skip(skip).limit(limit))
    
#     total = db.chat_sessions.count_documents({"user_id": user_id})
    
#     return jsonify({
#         "sessions": [session_to_dict(s) for s in sessions],
#         "total": total,
#         "page": page
#     })

# @chat_bp.route('/sessions/<session_id>', methods=['GET'])
# @jwt_required()
# def get_session(session_id):
#     user_id = get_jwt_identity()
#     db = current_app.db
    
#     try:
#         session = db.chat_sessions.find_one({
#             "_id": ObjectId(session_id),
#             "user_id": user_id
#         })
#     except:
#         return jsonify({"error": "Invalid session ID"}), 400
    
#     if not session:
#         return jsonify({"error": "Session not found"}), 404
    
#     messages = list(db.messages.find(
#         {"session_id": session_id},
#         sort=[("created_at", 1)]
#     ))
    
#     return jsonify({
#         "session": session_to_dict(session),
#         "messages": [message_to_dict(m) for m in messages]
#     })

# @chat_bp.route('/sessions/<session_id>', methods=['DELETE'])
# @jwt_required()
# def delete_session(session_id):
#     user_id = get_jwt_identity()
#     db = current_app.db
    
#     try:
#         session = db.chat_sessions.find_one({
#             "_id": ObjectId(session_id),
#             "user_id": user_id
#         })
#     except:
#         return jsonify({"error": "Invalid session ID"}), 400
    
#     if not session:
#         return jsonify({"error": "Session not found"}), 404
    
#     db.messages.delete_many({"session_id": session_id})
#     db.chat_sessions.delete_one({"_id": ObjectId(session_id)})
    
#     return jsonify({"message": "Session deleted successfully"})

# @chat_bp.route('/history', methods=['GET'])
# @jwt_required()
# def get_history():
#     user_id = get_jwt_identity()
#     db = current_app.db
    
#     # Get recent messages across all sessions
#     messages = list(db.messages.find(
#         {"user_id": user_id},
#         sort=[("created_at", -1)]
#     ).limit(50))
    
#     return jsonify({
#         "messages": [message_to_dict(m) for m in messages]
#     })


# routes/chat.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timezone
import logging
from models.chat import create_session, create_message, message_to_dict, session_to_dict
from utils.rag import retrieve_relevant_chunks, generate_answer, generate_session_title

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

@chat_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question:
        return jsonify({"error": "Question is required"}), 400
    if len(question) > 2000:
        return jsonify({"error": "Question too long (max 2000 characters)"}), 400

    db = current_app.db

    # Get or create session — strictly tied to user_id
    if session_id:
        try:
            session = db.chat_sessions.find_one({
                "_id": ObjectId(session_id),
                "user_id": user_id  # ← must belong to THIS user
            })
        except:
            session = None
        if not session:
            return jsonify({"error": "Session not found"}), 404
    else:
        title = generate_session_title(question)
        session_doc = create_session(user_id, title)
        result = db.chat_sessions.insert_one(session_doc)
        session_id = str(result.inserted_id)
        session_doc['_id'] = result.inserted_id
        session = session_doc

    # Get only THIS session's history
    history_msgs = list(db.messages.find(
        {
            "session_id": str(session["_id"]),
            "user_id": user_id  # ← only this user's messages
        },
        sort=[("created_at", 1)]
    ).limit(10))
    history = [{"role": m["role"], "content": m["content"]} for m in history_msgs]

    # Save user message
    user_msg = create_message(
        session_id=str(session["_id"]),
        user_id=user_id,
        role="user",
        content=question
    )
    user_msg_result = db.messages.insert_one(user_msg)
    user_msg['_id'] = user_msg_result.inserted_id

    # RAG — only search THIS user's documents
    try:
        context_chunks = retrieve_relevant_chunks(
            db, question, user_id=user_id
        )
        result = generate_answer(question, context_chunks, history)
        answer = result["answer"]
        sources = result["sources"]
        tokens_used = result["tokens_used"]
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        answer = f"An error occurred: {str(e)}"
        sources = []
        tokens_used = 0

    # Save assistant message
    assistant_msg = create_message(
        session_id=str(session["_id"]),
        user_id=user_id,
        role="assistant",
        content=answer,
        sources=sources,
        tokens_used=tokens_used
    )
    assistant_msg_result = db.messages.insert_one(assistant_msg)
    assistant_msg['_id'] = assistant_msg_result.inserted_id

    # Update session stats
    db.chat_sessions.update_one(
        {"_id": session["_id"]},
        {
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$inc": {"message_count": 2}
        }
    )

    # Update user token usage
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"total_queries": 1, "total_tokens_used": tokens_used}}
    )

    return jsonify({
        "session_id": str(session["_id"]),
        "session_title": session.get("title", "Conversation"),
        "user_message": message_to_dict(user_msg),
        "assistant_message": message_to_dict(assistant_msg),
        "sources": sources,
        "tokens_used": tokens_used
    })

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required()
def list_sessions():
    user_id = get_jwt_identity()
    db = current_app.db
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    skip = (page - 1) * limit

    # ONLY return sessions belonging to this user
    sessions = list(db.chat_sessions.find(
        {"user_id": user_id},  # ← strict filter
        sort=[("updated_at", -1)]
    ).skip(skip).limit(limit))

    total = db.chat_sessions.count_documents({"user_id": user_id})

    return jsonify({
        "sessions": [session_to_dict(s) for s in sessions],
        "total": total,
        "page": page
    })

@chat_bp.route('/sessions/<session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    user_id = get_jwt_identity()
    db = current_app.db

    try:
        # Must belong to THIS user
        session = db.chat_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id  # ← strict filter
        })
    except:
        return jsonify({"error": "Invalid session ID"}), 400

    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Only get messages for this session AND this user
    messages = list(db.messages.find(
        {
            "session_id": session_id,
            "user_id": user_id  # ← strict filter
        },
        sort=[("created_at", 1)]
    ))

    return jsonify({
        "session": session_to_dict(session),
        "messages": [message_to_dict(m) for m in messages]
    })

@chat_bp.route('/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    user_id = get_jwt_identity()
    db = current_app.db

    try:
        session = db.chat_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id  # ← strict filter
        })
    except:
        return jsonify({"error": "Invalid session ID"}), 400

    if not session:
        return jsonify({"error": "Session not found"}), 404

    db.messages.delete_many({"session_id": session_id, "user_id": user_id})
    db.chat_sessions.delete_one({"_id": ObjectId(session_id)})

    return jsonify({"message": "Session deleted successfully"})

@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    db = current_app.db

    # ONLY this user's messages
    messages = list(db.messages.find(
        {"user_id": user_id},  # ← strict filter
        sort=[("created_at", -1)]
    ).limit(50))

    return jsonify({
        "messages": [message_to_dict(m) for m in messages]
    })