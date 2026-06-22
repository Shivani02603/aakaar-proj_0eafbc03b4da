from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Citation
from database.config import get_db
from backend.services.auth import decode_access_token

router = APIRouter(
    prefix="/query-pipeline-citations",
    tags=["Query Pipeline - Citations"]
)

# Pydantic Schemas
class CitationBase(BaseModel):
    filename: str
    row_range: str
    metadata: Optional[dict] = None

class CitationCreate(CitationBase):
    pass

class CitationUpdate(CitationBase):
    pass

class CitationResponse(CitationBase):
    id: UUID

    class Config:
        orm_mode = True

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found"
        )
    return citation

@router.post("/", response_model=CitationResponse)
async def create_citation(citation_data: CitationCreate, db: Session = Depends(get_db)):
    new_citation = Citation(**citation_data.dict())
    db.add(new_citation)
    db.commit()
    db.refresh(new_citation)
    return new_citation

@router.put("/{citation_id}", response_model=CitationResponse)
async def update_citation(citation_id: UUID, citation_update: CitationUpdate, db: Session = Depends(get_db)):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found"
        )
    for key, value in citation_update.dict().items():
        setattr(citation, key, value)
    db.commit()
    db.refresh(citation)
    return citation

@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_citation(citation_id: UUID, db: Session = Depends(get_db)):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found"
        )
    db.delete(citation)
    db.commit()
    return None

# Functional Requirement Endpoint

@router.post("/answer-with-citations", response_model=dict)
async def answer_with_citations(query: str, db: Session = Depends(get_db)):
    # Simulate the process of retrieving answer and citations
    # This is a placeholder for actual implementation logic
    answer = "This is the answer to your query."
    citations = db.query(Citation).all()
    citation_sources = [
        {"filename": citation.filename, "row_range": citation.row_range}
        for citation in citations
    ]
    return {
        "answer": answer,
        "citations": citation_sources
    }