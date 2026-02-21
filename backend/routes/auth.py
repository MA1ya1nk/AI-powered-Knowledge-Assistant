# routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from datetime import timedelta
from models.user import create_user, user_to_dict
from bson import ObjectId
import logging
import re

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def validate_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
    
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    db = current_app.db
    
    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409
    
    if db.users.find_one({"username": username}):
        return jsonify({"error": "Username already taken"}), 409
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    role = "admin" if db.users.count_documents({}) == 0 else "user"
    
    user_doc = create_user(username, email, hashed.decode('utf-8'), role)
    result = db.users.insert_one(user_doc)
    
    user_doc['_id'] = result.inserted_id
    token = create_access_token(
        identity=str(result.inserted_id),
        expires_delta=timedelta(days=7)
    )
    
    logger.info(f"New user registered: {email} (role: {role})")
    
    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": user_to_dict(user_doc)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    db = current_app.db
    user = db.users.find_one({"email": email})
    
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    
    if not user.get('is_active', True):
        return jsonify({"error": "Account is disabled"}), 403
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401
    
    token = create_access_token(
        identity=str(user['_id']),
        expires_delta=timedelta(days=7)
    )
    
    logger.info(f"User logged in: {email}")
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user_to_dict(user)
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    db = current_app.db
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"user": user_to_dict(user)})

@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({"error": "Old and new passwords required"}), 400
    
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    
    db = current_app.db
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed.decode('utf-8')}}
    )
    
    return jsonify({"message": "Password updated successfully"})