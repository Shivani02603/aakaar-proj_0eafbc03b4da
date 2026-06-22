from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import timedelta
from database.models import User
from database.config import get_db
from backend.services.auth import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"[^@]+@[^@]+\.[^@]+")
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: str = Field(..., regex=r"[^@]+@[^@]+\.[^@]+")
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Dependency for protected routes
def get_current_user(token: str = Depends(decode_access_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Routes
@router.post("/auth/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    new_user = User(username=user_data.username, email=user_data.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"user_id": str(new_user.id)}, expires_delta=timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"user_id": str(user.id)}, expires_delta=timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return {"id": str(current_user.id), "username": current_user.username, "email": current_user.email}