import os
import pandas as pd
from tiktoken import Encoding
from .embeddings import get_embedding
from sqlalchemy import create_engine
from pgvector.sqlalchemy import Vector

# Chunking function
def chunk(document: str, strategy: str = "token", size: int = 1000, overlap: int = 200) -> list:
    if strategy != "token":
        raise ValueError("Only 'token' strategy is supported.")
    encoding = Encoding.for_model("text-embedding-3-small")
    tokens = encoding.encode(document)
    chunks = []
    for i in range(0, len(tokens), size - overlap):
        chunk_tokens = tokens[i:i + size]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

# Ingest Excel function
def ingest_excel(file_path: str, session_id: str, user_id: str):
    # Read OpenAI API key lazily
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    # Read PostgreSQL connection string lazily
    postgres_conn_str = os.getenv("POSTGRES_CONN_STR")
    if not postgres_conn_str:
        raise ValueError("POSTGRES_CONN_STR environment variable not set.")
    
    # Initialize database connection
    engine = create_engine(postgres_conn_str)
    
    # Read Excel file
    excel_data = pd.ExcelFile(file_path)
    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name)
        document = sheet_data.to_string(index=False)
        
        # Chunk the document
        chunks = chunk(document)
        
        # Embed each chunk
        embeddings = [get_embedding(chunk, model="text-embedding-3-small") for chunk in chunks]
        
        # Upsert into vector store
        with engine.connect() as conn:
            for chunk, embedding in zip(chunks, embeddings):
                conn.execute(
                    """
                    INSERT INTO vector_store (session_id, user_id, chunk, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id, user_id, chunk)
                    DO UPDATE SET embedding = EXCLUDED.embedding
                    """,
                    (session_id, user_id, chunk, embedding)
                )