"""
Pyronites email + password authentication.

Pyronites (PyroCore) auth model:
  - POST /auth/login  → {"email": "..."} + Set-Cookie session_token (NO access_token, often NO id)
  - POST /auth/signup → {"id", "email", "created_at"} + session cookie
  - GET  /auth/me     → {"authenticated", "email", "id"} (requires session cookie on the client)

PrepIQ frontend expects Bearer access_token, so after a successful Pyronites
sign_in/sign_up we resolve the user id (via /auth/me or signup body) and mint
our own JWT with JWT_SECRET.

Temporary hardcoded test user (bypass provider):
  email:    tets@test.com
  password: 123aA@
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.core.password_rules import validate_email, validate_password
from app.core.pyronites_client import get_pyronites_client, pyronites_configured
from app.repositories import users as users_repo

logger = logging.getLogger(__name__)

# ── Temporary hardcoded test account (remove before public launch) ────────────
TEST_USER_EMAIL = "tets@test.com"
TEST_USER_PASSWORD = "123aA@"
TEST_USER_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"prepiq:{TEST_USER_EMAIL}"))
TEST_USER_FULL_NAME = "Test User"


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


def _is_test_user(email: str, password: str) -> bool:
    return (
        email.strip().lower() == TEST_USER_EMAIL
        and password == TEST_USER_PASSWORD
    )


def _login_test_user(
    full_name: str = TEST_USER_FULL_NAME,
    college_name: str = "",
    program: str = "BTech",
    year_of_study: str = "1",
) -> UserResponse:
    """Issue JWT for the hardcoded test account without calling Pyronites."""
    uid = TEST_USER_ID
    email = TEST_USER_EMAIL

    try:
        profile = users_repo.upsert_profile(
            uid,
            email,
            {
                "full_name": full_name or TEST_USER_FULL_NAME,
                "college_name": college_name,
                "program": program or "BTech",
                "year_of_study": year_of_study or "1",
                "wizard_completed": True,
            },
        ) or {}
    except Exception as e:
        logger.warning("test user profile upsert failed (continuing): %s", e)
        profile = {
            "full_name": full_name or TEST_USER_FULL_NAME,
            "college_name": college_name,
            "program": program or "BTech",
            "year_of_study": year_of_study or "1",
        }

    access, expires_in = _mint_access_token(uid, email)
    logger.info("Hardcoded test user login: %s", email)

    return UserResponse(
        id=uid,
        email=email,
        full_name=str(profile.get("full_name") or full_name or TEST_USER_FULL_NAME),
        college_name=str(profile.get("college_name") or college_name or ""),
        program=str(profile.get("program") or program or "BTech"),
        year_of_study=str(profile.get("year_of_study") or year_of_study or "1"),
        access_token=access,
        refresh_token=None,
        expires_in=expires_in,
        needs_confirmation=False,
    )


def _jwt_secret() -> str:
    secret = (os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "").strip()
    if not secret or secret == "default-insecure-change-me":
        secret = secret or "default-insecure-change-me"
    return secret


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _token_expire_minutes() -> int:
    try:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 8)))
    except ValueError:
        return 60 * 24 * 8


def _mint_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Issue PrepIQ JWT for the frontend (Pyronites uses cookies, not bearer tokens)."""
    import jwt

    expires_in = _token_expire_minutes() * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email.strip().lower(),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
        "iss": "prepiq",
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token, expires_in


def _decode_bearer_payload(token: str) -> Optional[Dict[str, Any]]:
    try:
        import jwt

        secret = _jwt_secret()
        algorithms = [_jwt_algorithm()]
        verify = bool(secret and secret != "default-insecure-change-me")
        if not verify:
            return jwt.decode(token, options={"verify_signature": False})
        return jwt.decode(token, secret, algorithms=algorithms)
    except Exception as e:
        logger.debug("JWT decode failed: %s", e)
        try:
            import jwt as _jwt

            return _jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None


def _as_dict(obj: Any) -> Optional[Dict[str, Any]]:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "dict") and callable(obj.dict):
        try:
            return obj.dict()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return None


def _pick_id(data: Optional[Dict[str, Any]]) -> Optional[str]:
    if not data:
        return None
    for key in ("id", "user_id", "uid", "sub"):
        val = data.get(key)
        if val is not None and str(val).strip() and not isinstance(val, (dict, list)):
            return str(val).strip()
    return None


def _pick_email(data: Optional[Dict[str, Any]], fallback: str = "") -> str:
    if data:
        em = data.get("email")
        if isinstance(em, str) and "@" in em:
            return em.strip().lower()
    return (fallback or "").strip().lower()


