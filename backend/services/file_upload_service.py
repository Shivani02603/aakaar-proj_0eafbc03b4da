from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import UploadedFile
from env import UPLOAD_DIRECTORY
import os
import shutil


class FileUploadService:
    @staticmethod
    async def create_file(file_data: dict, db: AsyncSession) -> UploadedFile:
        """
        Create a new file record in the database.
        """
        new_file = UploadedFile(**file_data)
        try:
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File creation failed due to integrity error."
            )

    @staticmethod
    async def get_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        """
        Retrieve a file record by its ID.
        """
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found."
            )
        return file

    @staticmethod
    async def list_files(db: AsyncSession) -> List[UploadedFile]:
        """
        List all file records in the database.
        """
        result = await db.execute(select(UploadedFile))
        files = result.scalars().all()
        return files

    @staticmethod
    async def update_file(file_id: UUID, file_data: dict, db: AsyncSession) -> UploadedFile:
        """
        Update an existing file record.
        """
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found."
            )
        for key, value in file_data.items():
            setattr(file, key, value)
        try:
            await db.commit()
            await db.refresh(file)
            return file
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File update failed due to integrity error."
            )

    @staticmethod
    async def delete_file(file_id: UUID, db: AsyncSession) -> None:
        """
        Delete a file record by its ID.
        """
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found."
            )
        try:
            await db.delete(file)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File deletion failed due to integrity error."
            )

    @staticmethod
    def save_file_to_disk(uploaded_file, destination: str) -> None:
        """
        Save an uploaded file to the specified destination directory.
        """
        try:
            os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIRECTORY, destination)
            with open(file_path, "wb") as file:
                shutil.copyfileobj(uploaded_file.file, file)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file to disk: {str(e)}"
            )