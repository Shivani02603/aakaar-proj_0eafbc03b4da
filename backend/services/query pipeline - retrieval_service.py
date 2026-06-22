from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from env import CHUNK_SIZE, TOP_K
from sqlalchemy.sql import text

class RetrievalService:
    @staticmethod
    async def create_chunk(chunk_data: dict, db: AsyncSession) -> DocumentChunk:
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
        result = await db.execute(select(DocumentChunk))
        chunks = result.scalars().all()
        return chunks

    @staticmethod
    async def update_chunk(chunk_id: UUID, chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        chunk = await RetrievalService.get_chunk_by_id(chunk_id, db)
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
        chunk = await RetrievalService.get_chunk_by_id(chunk_id, db)
        await db.delete(chunk)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete chunk due to integrity error."
            )

    @staticmethod
    async def retrieve_top_chunks_by_similarity(query_embedding: List[float], db: AsyncSession) -> List[DocumentChunk]:
        try:
            sql_query = text("""
                SELECT id, file_id, session_id, content, embedding, metadata, chunk_index, token_count, created_at,
                embedding <-> :query_embedding AS similarity
                FROM document_chunks
                ORDER BY similarity ASC
                LIMIT :top_k
            """)
            result = await db.execute(
                sql_query.bindparams(query_embedding=query_embedding, top_k=TOP_K)
            )
            chunks = result.fetchall()
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No chunks found matching the query embedding."
                )
            return [DocumentChunk(**dict(row)) for row in chunks]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve chunks due to error: {str(e)}"
            )