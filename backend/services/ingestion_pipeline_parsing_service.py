from typing import List, Optional
from uuid import UUID
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import DocumentChunk
from env import CHUNK_SIZE, CHUNK_OVERLAP

class ParsingService:
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
    async def update_chunk(chunk_id: UUID, chunk_update: dict, db: AsyncSession) -> DocumentChunk:
        chunk = await ParsingService.get_chunk_by_id(chunk_id, db)
        for key, value in chunk_update.items():
            setattr(chunk, key, value)
        try:
            db.add(chunk)
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
        chunk = await ParsingService.get_chunk_by_id(chunk_id, db)
        await db.delete(chunk)
        await db.commit()

    @staticmethod
    def parse_excel_file(file_path: str) -> List[dict]:
        try:
            df = pd.read_excel(file_path)
            chunks = []
            for index, row in df.iterrows():
                chunk_content = row.to_dict()
                chunks.append(chunk_content)
            return chunks
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse Excel file: {str(e)}"
            )

    @staticmethod
    def split_content_into_chunks(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        if chunk_size <= overlap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chunk size must be greater than overlap."
            )
        chunks = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunks.append(content[start:end])
            start += chunk_size - overlap
        return chunks

    @staticmethod
    async def process_and_store_chunks(file_id: UUID, session_id: UUID, content: str, metadata: dict, db: AsyncSession) -> List[DocumentChunk]:
        chunks = ParsingService.split_content_into_chunks(content)
        stored_chunks = []
        for index, chunk_content in enumerate(chunks):
            chunk_data = {
                "file_id": file_id,
                "session_id": session_id,
                "content": chunk_content,
                "metadata": metadata,
                "chunk_index": index,
                "token_count": len(chunk_content.split()),
            }
            stored_chunk = await ParsingService.create_chunk(chunk_data, db)
            stored_chunks.append(stored_chunk)
        return stored_chunks