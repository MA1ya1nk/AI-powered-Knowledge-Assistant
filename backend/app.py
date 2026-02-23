from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
import os
import logging
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Config
    app.config['JWT_SECRET_KEY'] = config.JWT_SECRET
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # CORS
    CORS(app, origins=[
    "http://localhost:3000",
    "https://ai-powered-knowledge-assistant.vercel.app/"  # add after deploying frontend
], supports_credentials=True)

    # JWT
    jwt = JWTManager(app)
    
    # MongoDB
    client = MongoClient(config.MONGO_URI)
    db = client.get_default_database()
    app.db = db
    
    # Create indexes
    try:
        db.users.create_index("email", unique=True)
        db.users.create_index("username", unique=True)
        db.documents.create_index("user_id")
        db.document_chunks.create_index("document_id")
        db.chat_sessions.create_index("user_id")
        db.messages.create_index("session_id")
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")
    
    # Ensure uploads dir
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.documents import documents_bp
    from routes.chat import chat_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "message": "Knowledge Assistant API running"})
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token"}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization token required"}), 401
    
    # Global error handler
    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({"error": "File too large. Max size is 16MB"}), 413
    
    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    return app

# if __name__ == '__main__':
#     app = create_app()
#     logger.info(f"Starting server on port {config.FLASK_PORT}")
#     app.run(
#         debug=(config.FLASK_ENV == 'development'),
#         port=config.FLASK_PORT,
#         host='0.0.0.0'
#     )

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)