def _resolve_user_after_auth(client: Any, response: Any, email_fallback: str) -> Dict[str, str]:
    body = _as_dict(response) or {}
    email = _pick_email(body, email_fallback)
    uid = _pick_id(body)

    if not uid:
        try:
            me = None
            auth = client.auth
            if hasattr(auth, "user"):
                me = auth.user()
            me_d = _as_dict(me) or {}
            uid = _pick_id(me_d)
            email = _pick_email(me_d, email) or email
            if uid:
                logger.info("Resolved user id via /auth/me after Pyronites auth")
        except Exception as e:
            logger.warning("/auth/me after auth failed: %s", e)

    if not uid and email:
        try:
            row = users_repo.get_by_email(email)
            if row:
                uid = _pick_id(row)
                if uid:
                    logger.info("Resolved user id via users table email lookup")
        except Exception as e:
            logger.warning("users.get_by_email failed: %s", e)

    if not uid and email:
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"prepiq:{email}"))
        logger.warning(
            "Pyronites returned no user id; using deterministic id from email for %s",
            email,
        )

    if not uid:
        logger.error("Could not resolve user id (response keys=%s)", list(body.keys()))
        raise HTTPException(
            status_code=500,
            detail=(
                "Auth provider returned no user id. "
                "Pyronites login only returns email; /auth/me also failed."
            ),
        )

    if not email:
        raise HTTPException(status_code=500, detail="Auth provider returned no email")

    return {"id": uid, "email": email}


class PyronitesAuthService:
    @staticmethod
    async def signup(req: SignupRequest) -> UserResponse:
        email = str(req.email).strip().lower()

        # Hardcoded test user — works even if Pyronites is down
        if _is_test_user(email, req.password):
            return _login_test_user(
                full_name=req.full_name or TEST_USER_FULL_NAME,
                college_name=req.college_name,
                program=req.program,
                year_of_study=str(req.year_of_study),
            )

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
            response = client.auth.sign_up(email, req.password)
        except Exception as e:
            msg = str(e).lower()
            if "already" in msg or "exists" in msg or "registered" in msg or "409" in msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            logger.error("signup failed: %s", e)
            raise HTTPException(status_code=400, detail=f"Signup failed: {e}")

        resolved = _resolve_user_after_auth(client, response, email)
        uid, email = resolved["id"], resolved["email"]

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

        access, expires_in = _mint_access_token(uid, email)

        return UserResponse(
            id=uid,
            email=email,
            full_name=req.full_name,
            college_name=req.college_name,
            program=req.program,
            year_of_study=str(req.year_of_study),
            access_token=access,
            refresh_token=None,
            expires_in=expires_in,
            needs_confirmation=False,
        )

    @staticmethod
    async def login(req: LoginRequest) -> UserResponse:
        email = str(req.email).strip().lower()

        # Hardcoded test user — works even if Pyronites is down / unconfigured
        if _is_test_user(email, req.password):
            return _login_test_user()

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
            response = client.auth.sign_in(email, req.password)
        except Exception as e:
            msg = str(e).lower()
            logger.info("login failed: %s", e)
            if "confirm" in msg or "verified" in msg or "not confirmed" in msg:
                raise HTTPException(
                    status_code=401,
                    detail="Email is not confirmed at the auth provider.",
                )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        resolved = _resolve_user_after_auth(client, response, email)
        uid, email = resolved["id"], resolved["email"]

        try:
            profile = users_repo.upsert_profile(uid, email, {}) or {}
        except Exception:
            profile = {
                "full_name": "",
                "college_name": "",
                "program": "BTech",
                "year_of_study": 1,
            }

        access, expires_in = _mint_access_token(uid, email)

        return UserResponse(
            id=uid,
            email=email,
            full_name=str(profile.get("full_name") or ""),
            college_name=str(profile.get("college_name") or ""),
            program=str(profile.get("program") or "BTech"),
            year_of_study=str(profile.get("year_of_study") or 1),
            access_token=access,
            refresh_token=None,
            expires_in=expires_in,
            needs_confirmation=False,
        )

    @staticmethod
    async def get_user_from_token(token: str) -> Dict[str, Any]:
        if not token or not str(token).strip():
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        token = token.strip()
        claims = _decode_bearer_payload(token)
        uid: Optional[str] = None
        email = ""

        if claims:
            uid = (
                claims.get("sub")
                or claims.get("user_id")
                or claims.get("id")
            )
            if uid is not None:
                uid = str(uid)
            email = str(claims.get("email") or "").strip().lower()

        if not uid and pyronites_configured():
            try:
                client = get_pyronites_client()
                me = client.auth.user() if hasattr(client.auth, "user") else None
                me_d = _as_dict(me) or {}
                uid = _pick_id(me_d)
                email = _pick_email(me_d, email)
            except Exception as e:
                logger.info("Pyronites /auth/me token path failed: %s", e)

        if not uid:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

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
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = (
        authorization[7:].strip()
        if authorization.startswith("Bearer ")
        else authorization.strip()
    )
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await PyronitesAuthService.get_user_from_token(token)
