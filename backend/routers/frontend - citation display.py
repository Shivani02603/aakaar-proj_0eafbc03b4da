from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Citation
from database.config import get_db
from backend.services.auth import decode_access_token

router = APIRouter(
    prefix="/frontend - citation display",
    tags=["Frontend - Citation Display"]
)

# Pydantic Schemas
class CitationBase(BaseModel):
    source: str = Field(..., description="Source of the citation")
    content: str = Field(..., description="Content of the citation")
    metadata: Optional[dict] = Field(None, description="Additional metadata for the citation")

class CitationCreate(CitationBase):
    pass

class CitationUpdate(CitationBase):
    pass

class CitationResponse(CitationBase):
    id: UUID = Field(..., description="Unique identifier for the citation")

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return token

# CRUD Endpoints

@router.get("/", response_model=List[CitationResponse])
async def list_citations(db: Session = Depends(get_db)):
    citations = db.query(Citation).all()
    return citations

@router.get("/{citation_id}", response_model=CitationResponse)
async def get_citation(citation_id: UUID, db: Session = Depends(get_db)):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    return citation

@router.post("/", response_model=CitationResponse)
async def create_citation(citation: CitationCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_citation = Citation(**citation.dict())
    db.add(new_citation)
    db.commit()
    db.refresh(new_citation)
    return new_citation

@router.put("/{citation_id}", response_model=CitationResponse)
async def update_citation(citation_id: UUID, citation_update: CitationUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    for key, value in citation_update.dict().items():
        setattr(citation, key, value)
    db.commit()
    db.refresh(citation)
    return citation

@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_citation(citation_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    db.delete(citation)
    db.commit()