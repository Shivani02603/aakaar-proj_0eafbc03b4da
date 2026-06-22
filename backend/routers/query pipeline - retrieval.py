from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import decode_access_token
from ai.embeddings import get_embedding
from ai.vector_store import VectorStore

router = APIRouter(
    prefix="/query-pipeline-retrieval",
    tags=["Query Pipeline - Retrieval"]
)

# Pydantic schemas
class ChunkBase(BaseModel):
    content: str
    embedding: List[float]
    metadata: dict
    chunk_index: int
    token_count: int

class ChunkCreate(ChunkBase):
    file_id: UUID
    session_id: UUID

class ChunkResponse(ChunkBase):
    id: UUID

class ChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None
    chunk_index: Optional[int] = None
    token_count: Optional[int] = None

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token

# CRUD endpoints
@router.get("/", response_model=List[ChunkResponse])
async def list_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return [ChunkResponse(**chunk.__dict__) for chunk in chunks]

@router.get("/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return ChunkResponse(**chunk.__dict__)

@router.post("/", response_model=ChunkResponse)
async def create_chunk(chunk: ChunkCreate, db: Session = Depends(get_db)):
    new_chunk = DocumentChunk(**chunk.dict())
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return ChunkResponse(**new_chunk.__dict__)

@router.put("/{chunk_id}", response_model=ChunkResponse)
async def update_chunk(chunk_id: UUID, chunk: ChunkUpdate, db: Session = Depends(get_db)):
    existing_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not existing_chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    for key, value in chunk.dict(exclude_unset=True).items():
        setattr(existing_chunk, key, value)
    db.commit()
    db.refresh(existing_chunk)
    return ChunkResponse(**existing_chunk.__dict__)

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    db.delete(chunk)
    db.commit()
    return None

# Functional requirement: Retrieve top-5 chunks by cosine similarity
@router.post("/retrieve", response_model=List[ChunkResponse])
async def retrieve_chunks(query: str, session_id: UUID, db: Session = Depends(get_db)):
    embedding = get_embedding([query])[0]
    vector_store = VectorStore()
    top_chunks = vector_store.search(embedding, top_k=5, session_id=session_id)
    if not top_chunks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No relevant chunks found")
    return [ChunkResponse(**chunk.__dict__) for chunk in top_chunks]