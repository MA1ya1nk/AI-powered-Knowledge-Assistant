# utils/embeddings.py
import numpy as np
from openai import OpenAI
from config import config
import logging

logger = logging.getLogger(__name__)

_client = None

def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client

def generate_embedding(text):
    """Generate embedding vector for a text string."""
    try:
        client = get_openai_client()
        response = client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=text[:8000]  # truncate to avoid token limits
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise Exception(f"Failed to generate embedding: {str(e)}")

def generate_embeddings_batch(texts, batch_size=20):
    """Generate embeddings for multiple texts in batches."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            client = get_openai_client()
            response = client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=[t[:8000] for t in batch]
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Generated embeddings for batch {i//batch_size + 1}")
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise Exception(f"Batch embedding failed: {str(e)}")
    return all_embeddings

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return 0.0
    return float(dot / norm)

def find_similar_chunks(query_embedding, chunks_with_embeddings, top_k=5):
    """Find most similar chunks to query embedding."""
    scored = []
    for chunk in chunks_with_embeddings:
        if chunk.get("embedding"):
            score = cosine_similarity(query_embedding, chunk["embedding"])
            scored.append((score, chunk))
    
    # Sort by similarity descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]