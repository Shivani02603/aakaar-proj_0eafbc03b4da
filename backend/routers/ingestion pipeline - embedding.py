from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from ai.embeddings import get_embedding
from backend.services.auth import decode_access_token

router = APIRouter(
    prefix="/ingestion-pipeline-embedding",
    tags=["Ingestion Pipeline - Embedding"]
)

# Pydantic Schemas
class EmbeddingRequest(BaseModel):
    chunk_id: UUID
    content: str

class EmbeddingResponse(BaseModel):
    chunk_id: UUID
    embedding: List[float]

class DocumentChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    session_id: UUID
    content: str
    embedding: List[float]
    metadata: dict
    chunk_index: int
    token_count: int
    created_at: str

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

# Embed a single chunk
@router.post("/embed", response_model=EmbeddingResponse)
async def embed_chunk(request: EmbeddingRequest, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == request.chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    embedding = get_embedding([request.content])
    if not embedding or len(embedding) == 0:
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

    chunk.embedding = embedding[0]
    db.commit()

    return EmbeddingResponse(chunk_id=chunk.id, embedding=chunk.embedding)

# List all chunks with embeddings
@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return [
        DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            session_id=chunk.session_id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            created_at=chunk.created_at.isoformat()
        )
        for chunk in chunks
    ]

# Get a specific chunk by ID
@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    return DocumentChunkResponse(
        id=chunk.id,
        file_id=chunk.file_id,
        session_id=chunk.session_id,
        content=chunk.content,
        embedding=chunk.embedding,
        metadata=chunk.metadata,
        chunk_index=chunk.chunk_index,
        token_count=chunk.token_count,
        created_at=chunk.created_at.isoformat()
    )

# Update a chunk's embedding
@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_chunk(chunk_id: UUID, request: EmbeddingRequest, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    embedding = get_embedding([request.content])
    if not embedding or len(embedding) == 0:
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

    chunk.content = request.content
    chunk.embedding = embedding[0]
    db.commit()

    return DocumentChunkResponse(
        id=chunk.id,
        file_id=chunk.file_id,
        session_id=chunk.session_id,
        content=chunk.content,
        embedding=chunk.embedding,
        metadata=chunk.metadata,
        chunk_index=chunk.chunk_index,
        token_count=chunk.token_count,
        created_at=chunk.created_at.isoformat()
    )

# Delete a chunk
@router.delete("/chunks/{chunk_id}")
async def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    db.delete(chunk)
    db.commit()
    return {"detail": "Chunk deleted successfully"}