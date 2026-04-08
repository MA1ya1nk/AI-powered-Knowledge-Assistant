# utils/embeddings.py
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading embedding model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model ready!")
    return _model

def generate_embedding(text):
    try:
        model = get_model()
        embedding = model.encode(text[:2000], convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")

def generate_embeddings_batch(texts, batch_size=32):
    try:
        model = get_model()
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = model.encode(
            [t[:2000] for t in texts],
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        logger.info("Embeddings generated!")
        return embeddings.tolist()
    except Exception as e:
        raise Exception(f"Batch embedding failed: {str(e)}")

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(dot / norm) if norm != 0 else 0.0

def find_similar_chunks(query_embedding, chunks_with_embeddings, top_k=5):
    scored = [
        (cosine_similarity(query_embedding, chunk["embedding"]), chunk)
        for chunk in chunks_with_embeddings if chunk.get("embedding")
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]