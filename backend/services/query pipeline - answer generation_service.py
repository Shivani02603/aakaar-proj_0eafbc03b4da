from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import Message
from env import GEMINI_API_KEY
from google.generativeai import GeminiClient

class AnswerGenerationService:
    def __init__(self):
        self.client = GeminiClient(api_key=GEMINI_API_KEY)

    async def create_message(self, message_data: dict, db: AsyncSession) -> Message:
        try:
            new_message = Message(**message_data)
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create message due to integrity error."
            )

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found."
            )
        return message

    async def list_all_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        result = await db.execute(select(Message).where(Message.session_id == session_id))
        messages = result.scalars().all()
        return messages

    async def update_message(self, message_id: UUID, message_data: dict, db: AsyncSession) -> Message:
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found."
            )
        for key, value in message_data.items():
            setattr(message, key, value)
        try:
            await db.commit()
            await db.refresh(message)
            return message
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update message due to integrity error."
            )

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found."
            )
        await db.delete(message)
        await db.commit()

    async def generate_answer(self, query: str, context: str, session_id: UUID, db: AsyncSession) -> dict:
        try:
            response = self.client.generate_answer(question=query, context=context)
            if not response or "answer" not in response:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate answer from Gemini API."
                )
            answer = response["answer"]
            message_data = {
                "session_id": session_id,
                "role": "assistant",
                "content": answer,
                "metadata": {"query": query, "context": context}
            }
            return await self.create_message(message_data, db)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating answer: {str(e)}"
            )