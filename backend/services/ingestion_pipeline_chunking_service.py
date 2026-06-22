from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from env import CHUNK_SIZE, CHUNK_OVERLAP


class ChunkingService:
    @staticmethod
    async def create_chunk(chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk in the database.
        """
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create chunk due to integrity error."
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
                detail=f"Chunk with ID {chunk_id} not found."
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
    async def update_chunk(chunk_id: UUID, chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Update an existing document chunk.
        """
        chunk = await ChunkingService.get_chunk_by_id(chunk_id, db)
        for key, value in chunk_data.items():
            setattr(chunk, key, value)
        try:
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update chunk due to integrity error."
            )

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
        chunk = await ChunkingService.get_chunk_by_id(chunk_id, db)
        await db.delete(chunk)
        await db.commit()

    @staticmethod
    def split_content_into_chunks(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Split content into overlapping chunks.
        """
        if chunk_size <= overlap:
            raise ValueError("Chunk size must be greater than overlap.")

        chunks = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunks.append(content[start:end])
            start += chunk_size - overlap
        return chunks

    @staticmethod
    async def process_and_store_chunks(file_id: UUID, session_id: UUID, content: str, metadata: dict, db: AsyncSession) -> List[DocumentChunk]:
        """
        Process content into chunks and store them in the database.
        """
        chunks = ChunkingService.split_content_into_chunks(content)
        stored_chunks = []

        for index, chunk_content in enumerate(chunks):
            chunk_data = {
                "file_id": file_id,
                "session_id": session_id,
                "content": chunk_content,
                "metadata": metadata,
                "chunk_index": index,
                "token_count": len(chunk_content),
            }
            stored_chunk = await ChunkingService.create_chunk(chunk_data, db)
            stored_chunks.append(stored_chunk)

        return stored_chunks