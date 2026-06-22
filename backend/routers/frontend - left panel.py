from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Session, UploadedFile
from database.config import get_db
from backend.services.auth import decode_access_token
from datetime import datetime

router = APIRouter(
    prefix="/frontend - left panel",
    tags=["Frontend - Left Panel"]
)

# Pydantic Schemas
class SessionBase(BaseModel):
    name: str = Field(..., example="My Session")

class SessionCreate(SessionBase):
    user_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UploadedFileBase(BaseModel):
    filename: str = Field(..., example="uploaded_file.txt")
    original_filename: str = Field(..., example="original_file.txt")
    file_size: int = Field(..., example=1024)
    content_type: str = Field(..., example="text/plain")
    status: str = Field(..., example="uploaded")

class UploadedFileCreate(UploadedFileBase):
    session_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token

# Routes
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    new_session = Session(**session_data.dict(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions", response_model=List[SessionResponse], status_code=status.HTTP_200_OK)
async def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(Session).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def update_session(session_id: UUID, session_data: SessionBase, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    for key, value in session_data.dict().items():
        setattr(session, key, value)
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return None

@router.post("/sessions/{session_id}/files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    uploaded_file = UploadedFile(
        session_id=session_id,
        filename=file.filename,
        original_filename=file.filename,
        file_size=len(file.file.read()),
        content_type=file.content_type,
        status="uploaded",
        created_at=datetime.utcnow()
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    return uploaded_file

@router.get("/sessions/{session_id}/files", response_model=List[UploadedFileResponse], status_code=status.HTTP_200_OK)
async def list_files(session_id: UUID, db: Session = Depends(get_db)):
    files = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).all()
    return files

@router.get("/sessions/{session_id}/files/{file_id}", response_model=UploadedFileResponse, status_code=status.HTTP_200_OK)
async def get_file(session_id: UUID, file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.session_id == session_id, UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.delete("/sessions/{session_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(session_id: UUID, file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.session_id == session_id, UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()
    return None