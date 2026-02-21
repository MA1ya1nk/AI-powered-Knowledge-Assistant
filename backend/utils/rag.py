# utils/rag.py
from openai import OpenAI
from config import config
from utils.embeddings import generate_embedding, find_similar_chunks
import logging

logger = logging.getLogger(__name__)

def get_openai_client():
    return OpenAI(api_key=config.OPENAI_API_KEY)

def retrieve_relevant_chunks(db, query, user_id=None, top_k=None):
    """Retrieve relevant document chunks for a query using semantic search."""
    top_k = top_k or config.TOP_K_CHUNKS
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Fetch all active chunks for user
    filter_query = {"embedding": {"$exists": True, "$ne": None}}
    if user_id:
        filter_query["user_id"] = user_id
    
    # Also filter only chunks from active documents
    active_doc_ids = [
        str(doc["_id"]) 
        for doc in db.documents.find(
            {"is_active": True, "status": "ready", **({"user_id": user_id} if user_id else {})},
            {"_id": 1}
        )
    ]
    
    if not active_doc_ids:
        return []
    
    filter_query["document_id"] = {"$in": active_doc_ids}
    
    chunks = list(db.document_chunks.find(filter_query))
    
    if not chunks:
        return []
    
    # Find similar chunks
    similar = find_similar_chunks(query_embedding, chunks, top_k=top_k)
    
    # Enrich with document info
    results = []
    for score, chunk in similar:
        doc = db.documents.find_one({"_id": __import__('bson').ObjectId(chunk["document_id"])})
        results.append({
            "chunk_id": str(chunk["_id"]),
            "document_id": chunk["document_id"],
            "document_name": doc["original_name"] if doc else "Unknown",
            "content": chunk["content"],
            "chunk_index": chunk.get("chunk_index", 0),
            "similarity_score": round(score, 4)
        })
    
    return results

def build_prompt(question, context_chunks, chat_history=None):
    """Build the RAG prompt with context."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['document_name']}]\n{chunk['content']}"
        )
    
    context_text = "\n\n---\n\n".join(context_parts)
    
    system_prompt = """You are an intelligent Knowledge Assistant. You answer questions based on the provided document context.

Rules:
- Answer ONLY based on the provided context
- If the answer is not in the context, say "I couldn't find relevant information in the uploaded documents."
- Always cite which document(s) your answer comes from
- Be concise, accurate, and helpful
- Format your response clearly with proper structure when needed"""

    user_message = f"""Context from documents:

{context_text}

---

Question: {question}

Please answer based on the context above and cite your sources."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add chat history for context
    if chat_history:
        for msg in chat_history[-6:]:  # last 3 exchanges
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_message})
    return messages

def generate_answer(question, context_chunks, chat_history=None):
    """Generate AI answer using retrieved context."""
    if not context_chunks:
        return {
            "answer": "I couldn't find any relevant documents to answer your question. Please upload documents first.",
            "sources": [],
            "tokens_used": 0
        }
    
    client = get_openai_client()
    messages = build_prompt(question, context_chunks, chat_history)
    
    try:
        response = client.chat.completions.create(
            model=config.CHAT_MODEL,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            temperature=0.3  # lower temp for factual answers
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        # Build source references
        sources = [
            {
                "document_name": chunk["document_name"],
                "document_id": chunk["document_id"],
                "similarity_score": chunk["similarity_score"],
                "excerpt": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
            }
            for chunk in context_chunks
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "tokens_used": tokens_used
        }
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise Exception(f"Answer generation failed: {str(e)}")

def generate_session_title(question):
    """Generate a short title for a chat session."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate a very short title (max 6 words) for a chat session based on the user's first question. Return only the title, no quotes."},
                {"role": "user", "content": question}
            ],
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except:
        return question[:50] + "..." if len(question) > 50 else question