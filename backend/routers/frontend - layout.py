from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Layout
from database.config import get_db
from backend.services.auth import decode_access_token

router = APIRouter(
    prefix="/frontend-layout",
    tags=["Frontend - Layout"]
)

# Pydantic Schemas
class LayoutBase(BaseModel):
    name: str = Field(..., example="Two-Panel Layout")
    description: Optional[str] = Field(None, example="A layout with two panels")

class LayoutCreate(LayoutBase):
    pass

class LayoutUpdate(LayoutBase):
    pass

class LayoutResponse(LayoutBase):
    id: UUID
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

# Dependency for JWT authentication
def get_current_user(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token

# Routes
@router.post("/", response_model=LayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_layout(layout: LayoutCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_layout = Layout(**layout.dict())
    db.add(new_layout)
    db.commit()
    db.refresh(new_layout)
    return new_layout

@router.get("/", response_model=List[LayoutResponse], status_code=status.HTTP_200_OK)
async def list_layouts(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layouts = db.query(Layout).all()
    return layouts

@router.get("/{layout_id}", response_model=LayoutResponse, status_code=status.HTTP_200_OK)
async def get_layout(layout_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    return layout

@router.put("/{layout_id}", response_model=LayoutResponse, status_code=status.HTTP_200_OK)
async def update_layout(layout_id: UUID, layout_update: LayoutUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    for key, value in layout_update.dict().items():
        setattr(layout, key, value)
    db.commit()
    db.refresh(layout)
    return layout

@router.delete("/{layout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_layout(layout_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    db.delete(layout)
    db.commit()
    return None