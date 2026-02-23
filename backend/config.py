import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/knowledge_assistant")
    JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

    # Chunking
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K_CHUNKS = 5

    # Models
    GROQ_MODEL = "llama-3.1-8b-instant"   # free & fast on Groq
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # free local embeddings
    MAX_TOKENS = 1024

config = Config()