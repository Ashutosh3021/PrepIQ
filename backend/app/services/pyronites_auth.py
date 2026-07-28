"""
Pyronites email + password authentication (Fix Phase B hardened).

- Email validation + strong password on signup
- No Google/GitHub OAuth
- Frontend: Authorization: Bearer <access_token>
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.core.password_rules import validate_email, validate_password
from app.core.pyronites_client import get_pyronites_client, pyronites_configured
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


def _as_dict(obj: Any) -> Optional[Dict[str, Any]]:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    # pydantic / simple namespace objects
    data: Dict[str, Any] = {}
    for key in (
        "id",
        "user_id",
        "email",
        "user",
        "session",
        "access_token",
        "refresh_token",
        "expires_in",
        "token",
        "user_metadata",
    ):
        if hasattr(obj, key):
            data[key] = getattr(obj, key)
    if data:
        return data
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return None


def _extract_user_and_session(response: Any) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    if response is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    root = _as_dict(response) or {}
    user = root.get("user") or (root.get("data") or {}).get("user") if isinstance(root.get("data"), dict) else None
    session = root.get("session") or (root.get("data") or {}).get("session") if isinstance(root.get("data"), dict) else None

    if user is None and root.get("id") and root.get("email"):
        user = root
    if user is None and isinstance(response, dict):
        user = response.get("user") or response

    user_d = _as_dict(user) if not isinstance(user, dict) else user
    if not user_d:
        raise HTTPException(status_code=401, detail="Authentication failed")

    session_d = _as_dict(session) if session is not None and not isinstance(session, dict) else session
    if session_d is None and isinstance(root, dict):
        # flat token on root
        token = root.get("access_token") or root.get("token")
        if token:
            session_d = {
                "access_token": token,
                "refresh_token": root.get("refresh_token"),
                "expires_in": root.get("expires_in"),
            }

    return user_d, session_d


def _user_id(user: Dict[str, Any]) -> str:
    uid = user.get("id") or user.get("user_id") or user.get("uid")
    if not uid:
        raise HTTPException(status_code=500, detail="Auth provider returned no user id")
    return str(uid)


def _decode_bearer_payload(token: str) -> Optional[Dict[str, Any]]:
    """Best-effort JWT decode (verify if JWT_SECRET set)."""
    try:
        import jwt
        import os

        secret = (os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "").strip()
        algorithms = [os.getenv("JWT_ALGORITHM", "HS256")]
        options = {"verify_signature": bool(secret and secret != "default-insecure-change-me")}
        if not options["verify_signature"]:
            # still parse claims for id/email when secret unknown (dev only)
            return jwt.decode(token, options={"verify_signature": False})
        return jwt.decode(token, secret, algorithms=algorithms)
    except Exception as e:
        logger.debug("JWT decode failed: %s", e)
        return None


def _user_from_claims(claims: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    uid = claims.get("sub") or claims.get("user_id") or claims.get("id")
    email = claims.get("email") or ""
    if not uid:
        return None
    return {"id": str(uid), "email": str(email).lower()}


class PyronitesAuthService:
    @staticmethod
    async def signup(req: SignupRequest) -> UserResponse:
        if not pyronites_configured():
            raise HTTPException(
                status_code=503,
                detail="Auth service is not configured (PYRONITES_URL / PYRONITES_KEY)",
            )

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
            if "already" in msg or "exists" in msg or "registered" in msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            logger.error("signup failed: %s", e)
            raise HTTPException(status_code=400, detail="Signup failed")

        user, session = _extract_user_and_session(response)
        uid = _user_id(user)
        email = (user.get("email") or str(req.email)).strip().lower()

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
        if not pyronites_configured():
            raise HTTPException(
                status_code=503,
                detail="Auth service is not configured (PYRONITES_URL / PYRONITES_KEY)",
            )

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
            profile = users_repo.upsert_profile(uid, email, {}) or {}
        except Exception:
            profile = {"full_name": "", "college_name": "", "program": "BTech", "year_of_study": 1}

        access = (session or {}).get("access_token") if session else None
        refresh = (session or {}).get("refresh_token") if session else None
        expires = (session or {}).get("expires_in") if session else None
        if not access:
            raise HTTPException(
                status_code=401,
                detail="Login succeeded but no access token was returned by auth provider",
            )

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
        if not token or not str(token).strip():
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        token = token.strip()
        user: Optional[Dict[str, Any]] = None

        if pyronites_configured():
            try:
                client = get_pyronites_client()
                auth = client.auth
                # Prefer explicit token APIs
                if hasattr(auth, "get_user"):
                    try:
                        user = auth.get_user(token)
                    except TypeError:
                        user = auth.get_user()
                elif hasattr(auth, "user"):
                    try:
                        user = auth.user(token)
                    except TypeError:
                        if hasattr(auth, "set_session"):
                            try:
                                auth.set_session(token)
                            except TypeError:
                                try:
                                    auth.set_session(access_token=token)
                                except Exception:
                                    pass
                        user = auth.user()
            except HTTPException:
                raise
            except Exception as e:
                logger.info("Pyronites token validation failed: %s", e)
                user = None

        if isinstance(user, dict) and "user" in user:
            user = user["user"]
        if user is not None and not isinstance(user, dict):
            user = _as_dict(user)

        if not user or not (user.get("id") or user.get("user_id")):
            claims = _decode_bearer_payload(token)
            if claims:
                user = _user_from_claims(claims)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

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
    `db` is ignored (kept for legacy call sites).
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
