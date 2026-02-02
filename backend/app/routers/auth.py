from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

from ..database import get_db
from .. import models, schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.supabase_auth import SupabaseAuthService, SignupRequest, LoginRequest, UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable must be set")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use the SupabaseAuthService methods instead of duplicating them
@router.post("/signup", response_model=UserResponse)
async def signup(req: SignupRequest, db: Session = Depends(get_db)):
    return await SupabaseAuthService.signup(req, db)

@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    return await SupabaseAuthService.login(req, db)

@router.post("/logout")
async def logout():
    # In a real implementation, you might add the token to a blacklist
    return await SupabaseAuthService.logout("")

@router.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user = await SupabaseAuthService.get_current_user(credentials.credentials, db)
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "college_name": user.college_name,
        "program": user.program,
        "year_of_study": user.year_of_study,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "theme_preference": user.theme_preference,
        "language": user.language
    }

@router.get("/me")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "college_name": user.college_name,
            "program": user.program,
            "year_of_study": user.year_of_study,
            "created_at": user.created_at,
            "theme_preference": user.theme_preference,
            "language": user.language
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.put("/profile")
async def update_profile():
    # This will be implemented using the auth service
    # For now, return a placeholder
    return {"message": "Profile update endpoint"}