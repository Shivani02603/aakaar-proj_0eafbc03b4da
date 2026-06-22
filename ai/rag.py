import os
from .embeddings import get_embedding
from sqlalchemy import create_engine
from pgvector.sqlalchemy import Vector
import requests

# Retrieve context function
def retrieve_context(query: str, top_k: int, session_id: str, user_id: str) -> list:
    # Read OpenAI API key lazily
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    # Read PostgreSQL connection string lazily
    postgres_conn_str = os.getenv("POSTGRES_CONN_STR")
    if not postgres_conn_str:
        raise ValueError("POSTGRES_CONN_STR environment variable not set.")
    
    # Embed the query
    query_embedding = get_embedding(query, model="text-embedding-3-small")
    
    # Initialize database connection
    engine = create_engine(postgres_conn_str)
    
    # Retrieve top-k chunks by cosine similarity
    with engine.connect() as conn:
        result = conn.execute(
            """
            SELECT chunk
            FROM vector_store
            WHERE session_id = %s AND user_id = %s
            ORDER BY embedding <-> %s
            LIMIT %s
            """,
            (session_id, user_id, query_embedding, top_k)
        )
        return [row[0] for row in result]

# Answer question function
def answer_question(query: str, session_id: str, user_id: str) -> dict:
    # Read Google Generative AI API key lazily
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    
    # Retrieve context
    context_chunks = retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    context = "\n".join(context_chunks)
    
    # Build prompt
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer with citations:"
    
    # Call runtime LLM
    response = requests.post(
        "https://generativeai.googleapis.com/v1/models/gemini-2.0-flash:generateText",
        headers={"Authorization": f"Bearer {google_api_key}"},
        json={"prompt": prompt}
    )
    response_data = response.json()
    
    # Extract answer and sources
    answer = response_data.get("text", "").strip()
    sources = context_chunks
    
    return {"answer": answer, "sources": sources}