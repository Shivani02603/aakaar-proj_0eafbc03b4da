from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from env import EMBEDDING_MODEL
from ai.embeddings import get_embedding


class QueryEmbeddingService:
    async def embed_query(self, query: str, db: AsyncSession) -> List[float]:
        """
        Embed a user query into a vector representation using the embedding model.

        :param query: The query string to embed.
        :param db: SQLAlchemy AsyncSession instance.
        :return: A list of floats representing the embedded query.
        """
        try:
            embedding = get_embedding([query])
            if not embedding or len(embedding) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate embedding for the query."
                )
            return embedding[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error embedding query: {str(e)}"
            )

    async def create_document_chunk(self, chunk: DocumentChunk, db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk in the database.

        :param chunk: DocumentChunk instance to create.
        :param db: SQLAlchemy AsyncSession instance.
        :return: The created DocumentChunk instance.
        """
        try:
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integrity error while creating document chunk: {str(e)}"
            )

    async def get_document_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.

        :param chunk_id: UUID of the document chunk.
        :param db: SQLAlchemy AsyncSession instance.
        :return: The DocumentChunk instance if found.
        """
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
        chunk = result.scalar_one_or_none()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document chunk with ID {chunk_id} not found."
            )
        return chunk

    async def list_all_document_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        """
        List all document chunks in the database.

        :param db: SQLAlchemy AsyncSession instance.
        :return: A list of DocumentChunk instances.
        """
        result = await db.execute(select(DocumentChunk))
        chunks = result.scalars().all()
        return chunks

    async def update_document_chunk(self, chunk_id: UUID, chunk_update: dict, db: AsyncSession) -> DocumentChunk:
        """
        Update a document chunk by its ID.

        :param chunk_id: UUID of the document chunk to update.
        :param chunk_update: Dictionary containing the fields to update.
        :param db: SQLAlchemy AsyncSession instance.
        :return: The updated DocumentChunk instance.
        """
        chunk = await self.get_document_chunk_by_id(chunk_id, db)
        for key, value in chunk_update.items():
            setattr(chunk, key, value)
        try:
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integrity error while updating document chunk: {str(e)}"
            )

    async def delete_document_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.

        :param chunk_id: UUID of the document chunk to delete.
        :param db: SQLAlchemy AsyncSession instance.
        """
        chunk = await self.get_document_chunk_by_id(chunk_id, db)
        try:
            await db.delete(chunk)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting document chunk: {str(e)}"
            )