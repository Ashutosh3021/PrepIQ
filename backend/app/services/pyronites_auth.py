"""
Pyronites email + password authentication.

Pyronites (PyroCore) auth model:
  - POST /auth/login  → {"email": "..."} + Set-Cookie session_token (NO access_token, often NO id)
  - POST /auth/signup → {"id", "email", "created_at"} + session cookie
  - GET  /auth/me     → {"authenticated", "email", "id"} (requires session cookie on the client)

PrepIQ frontend expects Bearer access_token, so after a successful Pyronites
sign_in/sign_up we resolve the user id (via /auth/me or signup body) and mint
our own JWT with SECRET_KEY.

Test user (env-var gated, disabled when TEST_USER_EMAIL is unset):
  Set TEST_USER_EMAIL + TEST_USER_PASSWORD in .env to enable.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.password_rules import validate_email, validate_password
from app.core.pyronites_client import get_pyronites_client, pyronites_configured
from app.repositories import users as users_repo

logger = logging.getLogger(__name__)

# ── Retry helper for 429 Too Many Requests ────────────────────────────────────
T = TypeVar("T")

_MAX_RETRIES = 3
_BASE_DELAY = 2.0   # seconds — first retry after 2s
_MAX_DELAY = 30.0    # cap backoff


def _is_rate_limited(exc: Exception) -> bool:
    """Return True if the exception looks like a 429 rate-limit response."""
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg or "rate limit" in msg


def _parse_retry_after(exc: Exception) -> Optional[float]:
    """Try to extract Retry-After seconds from the exception message/headers."""
    msg = str(exc)
    # Common patterns: "Retry-After: 5", "retry-after: 5", "retry after 5"
    for token in ("retry-after:", "retry after"):
        idx = msg.lower().find(token)
        if idx >= 0:
            tail = msg[idx + len(token):].strip().split()[0]
            try:
                return float(tail)
            except ValueError:
                pass
    return None


async def _retry_on_429(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Call *fn* with retries when PyroCore returns 429.

    Uses Retry-After header if present, otherwise exponential backoff
    with jitter (2s → 4s → 8s, capped at 30s).
    """
    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if not _is_rate_limited(exc) or attempt == _MAX_RETRIES - 1:
                raise
            last_exc = exc
            retry_after = _parse_retry_after(exc)
            if retry_after and retry_after > 0:
                delay = min(retry_after, _MAX_DELAY)
            else:
                delay = min(_BASE_DELAY * (2 ** attempt), _MAX_DELAY)
            delay += random.uniform(0, 0.5)  # jitter
            logger.warning(
                "PyroCore 429 (attempt %d/%d) — retrying in %.1fs",
                attempt + 1, _MAX_RETRIES, delay,
            )
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]

# ── Test user (env-var gated — leave both unset to disable) ───────────────────
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "").strip().lower()
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "")
TEST_USER_ENABLED = bool(TEST_USER_EMAIL and TEST_USER_PASSWORD)
TEST_USER_ID = (
    str(uuid.uuid5(uuid.NAMESPACE_URL, f"prepiq:{TEST_USER_EMAIL}"))
    if TEST_USER_ENABLED
    else ""
)
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
    if not TEST_USER_ENABLED:
        return False
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
    secret = settings.SECRET_KEY.strip()
    if not secret or secret == "default-insecure-change-me":
        raise RuntimeError(
            "SECRET_KEY is not set or is the insecure default. "
            "Set a strong SECRET_KEY in your environment."
        )
    return secret


def _jwt_algorithm() -> str:
    return settings.JWT_ALGORITHM


def _token_expire_minutes() -> int:
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES


def _mint_access_token(user_id: str, email: str) -> Tuple[str, int]:
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
        return jwt.decode(token, secret, algorithms=algorithms)
    except Exception as e:
        logger.debug("JWT decode failed: %s", e)
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

        # Test user — checked AFTER validation so credentials are still vetted
        if _is_test_user(email, req.password):
            return _login_test_user(
                full_name=req.full_name or TEST_USER_FULL_NAME,
                college_name=req.college_name,
                program=req.program,
                year_of_study=str(req.year_of_study),
            )

        # Check for existing user before attempting signup to avoid duplicate token
        try:
            existing = users_repo.get_by_email(email)
            if existing:
                raise HTTPException(status_code=409, detail="Email already registered")
        except HTTPException:
            raise
        except Exception as e:
            # DB read failure is non-fatal — proceed with signup attempt
            logger.debug("Existing-user check failed (continuing): %s", e)

        client = get_pyronites_client()
        try:
            response = await _retry_on_429(client.auth.sign_up, email, req.password)
        except Exception as e:
            msg = str(e).lower()
            if "already" in msg or "exists" in msg or "registered" in msg or "409" in msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            if _is_rate_limited(e):
                logger.warning("signup rate-limited after retries: %s", e)
                raise HTTPException(
                    status_code=429,
                    detail="Auth service is rate-limited. Please try again later.",
                )
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

        # Test user — checked AFTER validation so credentials are still vetted
        if _is_test_user(email, req.password):
            return _login_test_user()

        client = get_pyronites_client()
        try:
            response = await _retry_on_429(client.auth.sign_in, email, req.password)
        except Exception as e:
            msg = str(e).lower()
            logger.info("login failed: %s", e)
            if _is_rate_limited(e):
                logger.warning("login rate-limited after retries: %s", e)
                raise HTTPException(
                    status_code=429,
                    detail="Auth service is rate-limited. Please try again later.",
                )
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

        # Profile is best-effort. JWT claims alone authorize the request.
        # Login already swallowed users-table errors; token validation must too,
        # otherwise every authenticated route becomes a generic 500 when the
        # Pyronites `users` table is missing, unreachable, or rejects the query.
        # NOTE: we intentionally do NOT attempt a lazy upsert here — doing so on
        # every authenticated request (esp. while the table is rate-limited)
        # amplifies PyroCore 429s. The users row is created at signup/login.
        profile: Dict[str, Any] = {}
        try:
            profile = users_repo.get(uid) or {}
        except Exception as e:
            logger.warning("users_repo.get failed for %s (continuing with JWT claims): %s", uid, e)
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
