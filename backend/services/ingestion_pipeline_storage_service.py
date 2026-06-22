from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from env import CHUNK_SIZE, CHUNK_OVERLAP


class StorageService:
    @staticmethod
    async def create_chunk(chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk and store it in the database.
        """
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integrity error occurred while creating chunk: {str(e)}"
            )

    @staticmethod
    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
        chunk = result.scalar_one_or_none()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document chunk with ID {chunk_id} not found."
            )
        return chunk

    @staticmethod
    async def list_all_chunks(db: AsyncSession) -> List[DocumentChunk]:
        """
        List all document chunks in the database.
        """
        result = await db.execute(select(DocumentChunk))
        chunks = result.scalars().all()
        return chunks

    @staticmethod
    async def update_chunk(chunk_id: UUID, chunk_update_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Update an existing document chunk.
        """
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
        chunk = result.scalar_one_or_none()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document chunk with ID {chunk_id} not found."
            )
        for key, value in chunk_update_data.items():
            setattr(chunk, key, value)
        try:
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integrity error occurred while updating chunk: {str(e)}"
            )

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
        chunk = result.scalar_one_or_none()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document chunk with ID {chunk_id} not found."
            )
        try:
            await db.delete(chunk)
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integrity error occurred while deleting chunk: {str(e)}"
            )