# models/chat.py
from datetime import datetime, timezone

def create_session(user_id, title="New Conversation"):
    return {
        "user_id": user_id,
        "title": title,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "message_count": 0
    }

def create_message(session_id, user_id, role, content, sources=None, tokens_used=0):
    return {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,  # user | assistant
        "content": content,
        "sources": sources or [],
        "tokens_used": tokens_used,
        "created_at": datetime.now(timezone.utc)
    }

def message_to_dict(msg):
    return {
        "id": str(msg["_id"]),
        "session_id": str(msg["session_id"]),
        "role": msg["role"],
        "content": msg["content"],
        "sources": msg.get("sources", []),
        "tokens_used": msg.get("tokens_used", 0),
        "created_at": msg["created_at"].isoformat() if msg.get("created_at") else None
    }

def session_to_dict(session):
    return {
        "id": str(session["_id"]),
        "user_id": str(session["user_id"]),
        "title": session.get("title", "Conversation"),
        "message_count": session.get("message_count", 0),
        "created_at": session["created_at"].isoformat() if session.get("created_at") else None,
        "updated_at": session["updated_at"].isoformat() if session.get("updated_at") else None
    }