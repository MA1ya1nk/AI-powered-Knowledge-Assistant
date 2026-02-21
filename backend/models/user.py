# models/user.py
from datetime import datetime, timezone
from bson import ObjectId

def create_user(username, email, hashed_password, role="user"):
    return {
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": role,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
        "total_queries": 0,
        "total_tokens_used": 0
    }

def user_to_dict(user):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "is_active": user.get("is_active", True),
        "total_queries": user.get("total_queries", 0),
        "total_tokens_used": user.get("total_tokens_used", 0)
    }