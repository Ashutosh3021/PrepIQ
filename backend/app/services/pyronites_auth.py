"""
Pyronites email + password authentication (Phase 2).

Replaces Supabase-first auth. No Google/GitHub OAuth.

Frontend should send: Authorization: Bearer <access_token>
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.core.password_rules import validate_email, validate_password
from app.core.pyronites_client import get_pyronites_client
from app.repositories import users as users_repo

logger = logging.getLogger(__name__)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    full_name: str = ""
    college_name: str = ""
    program: str = "BTech"
    year_of_study: str = "1"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str = ""
    college_name: str = ""
    program: str = "BTech"
    year_of_study: str = "1"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = None
    needs_confirmation: bool = False


def _extract_user_and_session(response: Any) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Normalize Pyronites auth response shapes."""
    user = None
    session = None
    if response is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    if isinstance(response, dict):
        user = response.get("user") or response.get("data", {}).get("user") or response
        session = response.get("session") or response.get("data", {}).get("session")
    else:
        user = getattr(response, "user", None) or response
        session = getattr(response, "session", None)

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    if not isinstance(user, dict):
        user = {
            "id": str(getattr(user, "id", "")),
            "email": getattr(user, "email", "") or "",
            "user_metadata": getattr(user, "user_metadata", None) or {},
        }

    if session is not None and not isinstance(session, dict):
        session = {
            "access_token": getattr(session, "access_token", None),
            "refresh_token": getattr(session, "refresh_token", None),
            "expires_in": getattr(session, "expires_in", None),
        }

    return user, session


def _user_id(user: Dict[str, Any]) -> str:
    uid = user.get("id") or user.get("user_id")
    if not uid:
        raise HTTPException(status_code=500, detail="Auth provider returned no user id")
    return str(uid)


class PyronitesAuthService:
    @staticmethod
    async def signup(req: SignupRequest) -> UserResponse:
        ok, err = validate_email(str(req.email))
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        ok, err = validate_password(req.password)
        if not ok:
            raise HTTPException(status_code=400, detail=err)

        client = get_pyronites_client()
        try:
            response = client.auth.sign_up(str(req.email).strip().lower(), req.password)
        except Exception as e:
            msg = str(e).lower()
            if "already" in msg or "exists" in msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            logger.error("signup failed: %s", e)
            raise HTTPException(status_code=400, detail="Signup failed")

        user, session = _extract_user_and_session(response)
        uid = _user_id(user)
        email = (user.get("email") or str(req.email)).strip().lower()

        # Application profile row (password stays only in Pyronites auth)
        try:
            users_repo.upsert_profile(
                uid,
                email,
                {
                    "full_name": req.full_name,
                    "college_name": req.college_name,
                    "program": req.program,
                    "year_of_study": req.year_of_study,
                    "wizard_completed": False,
                },
            )
        except Exception as e:
            logger.warning("user profile upsert after signup failed: %s", e)

        access = (session or {}).get("access_token") if session else None
        refresh = (session or {}).get("refresh_token") if session else None
        expires = (session or {}).get("expires_in") if session else None

        return UserResponse(
            id=uid,
            email=email,
            full_name=req.full_name,
            college_name=req.college_name,
            program=req.program,
            year_of_study=str(req.year_of_study),
            access_token=access,
            refresh_token=refresh,
            expires_in=expires,
            needs_confirmation=access is None,
        )

    @staticmethod
    async def login(req: LoginRequest) -> UserResponse:
        ok, err = validate_email(str(req.email))
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        if not req.password:
            raise HTTPException(status_code=400, detail="Password is required")

        client = get_pyronites_client()
        try:
            response = client.auth.sign_in(str(req.email).strip().lower(), req.password)
        except Exception as e:
            logger.info("login failed: %s", e)
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user, session = _extract_user_and_session(response)
        uid = _user_id(user)
        email = (user.get("email") or str(req.email)).strip().lower()

        try:
            profile = users_repo.upsert_profile(uid, email, {})
        except Exception:
            profile = {"full_name": "", "college_name": "", "program": "BTech", "year_of_study": 1}

        access = (session or {}).get("access_token") if session else None
        refresh = (session or {}).get("refresh_token") if session else None
        expires = (session or {}).get("expires_in") if session else None
        if not access:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return UserResponse(
            id=uid,
            email=email,
            full_name=str(profile.get("full_name") or ""),
            college_name=str(profile.get("college_name") or ""),
            program=str(profile.get("program") or "BTech"),
            year_of_study=str(profile.get("year_of_study") or 1),
            access_token=access,
            refresh_token=refresh,
            expires_in=expires,
            needs_confirmation=False,
        )

    @staticmethod
    async def get_user_from_token(token: str) -> Dict[str, Any]:
        """Resolve bearer token to app user dict."""
        client = get_pyronites_client()
        user = None
        try:
            auth = client.auth
            # Prefer explicit token APIs when present
            if hasattr(auth, "get_user"):
                user = auth.get_user(token)
            elif hasattr(auth, "user"):
                # Some clients accept token kwarg or use session set from header
                try:
                    user = auth.user(token)
                except TypeError:
                    if hasattr(auth, "set_session"):
                        auth.set_session(token)
                    user = auth.user()
            else:
                raise HTTPException(status_code=501, detail="Auth provider missing user lookup")
        except HTTPException:
            raise
        except Exception as e:
            logger.info("token validation failed: %s", e)
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        if isinstance(user, dict) and "user" in user:
            user = user["user"]
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        if not isinstance(user, dict):
            user = {
                "id": str(getattr(user, "id", "")),
                "email": getattr(user, "email", "") or "",
            }

        uid = _user_id(user)
        email = (user.get("email") or "").strip().lower()

        profile = users_repo.get(uid)
        if not profile and email:
            try:
                profile = users_repo.upsert_profile(uid, email, {})
            except Exception as e:
                logger.warning("lazy profile create failed: %s", e)
                profile = {}

        profile = profile or {}
        return {
            "id": uid,
            "email": email or profile.get("email") or "",
            "full_name": profile.get("full_name") or "",
            "college_name": profile.get("college_name") or "",
            "program": profile.get("program") or "BTech",
            "year_of_study": profile.get("year_of_study") or 1,
            "wizard_completed": bool(profile.get("wizard_completed", False)),
            "exam_name": profile.get("exam_name"),
            "days_until_exam": profile.get("days_until_exam"),
            "focus_subjects": profile.get("focus_subjects") or [],
            "study_hours_per_day": profile.get("study_hours_per_day"),
            "target_score": profile.get("target_score"),
            "preparation_level": profile.get("preparation_level"),
            "exam_date": profile.get("exam_date"),
        }


async def get_current_user_from_token(authorization: str = None, db=None):
    """
    FastAPI-compatible dependency helper.

    `db` is ignored (SQLAlchemy removed from auth path) but kept so existing
    call sites that pass db continue to work.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:].strip() if authorization.startswith("Bearer ") else authorization.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await PyronitesAuthService.get_user_from_token(token)
