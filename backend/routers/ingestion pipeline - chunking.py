from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import decode_access_token
from backend.routers.ingestion_pipeline_parsing import split_into_chunks

router = APIRouter(
    prefix="/ingestion pipeline - chunking",
    tags=["Ingestion Pipeline - Chunking"]
)

# Pydantic Schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    session_id: UUID
    content: str
    metadata: Optional[dict] = None
    chunk_index: int
    token_count: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

# Routes
@router.post("/", response_model=DocumentChunkResponse)
async def create_chunk(chunk_data: DocumentChunkCreate, db: Session = Depends(get_db)):
    new_chunk = DocumentChunk(**chunk_data.dict())
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk

@router.get("/", response_model=List[DocumentChunkResponse])
async def list_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return chunks

@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk

@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
async def update_chunk(chunk_id: UUID, chunk_update: DocumentChunkUpdate, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    for key, value in chunk_update.dict(exclude_unset=True).items():
        setattr(chunk, key, value)
    
    db.commit()
    db.refresh(chunk)
    return chunk

@router.delete("/{chunk_id}")
async def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    db.delete(chunk)
    db.commit()
    return {"detail": "Chunk deleted successfully"}

@router.post("/split", response_model=List[DocumentChunkResponse])
async def split_content_into_chunks(
    file_id: UUID,
    session_id: UUID,
    content: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    db: Session = Depends(get_db)
):
    chunks = split_into_chunks(content, chunk_size, overlap)
    chunk_objects = []
    for index, chunk_content in enumerate(chunks):
        chunk = DocumentChunk(
            file_id=file_id,
            session_id=session_id,
            content=chunk_content,
            chunk_index=index,
            token_count=len(chunk_content.split()),  # Assuming token count is word count
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        chunk_objects.append(chunk)
    return chunk_objects