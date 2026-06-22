from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session, UploadedFile
from database.config import get_db
from backend.services.auth import decode_access_token

router = APIRouter(prefix="/backend", tags=["Backend"])

# Pydantic Schemas
class UserBase(BaseModel):
    session_id: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: str

class SessionBase(BaseModel):
    user_id: UUID
    name: str

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: UUID
    created_at: str
    updated_at: str

class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    status: str

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    created_at: str

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return token

# User Endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for key, value in user_data.dict().items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return None

# Session Endpoints
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    session = Session(**session_data.dict())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(Session).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, session_data: SessionCreate, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    for key, value in session_data.dict().items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return None

# UploadedFile Endpoints
@router.post("/files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def create_file(file_data: UploadedFileCreate, db: Session = Depends(get_db)):
    file = UploadedFile(**file_data.dict())
    db.add(file)
    db.commit()
    db.refresh(file)
    return file

@router.get("/files", response_model=List[UploadedFileResponse])
def list_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return files

@router.get("/files/{file_id}", response_model=UploadedFileResponse)
def get_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.put("/files/{file_id}", response_model=UploadedFileResponse)
def update_file(file_id: UUID, file_data: UploadedFileCreate, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    for key, value in file_data.dict().items():
        setattr(file, key, value)
    db.commit()
    db.refresh(file)
    return file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()
    return None