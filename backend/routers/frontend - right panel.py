from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Message
from database.config import get_db
from backend.services.auth import decode_access_token

router = APIRouter(prefix="/frontend - right panel", tags=["Frontend - Right Panel"])

# Pydantic Schemas
class MessageBase(BaseModel):
    session_id: UUID
    role: str
    content: str
    metadata: Optional[dict] = Field(default_factory=dict)

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    role: Optional[str]
    content: Optional[str]
    metadata: Optional[dict]

class MessageResponse(MessageBase):
    id: UUID
    created_at: str

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return token

# Routes
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    new_message = Message(**message_data.dict())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return MessageResponse(
        id=new_message.id,
        session_id=new_message.session_id,
        role=new_message.role,
        content=new_message.content,
        metadata=new_message.metadata,
        created_at=new_message.created_at.isoformat(),
    )

@router.get("/", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def list_messages(session_id: UUID, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.session_id == session_id).all()
    return [
        MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at.isoformat(),
        )
        for message in messages
    ]

@router.get("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        metadata=message.metadata,
        created_at=message.created_at.isoformat(),
    )

@router.put("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def update_message(message_id: UUID, message_data: MessageUpdate, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    for key, value in message_data.dict(exclude_unset=True).items():
        setattr(message, key, value)
    db.commit()
    db.refresh(message)
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        metadata=message.metadata,
        created_at=message.created_at.isoformat(),
    )

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    db.delete(message)
    db.commit()
    return None