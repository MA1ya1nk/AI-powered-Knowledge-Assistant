# utils/rag.py
import logging
from groq import Groq
from config import config
from utils.embeddings import generate_embedding, find_similar_chunks

logger = logging.getLogger(__name__)

_client = None

def get_groq_client():
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client

def retrieve_relevant_chunks(db, query, user_id=None, top_k=5):
    query_embedding = generate_embedding(query)

    doc_filter = {"is_active": True, "status": "ready"}
    if user_id:
        doc_filter["$or"] = [
            {"user_id": user_id},
            {"user_id": str(user_id)}
        ]

    active_docs = list(db.documents.find(doc_filter, {"_id": 1}))
    active_doc_ids = [str(doc["_id"]) for doc in active_docs]

    logger.info(f"Found {len(active_doc_ids)} active docs for user {user_id}")

    if not active_doc_ids:
        return []

    chunk_filter = {
        "document_id": {"$in": active_doc_ids},
        "embedding": {"$exists": True, "$ne": None}
    }

    chunks = list(db.document_chunks.find(chunk_filter))
    logger.info(f"Found {len(chunks)} chunks to search through")

    if not chunks:
        return []

    similar = find_similar_chunks(query_embedding, chunks, top_k=top_k)

    results = []
    for score, chunk in similar:
        from bson import ObjectId
        doc = db.documents.find_one({"_id": ObjectId(chunk["document_id"])})
        results.append({
            "chunk_id": str(chunk["_id"]),
            "document_id": chunk["document_id"],
            "document_name": doc["original_name"] if doc else "Unknown",
            "content": chunk["content"],
            "chunk_index": chunk.get("chunk_index", 0),
            "similarity_score": round(score, 4)
        })
    return results

def generate_answer(question, context_chunks, chat_history=None):
    if not context_chunks:
        return {
            "answer": "I couldn't find any relevant documents. Please upload documents first.",
            "sources": [],
            "tokens_used": 0
        }

    context_text = "\n\n---\n\n".join(
        f"[Source {i}: {c['document_name']}]\n{c['content']}"
        for i, c in enumerate(context_chunks, 1)
    )

    system_prompt = """You are an intelligent Knowledge Assistant. Answer questions based ONLY on the provided document context.
Rules:
- Answer ONLY based on the provided context
- If the answer is not in the context, say "I couldn't find relevant information in the uploaded documents."
- Always mention which document your answer comes from
- Be concise, accurate, and helpful"""

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        for msg in chat_history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": f"Context:\n\n{context_text}\n\n---\n\nQuestion: {question}"
    })

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            temperature=0.3
        )
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

    except Exception as e:
        logger.error(f"Groq error: {e}")
        answer = f"Error generating answer: {str(e)}"
        tokens_used = 0

    sources = [
        {
            "document_name": c["document_name"],
            "document_id": c["document_id"],
            "similarity_score": c["similarity_score"],
            "excerpt": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"]
        }
        for c in context_chunks
    ]

    return {"answer": answer, "sources": sources, "tokens_used": tokens_used}

def generate_session_title(question):
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Generate a very short title (max 5 words) for a chat session. Return ONLY the title, nothing else."},
                {"role": "user", "content": question}
            ],
            max_tokens=15,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except:
        return question[:50] + "..." if len(question) > 50 else question