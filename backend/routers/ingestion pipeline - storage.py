from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import decode_access_token
from datetime import datetime

router = APIRouter(
    prefix="/ingestion-pipeline-storage",
    tags=["Ingestion Pipeline - Storage"]
)

# Pydantic Schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    session_id: UUID
    content: str
    embedding: List[float]
    metadata: dict
    chunk_index: int
    token_count: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[dict] = None
    chunk_index: Optional[int] = None
    token_count: Optional[int] = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return token

# CRUD Endpoints
@router.post("/", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(
    chunk: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    new_chunk = DocumentChunk(**chunk.dict())
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk

@router.get("/", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunks = db.query(DocumentChunk).offset(skip).limit(limit).all()
    return chunks

@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found"
        )
    return chunk

@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
async def update_document_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found"
        )
    for key, value in chunk_update.dict(exclude_unset=True).items():
        setattr(chunk, key, value)
    db.commit()
    db.refresh(chunk)
    return chunk

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found"
        )
    db.delete(chunk)
    db.commit()