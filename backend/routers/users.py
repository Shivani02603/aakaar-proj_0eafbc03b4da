from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database.models import User
from database.config import get_db
from backend.services.auth import decode_access_token

router = APIRouter()

# Pydantic Schemas
class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"[^@]+@[^@]+\.[^@]+")
    password: str = Field(..., min_length=6)

class UserUpdateSchema(BaseModel):
    username: str = Field(None, min_length=3, max_length=50)
    email: str = Field(None, regex=r"[^@]+@[^@]+\.[^@]+")

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

# Dependency for protected routes
def get_current_user(token: str = Depends(decode_access_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Routes
@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    return [{"id": str(user.id), "username": user.username, "email": user.email} for user in users]

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "username": user.username, "email": user.email}

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_data: UserUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.username:
        user.username = user_data.username
    if user_data.email:
        user.email = user_data.email
    
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "username": user.username, "email": user.email}

@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}