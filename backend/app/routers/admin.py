from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin, get_password_hash
from app.models.domain_models import User
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])

class InstructorCreate(BaseModel):
    email: str
    full_name: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True

@router.post("/instructors", response_model=UserResponse)
def create_instructor(
    request: InstructorCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_instructor = User(
        email=request.email,
        full_name=request.full_name,
        role="instructor",
        password_hash=get_password_hash(request.password)
    )
    db.add(new_instructor)
    db.commit()
    db.refresh(new_instructor)
    return new_instructor

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    users = db.query(User).all()
    return users
