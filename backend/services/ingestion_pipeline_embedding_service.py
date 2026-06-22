from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from env import EMBEDDING_MODEL
from ai.embeddings import get_embedding


class EmbeddingService:
    @staticmethod
    async def create_embedding(chunk_id: UUID, db: AsyncSession) -> List[float]:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalars().first()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with ID {chunk_id} not found."
                )

            # Generate embedding for the chunk content
            embedding = get_embedding([chunk.content])[0]

            # Update the chunk with the generated embedding
            chunk.embedding = embedding
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)

            return embedding
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create embedding: {str(e)}"
            )

    @staticmethod
    async def get_embedding_by_id(chunk_id: UUID, db: AsyncSession) -> List[float]:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalars().first()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with ID {chunk_id} not found."
                )

            if not chunk.embedding:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No embedding found for DocumentChunk with ID {chunk_id}."
                )

            return chunk.embedding
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve embedding: {str(e)}"
            )

    @staticmethod
    async def list_all_embeddings(db: AsyncSession) -> List[DocumentChunk]:
        try:
            # Fetch all chunks with embeddings
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.embedding.is_not(None)))
            chunks = result.scalars().all()

            return chunks
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list embeddings: {str(e)}"
            )

    @staticmethod
    async def update_embedding(chunk_id: UUID, db: AsyncSession) -> List[float]:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalars().first()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with ID {chunk_id} not found."
                )

            # Generate new embedding for the chunk content
            embedding = get_embedding([chunk.content])[0]

            # Update the chunk with the new embedding
            chunk.embedding = embedding
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)

            return embedding
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update embedding: {str(e)}"
            )

    @staticmethod
    async def delete_embedding(chunk_id: UUID, db: AsyncSession) -> None:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalars().first()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with ID {chunk_id} not found."
                )

            # Remove the embedding from the chunk
            chunk.embedding = None
            db.add(chunk)
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete embedding: {str(e)}"
            )