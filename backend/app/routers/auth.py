from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

from ..database import get_db
from .. import models, schemas

# Use the new Supabase-first auth service
from ..services.supabase_first_auth import (
    SupabaseFirstAuthService, 
    SignupRequest, 
    LoginRequest, 
    UserResponse,
    get_current_user_from_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Security setup
security = HTTPBearer()

@router.post("/signup", response_model=UserResponse)
async def signup(req: SignupRequest):
    """Supabase-first signup - creates user directly in Supabase"""
    return await SupabaseFirstAuthService.signup(req)

@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest):
    """Supabase-first login - authenticates with Supabase"""
    return await SupabaseFirstAuthService.login(req)

@router.post("/logout")
async def logout():
    """Logout (client-side token invalidation)"""
    # Supabase handles token invalidation on client side
    return {"message": "Logged out successfully"}

@router.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user profile using Supabase token"""
    user = await get_current_user_from_token(f"Bearer {credentials.credentials}")
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "college_name": user["college_name"],
        "program": user["program"],
        "year_of_study": user["year_of_study"],
        "created_at": datetime.now().isoformat()  # Supabase handles this
    }

@router.get("/me")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user info"""
    return await get_current_user_from_token(f"Bearer {credentials.credentials}")

@router.get("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if token is valid"""
    try:
        user = await get_current_user_from_token(f"Bearer {credentials.credentials}")
        return {
            "valid": True,
            "user_id": user["id"],
            "email": user["email"]
        }
    except HTTPException:
        return {"valid": False}

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(req: RefreshTokenRequest):
    """Refresh access token using Supabase refresh token"""
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Exchange refresh token for new session
        response = supabase.auth.refresh_session(req.refresh_token)
        
        if response.session:
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")