from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile, DocumentChunk
from database.config import get_db
import pandas as pd
import json

router = APIRouter(
    prefix="/ingestion-pipeline-parsing",
    tags=["Ingestion Pipeline - Parsing"]
)

# Pydantic Schemas
class ParseExcelRequest(BaseModel):
    session_id: UUID
    file_id: UUID

class ParsedDataResponse(BaseModel):
    chunk_index: int
    content: str
    metadata: dict
    token_count: int

# Helper function to parse Excel file
def parse_excel(file_content: bytes) -> List[ParsedDataResponse]:
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(file_content)
        parsed_data = []
        for index, row in df.iterrows():
            metadata = row.to_dict()
            content = json.dumps(metadata)  # Convert row data to JSON string
            parsed_data.append(ParsedDataResponse(
                chunk_index=index,
                content=content,
                metadata=metadata,
                token_count=len(content.split())
            ))
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(e)}")

# Endpoints
@router.post("/parse-excel", response_model=List[ParsedDataResponse])
async def parse_uploaded_excel(
    session_id: UUID = Form(...),
    file_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Parse an uploaded Excel file and return parsed data.
    """
    try:
        # Validate session and file existence
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == session_id).first()
        if not uploaded_file:
            raise HTTPException(status_code=404, detail="Uploaded file not found for the given session.")

        # Read file content
        file_content = await file.read()
        parsed_data = parse_excel(file_content)

        # Optionally, save parsed data into the database
        for parsed_chunk in parsed_data:
            document_chunk = DocumentChunk(
                file_id=file_id,
                session_id=session_id,
                content=parsed_chunk.content,
                embedding=None,  # Embedding will be handled separately
                metadata=parsed_chunk.metadata,
                chunk_index=parsed_chunk.chunk_index,
                token_count=parsed_chunk.token_count,
                created_at=pd.Timestamp.now()
            )
            db.add(document_chunk)
        db.commit()

        return parsed_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/chunks/{session_id}", response_model=List[ParsedDataResponse])
async def get_chunks(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve all parsed chunks for a given session.
    """
    try:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.session_id == session_id).all()
        if not chunks:
            raise HTTPException(status_code=404, detail="No chunks found for the given session.")

        return [
            ParsedDataResponse(
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                metadata=chunk.metadata,
                token_count=chunk.token_count
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/chunks/{chunk_id}")
async def delete_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a specific chunk by its ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found.")

        db.delete(chunk)
        db.commit()
        return {"detail": "Chunk deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")