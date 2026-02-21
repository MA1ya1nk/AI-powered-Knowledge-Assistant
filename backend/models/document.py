# models/document.py
from datetime import datetime, timezone

def create_document(user_id, filename, original_name, file_type, file_size):
    return {
        "user_id": user_id,
        "filename": filename,
        "original_name": original_name,
        "file_type": file_type,
        "file_size": file_size,
        "status": "processing",  # processing | ready | error | disabled
        "chunk_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
        "error_message": None
    }

def document_to_dict(doc):
    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "filename": doc["filename"],
        "original_name": doc["original_name"],
        "file_type": doc["file_type"],
        "file_size": doc["file_size"],
        "status": doc.get("status", "processing"),
        "chunk_count": doc.get("chunk_count", 0),
        "is_active": doc.get("is_active", True),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        "error_message": doc.get("error_message")
    }

def create_chunk(document_id, user_id, content, chunk_index, embedding=None):
    return {
        "document_id": document_id,
        "user_id": user_id,
        "content": content,
        "chunk_index": chunk_index,
        "embedding": embedding,
        "token_count": len(content.split()),
        "created_at": datetime.now(timezone.utc)
    }