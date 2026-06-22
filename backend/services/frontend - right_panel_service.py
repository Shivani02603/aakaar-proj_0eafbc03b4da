from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import Message
from env import DEFAULT_CHAT_SETTINGS


class RightPanelService:
    async def create_message(self, message_data: dict, db: AsyncSession) -> Message:
        """
        Create a new message in the chat window.
        """
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
        """
        Retrieve a message by its ID.
        """
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found."
            )
        return message

    async def list_all_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        """
        List all messages for a given session.
        """
        result = await db.execute(select(Message).where(Message.session_id == session_id))
        messages = result.scalars().all()
        return messages

    async def update_message(self, message_id: UUID, message_data: dict, db: AsyncSession) -> Message:
        """
        Update an existing message.
        """
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
            db.add(message)
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
        """
        Delete a message by its ID.
        """
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found."
            )
        try:
            await db.delete(message)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete message due to integrity error."
            )