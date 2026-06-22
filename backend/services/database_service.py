from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import User, Session, UploadedFile
from env import DEFAULT_SESSION_NAME, DEFAULT_FILE_STATUS


class DatabaseService:
    # User CRUD operations
    async def create_user(self, user_data: dict, db: AsyncSession) -> User:
        try:
            new_user = User(**user_data)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed due to integrity error."
            )

    async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found."
            )
        return user

    async def list_all_users(self, db: AsyncSession) -> List[User]:
        result = await db.execute(select(User))
        return result.scalars().all()

    async def update_user(self, user_id: UUID, user_data: dict, db: AsyncSession) -> User:
        user = await self.get_user_by_id(user_id, db)
        for key, value in user_data.items():
            setattr(user, key, value)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, user_id: UUID, db: AsyncSession) -> None:
        user = await self.get_user_by_id(user_id, db)
        await db.delete(user)
        await db.commit()

    # Session CRUD operations
    async def create_session(self, session_data: dict, db: AsyncSession) -> Session:
        try:
            new_session = Session(**session_data)
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session creation failed due to integrity error."
            )

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found."
            )
        return session

    async def list_all_sessions(self, db: AsyncSession) -> List[Session]:
        result = await db.execute(select(Session))
        return result.scalars().all()

    async def update_session(self, session_id: UUID, session_data: dict, db: AsyncSession) -> Session:
        session = await self.get_session_by_id(session_id, db)
        for key, value in session_data.items():
            setattr(session, key, value)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def delete_session(self, session_id: UUID, db: AsyncSession) -> None:
        session = await self.get_session_by_id(session_id, db)
        await db.delete(session)
        await db.commit()

    # UploadedFile CRUD operations
    async def create_file(self, file_data: dict, db: AsyncSession) -> UploadedFile:
        try:
            new_file = UploadedFile(**file_data)
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

    async def get_file_by_id(self, file_id: UUID, db: AsyncSession) -> UploadedFile:
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found."
            )
        return file

    async def list_files(self, db: AsyncSession) -> List[UploadedFile]:
        result = await db.execute(select(UploadedFile))
        return result.scalars().all()

    async def update_file(self, file_id: UUID, file_data: dict, db: AsyncSession) -> UploadedFile:
        file = await self.get_file_by_id(file_id, db)
        for key, value in file_data.items():
            setattr(file, key, value)
        db.add(file)
        await db.commit()
        await db.refresh(file)
        return file

    async def delete_file(self, file_id: UUID, db: AsyncSession) -> None:
        file = await self.get_file_by_id(file_id, db)
        await db.delete(file)
        await db.commit()