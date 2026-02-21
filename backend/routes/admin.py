# routes/admin.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timezone
import logging

from middleware.auth_middleware import require_admin
from models.user import user_to_dict
from models.document import document_to_dict

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_stats():
    db = current_app.db
    
    total_users = db.users.count_documents({})
    total_docs = db.documents.count_documents({})
    total_chunks = db.document_chunks.count_documents({})
    total_sessions = db.chat_sessions.count_documents({})
    total_messages = db.messages.count_documents({})
    
    # Token usage aggregate
    pipeline = [
        {"$group": {
            "_id": None,
            "total_tokens": {"$sum": "$total_tokens_used"},
            "total_queries": {"$sum": "$total_queries"}
        }}
    ]
    usage = list(db.users.aggregate(pipeline))
    token_data = usage[0] if usage else {"total_tokens": 0, "total_queries": 0}
    
    # Docs by status
    docs_by_status = {}
    for status in ["ready", "processing", "error", "disabled"]:
        docs_by_status[status] = db.documents.count_documents({"status": status})
    
    # Recent activity
    recent_messages = list(db.messages.find(
        {"role": "user"},
        sort=[("created_at", -1)]
    ).limit(10))
    
    return jsonify({
        "users": {
            "total": total_users,
            "active": db.users.count_documents({"is_active": True})
        },
        "documents": {
            "total": total_docs,
            "by_status": docs_by_status,
            "total_chunks": total_chunks
        },
        "conversations": {
            "total_sessions": total_sessions,
            "total_messages": total_messages
        },
        "usage": {
            "total_tokens": token_data.get("total_tokens", 0),
            "total_queries": token_data.get("total_queries", 0),
            "estimated_cost_usd": round(token_data.get("total_tokens", 0) * 0.000002, 4)
        },
        "recent_queries": [
            {
                "content": m["content"][:100],
                "user_id": m["user_id"],
                "created_at": m["created_at"].isoformat()
            }
            for m in recent_messages
        ]
    })

@admin_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    db = current_app.db
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    skip = (page - 1) * limit
    
    users = list(db.users.find(
        {},
        sort=[("created_at", -1)]
    ).skip(skip).limit(limit))
    
    total = db.users.count_documents({})
    
    return jsonify({
        "users": [user_to_dict(u) for u in users],
        "total": total,
        "page": page
    })

@admin_bp.route('/users/<user_id>/toggle', methods=['PUT'])
@require_admin
def toggle_user(user_id):
    db = current_app.db
    
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except:
        return jsonify({"error": "Invalid user ID"}), 400
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    current_admin_id = get_jwt_identity()
    if str(user["_id"]) == current_admin_id:
        return jsonify({"error": "Cannot disable your own account"}), 400
    
    new_status = not user.get("is_active", True)
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status}}
    )
    
    return jsonify({
        "message": f"User {'enabled' if new_status else 'disabled'} successfully",
        "is_active": new_status
    })

@admin_bp.route('/documents', methods=['GET'])
@require_admin
def list_all_documents():
    db = current_app.db
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    skip = (page - 1) * limit
    status_filter = request.args.get('status')
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    docs = list(db.documents.find(
        query,
        sort=[("created_at", -1)]
    ).skip(skip).limit(limit))
    
    total = db.documents.count_documents(query)
    
    # Enrich with usernames
    result = []
    for doc in docs:
        d = document_to_dict(doc)
        user = db.users.find_one({"_id": ObjectId(doc["user_id"])}, {"username": 1, "email": 1})
        d["uploaded_by"] = user.get("username", "Unknown") if user else "Unknown"
        d["user_email"] = user.get("email", "") if user else ""
        result.append(d)
    
    return jsonify({
        "documents": result,
        "total": total,
        "page": page
    })

@admin_bp.route('/documents/<document_id>/toggle', methods=['PUT'])
@require_admin
def toggle_document(document_id):
    db = current_app.db
    
    try:
        doc = db.documents.find_one({"_id": ObjectId(document_id)})
    except:
        return jsonify({"error": "Invalid document ID"}), 400
    
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    
    new_active = not doc.get("is_active", True)
    new_status = "ready" if new_active else "disabled"
    
    db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {
            "is_active": new_active,
            "status": new_status,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return jsonify({
        "message": f"Document {'enabled' if new_active else 'disabled'} successfully",
        "is_active": new_active
    })

@admin_bp.route('/queries', methods=['GET'])
@require_admin
def list_queries():
    db = current_app.db
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 30))
    skip = (page - 1) * limit
    
    messages = list(db.messages.find(
        {},
        sort=[("created_at", -1)]
    ).skip(skip).limit(limit))
    
    total = db.messages.count_documents({})
    
    result = []
    for msg in messages:
        m = {
            "id": str(msg["_id"]),
            "role": msg["role"],
            "content": msg["content"][:300],
            "tokens_used": msg.get("tokens_used", 0),
            "session_id": msg.get("session_id"),
            "user_id": msg.get("user_id"),
            "created_at": msg["created_at"].isoformat() if msg.get("created_at") else None
        }
        user = db.users.find_one({"_id": ObjectId(msg["user_id"])}, {"username": 1}) if msg.get("user_id") else None
        m["username"] = user.get("username", "Unknown") if user else "Unknown"
        result.append(m)
    
    return jsonify({
        "messages": result,
        "total": total,
        "page": page
    })