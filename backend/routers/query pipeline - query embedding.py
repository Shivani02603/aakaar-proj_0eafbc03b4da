from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import decode_access_token
from ai.embeddings import get_embedding

router = APIRouter(
    prefix="/query-pipeline-query-embedding",
    tags=["Query Pipeline - Query Embedding"]
)

# Pydantic Schemas
class QueryEmbeddingRequest(BaseModel):
    query: str = Field(..., description="The query text to embed")
    session_id: UUID = Field(..., description="Session ID associated with the query")
    user_id: UUID = Field(..., description="User ID associated with the query")

class QueryEmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="Generated embedding for the query")
    session_id: UUID = Field(..., description="Session ID associated with the query")
    user_id: UUID = Field(..., description="User ID associated with the query")

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return token

# Endpoint to embed a query
@router.post("/embed", response_model=QueryEmbeddingResponse)
async def embed_query(request: QueryEmbeddingRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        # Validate session and user
        session_id = request.session_id
        user_id = request.user_id

        # Generate embedding
        embedding = get_embedding([request.query])
        if not embedding or len(embedding) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embedding"
            )

        return QueryEmbeddingResponse(
            embedding=embedding[0],
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# CRUD Endpoints for DocumentChunk (standard CRUD operations)
class DocumentChunkCreate(BaseModel):
    file_id: UUID = Field(..., description="File ID associated with the chunk")
    session_id: UUID = Field(..., description="Session ID associated with the chunk")
    content: str = Field(..., description="Content of the chunk")
    embedding: List[float] = Field(..., description="Embedding vector for the chunk")
    metadata: dict = Field(..., description="Metadata for the chunk")
    chunk_index: int = Field(..., description="Index of the chunk")
    token_count: int = Field(..., description="Token count for the chunk")

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Updated content of the chunk")
    embedding: Optional[List[float]] = Field(None, description="Updated embedding vector for the chunk")
    metadata: Optional[dict] = Field(None, description="Updated metadata for the chunk")
    chunk_index: Optional[int] = Field(None, description="Updated index of the chunk")
    token_count: Optional[int] = Field(None, description="Updated token count for the chunk")

class DocumentChunkResponse(BaseModel):
    id: UUID = Field(..., description="ID of the chunk")
    file_id: UUID = Field(..., description="File ID associated with the chunk")
    session_id: UUID = Field(..., description="Session ID associated with the chunk")
    content: str = Field(..., description="Content of the chunk")
    embedding: List[float] = Field(..., description="Embedding vector for the chunk")
    metadata: dict = Field(..., description="Metadata for the chunk")
    chunk_index: int = Field(..., description="Index of the chunk")
    token_count: int = Field(..., description="Token count for the chunk")
    created_at: str = Field(..., description="Timestamp when the chunk was created")

@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_chunks(db: Session = Depends(get_db)):
    try:
        chunks = db.query(DocumentChunk).all()
        return chunks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found"
            )
        return chunk
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/chunks", response_model=DocumentChunkResponse)
async def create_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    try:
        new_chunk = DocumentChunk(**chunk.dict())
        db.add(new_chunk)
        db.commit()
        db.refresh(new_chunk)
        return new_chunk
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_chunk(chunk_id: UUID, chunk_update: DocumentChunkUpdate, db: Session = Depends(get_db)):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found"
            )
        for key, value in chunk_update.dict(exclude_unset=True).items():
            setattr(chunk, key, value)
        db.commit()
        db.refresh(chunk)
        return chunk
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found"
            )
        db.delete(chunk)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )