from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database.models import Deployment
from env import DEFAULT_DEPLOYMENT_NAME


class DeploymentService:
    @staticmethod
    async def create_deployment(deployment_data: dict, db: AsyncSession) -> Deployment:
        """
        Create a new deployment record in the database.
        """
        try:
            new_deployment = Deployment(**deployment_data)
            db.add(new_deployment)
            await db.commit()
            await db.refresh(new_deployment)
            return new_deployment
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment creation failed due to integrity error."
            )

    @staticmethod
    async def get_deployment_by_id(deployment_id: UUID, db: AsyncSession) -> Deployment:
        """
        Retrieve a deployment record by its ID.
        """
        result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment with ID {deployment_id} not found."
            )
        return deployment

    @staticmethod
    async def list_all_deployments(db: AsyncSession) -> List[Deployment]:
        """
        List all deployment records in the database.
        """
        result = await db.execute(select(Deployment))
        deployments = result.scalars().all()
        return deployments

    @staticmethod
    async def update_deployment(deployment_id: UUID, deployment_update: dict, db: AsyncSession) -> Deployment:
        """
        Update an existing deployment record by its ID.
        """
        result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment with ID {deployment_id} not found."
            )
        for key, value in deployment_update.items():
            setattr(deployment, key, value)
        try:
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment update failed due to integrity error."
            )

    @staticmethod
    async def delete_deployment(deployment_id: UUID, db: AsyncSession) -> None:
        """
        Delete a deployment record by its ID.
        """
        result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
        deployment = result.scalar_one_or_none()
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment with ID {deployment_id} not found."
            )
        await db.delete(deployment)
        await db.commit()