from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile
from database.config import get_db
from backend.services.auth import decode_access_token, get_current_user
from backend.routers.file_upload import save_file_to_disk

router = APIRouter(prefix="/api/sessions/{session_id}/files", tags=["File Upload"])

# Pydantic Schemas
class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    status: str

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileUpdate(BaseModel):
    status: Optional[str] = None

class UploadedFileResponse(UploadedFileBase):
    id: UUID

# Helper function to check file type
def validate_file_type(file: UploadFile):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed.")

# Routes
@router.post("/", response_model=UploadedFileResponse, operation_id="uploadFile")
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    validate_file_type(file)

    # Save file to disk
    destination = f"uploads/{file.filename}"
    save_file_to_disk(file, destination)

    # Create UploadedFile record in the database
    uploaded_file = UploadedFile(
        session_id=session_id,
        filename=destination,
        original_filename=file.filename,
        file_size=len(file.file.read()),
        content_type=file.content_type,
        status="uploaded",
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return uploaded_file

@router.get("/", response_model=List[UploadedFileResponse], operation_id="getSessionFiles")
async def list_files(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    files = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).all()
    return files

@router.get("/{file_id}", response_model=UploadedFileResponse)
async def get_file(
    session_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == session_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.put("/{file_id}", response_model=UploadedFileResponse)
async def update_file(
    session_id: UUID,
    file_id: UUID,
    update_data: UploadedFileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == session_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(file, key, value)

    db.commit()
    db.refresh(file)
    return file

@router.delete("/{file_id}", response_model=dict)
async def delete_file(
    session_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == session_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    db.delete(file)
    db.commit()
    return {"detail": "File deleted successfully"}