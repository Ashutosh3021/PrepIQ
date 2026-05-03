from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from ..database import get_db

# Use the new Supabase-first auth service
from ..services.supabase_first_auth import (
    SupabaseFirstAuthService,
    SignupRequest,
    LoginRequest,
    UserResponse,
    get_current_user_from_token,
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
    return {"message": "Logged out successfully"}


@router.get("/profile")
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get user profile using Supabase token"""
    from ..models import User as UserModel
    user = await get_current_user_from_token(f"Bearer {credentials.credentials}", db)

    # BUG-L02: return the real created_at from the DB record, not datetime.now()
    db_user = db.query(UserModel).filter(UserModel.id == user["id"]).first()
    created_at = (
        db_user.created_at.isoformat()
        if db_user and db_user.created_at
        else None
    )

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "college_name": user.get("college_name", ""),
        "program": user.get("program", ""),
        "year_of_study": user.get("year_of_study", 1),
        "wizard_completed": user.get("wizard_completed", False),
        "created_at": created_at,
    }


@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user info"""
    return await get_current_user_from_token(f"Bearer {credentials.credentials}", db)


@router.get("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if token is valid"""
    try:
        user = await get_current_user_from_token(f"Bearer {credentials.credentials}")
        return {
            "valid": True,
            "user_id": user["id"],
            "email": user["email"],
        }
    except HTTPException:
        return {"valid": False}


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_token(req: RefreshTokenRequest):
    """Refresh access token using Supabase refresh token"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        response = supabase.auth.refresh_session(req.refresh_token)

        if response.session:
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
            }
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    except HTTPException:
        raise
    except Exception as e:
        err_str = str(e)
        # H-15: distinguish network/service errors from auth errors
        if any(code in err_str for code in ("503", "502", "504", "Service Unavailable", "Connection")):
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable. Please try again.",
            )
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {err_str}")
