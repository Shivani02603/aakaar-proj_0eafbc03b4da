from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import Citation
from env import DEFAULT_CITATION_SETTINGS


class CitationDisplayService:
    async def create_citation(self, citation_data: dict, db: AsyncSession) -> Citation:
        """
        Create a new citation record in the database.

        :param citation_data: Dictionary containing citation details.
        :param db: SQLAlchemy AsyncSession instance.
        :return: Created Citation object.
        """
        try:
            new_citation = Citation(**citation_data)
            db.add(new_citation)
            await db.commit()
            await db.refresh(new_citation)
            return new_citation
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create citation due to integrity constraints."
            )

    async def get_citation_by_id(self, citation_id: UUID, db: AsyncSession) -> Citation:
        """
        Retrieve a citation by its ID.

        :param citation_id: UUID of the citation.
        :param db: SQLAlchemy AsyncSession instance.
        :return: Citation object if found.
        """
        result = await db.execute(select(Citation).where(Citation.id == citation_id))
        citation = result.scalar_one_or_none()
        if not citation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Citation with ID {citation_id} not found."
            )
        return citation

    async def list_all_citations(self, db: AsyncSession) -> List[Citation]:
        """
        List all citations in the database.

        :param db: SQLAlchemy AsyncSession instance.
        :return: List of Citation objects.
        """
        result = await db.execute(select(Citation))
        citations = result.scalars().all()
        return citations

    async def update_citation(self, citation_id: UUID, citation_update: dict, db: AsyncSession) -> Citation:
        """
        Update an existing citation record.

        :param citation_id: UUID of the citation to update.
        :param citation_update: Dictionary containing updated citation details.
        :param db: SQLAlchemy AsyncSession instance.
        :return: Updated Citation object.
        """
        citation = await self.get_citation_by_id(citation_id, db)
        for key, value in citation_update.items():
            setattr(citation, key, value)
        try:
            db.add(citation)
            await db.commit()
            await db.refresh(citation)
            return citation
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update citation due to integrity constraints."
            )

    async def delete_citation(self, citation_id: UUID, db: AsyncSession) -> None:
        """
        Delete a citation record by its ID.

        :param citation_id: UUID of the citation to delete.
        :param db: SQLAlchemy AsyncSession instance.
        """
        citation = await self.get_citation_by_id(citation_id, db)
        try:
            await db.delete(citation)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete citation due to integrity constraints."
            )