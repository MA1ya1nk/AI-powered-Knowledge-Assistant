import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/knowledge_assistant")
    JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    
    # Chunking config
    CHUNK_SIZE = 500          # tokens per chunk
    CHUNK_OVERLAP = 50        # token overlap between chunks
    TOP_K_CHUNKS = 5          # how many chunks to retrieve
    
    # LLM config
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHAT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 1000

config = Config()