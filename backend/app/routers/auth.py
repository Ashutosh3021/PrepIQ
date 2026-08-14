import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.pyronites_auth import (
    PyronitesAuthService,
    SignupRequest,
    LoginRequest,
    UserResponse,
    get_current_user_from_token,
)
from app.repositories import users as users_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse)
async def signup(req: SignupRequest):
    """Email + password signup via Pyronites (strong password + email validation)."""
    return await PyronitesAuthService.signup(req)


@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest):
    """Email + password login via Pyronites."""
    return await PyronitesAuthService.login(req)


@router.post("/logout")
async def logout():
    """Client-side token discard; optional server sign_out when supported."""
    try:
        from app.core.pyronites_client import get_pyronites_client

        client = get_pyronites_client()
        if hasattr(client.auth, "sign_out"):
            client.auth.sign_out()
    except Exception:
        pass
    return {"message": "Logged out successfully"}


@router.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user_from_token(f"Bearer {credentials.credentials}")
    db_user = {}
    try:
        db_user = users_repo.get(user["id"]) or {}
    except Exception as e:
        # PyroCore can be rate-limited (429); JWT claims already carry the
        # identity fields, so a failed read must not 500 the profile endpoint.
        logger.warning("profile read failed (continuing): %s", e)
        db_user = {}
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "college_name": user.get("college_name", ""),
        "program": user.get("program", ""),
        "year_of_study": user.get("year_of_study", 1),
        "wizard_completed": user.get("wizard_completed", False),
        "created_at": db_user.get("created_at"),
    }


@router.get("/me")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user_from_token(f"Bearer {credentials.credentials}")


@router.get("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user = await get_current_user_from_token(f"Bearer {credentials.credentials}")
        return {"valid": True, "user_id": user["id"], "email": user["email"]}
    except HTTPException:
        return {"valid": False}
