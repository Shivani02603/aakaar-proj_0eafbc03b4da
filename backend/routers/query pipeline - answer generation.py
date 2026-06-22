from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Message
from database.config import get_db
from backend.services.auth import decode_access_token
from ai.rag import retrieve_context, answer_question

router = APIRouter(
    prefix="/query-pipeline-answer-generation",
    tags=["Query Pipeline - Answer Generation"]
)

# Pydantic Schemas
class AnswerRequest(BaseModel):
    query: str = Field(..., description="The question or query to be answered.")
    session_id: UUID = Field(..., description="The session ID associated with the query.")
    user_id: UUID = Field(..., description="The user ID making the query.")

class AnswerResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the query.")
    context: List[str] = Field(..., description="The context used to generate the answer.")

class MessageBase(BaseModel):
    session_id: UUID = Field(..., description="The session ID associated with the message.")
    role: str = Field(..., description="The role of the message sender (e.g., 'user', 'system').")
    content: str = Field(..., description="The content of the message.")
    metadata: Optional[dict] = Field(None, description="Additional metadata for the message.")

class MessageResponse(MessageBase):
    id: UUID = Field(..., description="The unique identifier of the message.")
    created_at: str = Field(..., description="Timestamp when the message was created.")

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    user_data = decode_access_token(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_data

# Routes
@router.post("/generate-answer", response_model=AnswerResponse)
async def generate_answer(request: AnswerRequest, db: Session = Depends(get_db)):
    """
    Generate an answer to a query using retrieved context and Google Generative AI SDK.
    """
    try:
        # Retrieve context for the query
        context = retrieve_context(query=request.query, top_k=5, session_id=request.session_id, user_id=request.user_id)
        
        # Generate answer using Google Generative AI SDK
        answer = answer_question(query=request.query, session_id=request.session_id, user_id=request.user_id)
        
        return AnswerResponse(answer=answer, context=context)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/messages", response_model=List[MessageResponse])
async def list_messages(session_id: UUID, db: Session = Depends(get_db)):
    """
    List all messages for a given session.
    """
    try:
        messages = db.query(Message).filter(Message.session_id == session_id).all()
        return [MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at.isoformat()
        ) for message in messages]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(message_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific message by ID.
    """
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        return MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/messages", response_model=MessageResponse)
async def create_message(message_data: MessageBase, db: Session = Depends(get_db)):
    """
    Create a new message.
    """
    try:
        new_message = Message(
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content,
            metadata=message_data.metadata
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return MessageResponse(
            id=new_message.id,
            session_id=new_message.session_id,
            role=new_message.role,
            content=new_message.content,
            metadata=new_message.metadata,
            created_at=new_message.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/messages/{message_id}", response_model=MessageResponse)
async def update_message(message_id: UUID, message_data: MessageBase, db: Session = Depends(get_db)):
    """
    Update an existing message.
    """
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        
        message.role = message_data.role
        message.content = message_data.content
        message.metadata = message_data.metadata
        db.commit()
        db.refresh(message)
        return MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a message by ID.
    """
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        
        db.delete(message)
        db.commit()
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))