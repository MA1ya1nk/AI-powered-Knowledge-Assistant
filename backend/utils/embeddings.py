# utils/embeddings.py
import numpy as np
from openai import OpenAI
from config import config
import logging

logger = logging.getLogger(__name__)

_client = None

import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading embedding model (only on first startup)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model ready!")
    return _model

def generate_embedding(text):
    try:
        model = get_model()
        emb = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        return emb.tolist() if hasattr(emb, 'tolist') else emb
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise Exception(f"Failed to generate embedding: {str(e)}")

def generate_embeddings_batch(texts, batch_size=20):
    try:
        model = get_model()
        embs = model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
        return [e.tolist() if hasattr(e, 'tolist') else e for e in embs]
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        raise Exception(f"Batch embedding failed: {str(e)}")

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return 0.0
    return float(dot / norm)

def find_similar_chunks(query_embedding, chunks_with_embeddings, top_k=5):
    scored = []
    for chunk in chunks_with_embeddings:
        if chunk.get("embedding"):
            score = cosine_similarity(query_embedding, chunk["embedding"])
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]