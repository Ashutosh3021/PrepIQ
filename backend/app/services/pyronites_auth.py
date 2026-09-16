"""
Pyronites email + password authentication.

Pyronites (PyroCore) auth model:
  - POST /auth/login  → {"email": "..."} + Set-Cookie session_token (NO access_token, often NO id)
  - POST /auth/signup → {"id", "email", "created_at"} + session cookie
  - GET  /auth/me     → {"authenticated", "email", "id"} (requires session cookie on the client)

PrepIQ frontend expects Bearer access_token, so after a successful Pyronites
sign_in/sign_up we resolve the user id (via /auth/me or signup body) and mint
our own JWT with SECRET_KEY.

NOTE: PyroCore's /auth/me only accepts session cookies, NOT API keys.
The pyronites SDK sends Authorization: Bearer {api_key} which fails on /auth/me.
We make direct httpx calls with the session cookie to resolve user identity.

Test user (env-var gated, disabled when TEST_USER_EMAIL is unset):
  Set TEST_USER_EMAIL + TEST_USER_PASSWORD in .env to enable.
"""
from __future__ import annotations

import logging
import os
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

# ── PyroCore call wrapper (SDK handles 429 retries internally) ────────────────
T = TypeVar("T")


def _extract_session_cookie(client: Any) -> str:
    """Extract session_token cookie from the pyronites SDK's httpx client.

    After sign_in/sign_up, PyroCore sets a session_token cookie in the
    response.  httpx.Client stores it in its cookie jar automatically.
    """
    try:
        http = getattr(client, "_http", None)
        wrapped = getattr(http, "_wrapped", http)
        http_client = getattr(wrapped, "_client", None)
        if http_client is None:
            return ""
        cookies = getattr(http_client, "cookies", None)
        if cookies is None:
            return ""
        # httpx.Cookies is a dict-like; iterate to find session_token
        for name, value in cookies.items():
            if name == "session_token":
                return str(value)
        # Also try direct key access
        val = cookies.get("session_token")
        return str(val) if val else ""
    except Exception as e:
        logger.debug("Could not extract session cookie: %s", e)
        return ""


def _is_rate_limited(exc: Exception) -> bool:
    """Return True if the exception looks like a 429 rate-limit response."""
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg or "rate limit" in msg


async def _call_pyrocore(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Call a pyronites SDK method with circuit breaker protection.

    The pyronites SDK (v1.2.0+) handles 429 Retry-After and exponential
    backoff internally. We do NOT add another retry layer on top — that
    would double the request count and amplify rate-limit violations.

    What this wrapper does:
      1. Checks the circuit breaker before calling.
      2. Records success/failure on the circuit breaker.
      3. Translates SDK exceptions into HTTP responses.
    """
    from app.core.circuit_breaker import pyrocore_breaker

    if pyrocore_breaker.is_open:
        raise HTTPException(
            status_code=503,
            detail="Auth service temporarily unavailable (circuit breaker open). Please retry later.",
        )

    try:
        result = fn(*args, **kwargs)
        pyrocore_breaker.record_success()
        return result
    except Exception as exc:
        if _is_rate_limited(exc):
            pyrocore_breaker.record_failure()
        raise

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


def _call_auth_me_with_cookie(session_cookie: str) -> Optional[Dict[str, Any]]:
    """Call PyroCore /auth/me directly with session cookie.

    The pyronites SDK sends Authorization: Bearer {api_key} which PyroCore's
    unscoped /auth/me rejects (it only accepts session cookies).  This function
    makes a direct httpx call with the session cookie to resolve user identity.
    """
    import httpx

    url = (os.getenv("PYRONITES_URL") or "").strip()
    if not url or not session_cookie:
        return None

    try:
        resp = httpx.get(
            f"{url.rstrip('/')}/auth/me",
            cookies={"session_token": session_cookie},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("authenticated"):
                return data
        logger.debug("/auth/me with cookie returned HTTP %s", resp.status_code)
    except Exception as e:
        logger.debug("/auth/me with cookie failed: %s", e)
    return None


def _resolve_user_after_auth(client: Any, response: Any, email_fallback: str, session_cookie: str = "") -> Dict[str, str]:
    body = _as_dict(response) or {}
    email = _pick_email(body, email_fallback)
    uid = _pick_id(body)

    # 1. Try direct /auth/me with session cookie (most reliable for login)
    if not uid and session_cookie:
        try:
            me_d = _call_auth_me_with_cookie(session_cookie)
            if me_d:
                uid = _pick_id(me_d)
                email = _pick_email(me_d, email) or email
                if uid:
                    logger.info("Resolved user id via /auth/me (session cookie)")
        except Exception as e:
            logger.warning("/auth/me with cookie failed: %s", e)

    # 2. Try SDK auth.user() (works for signup where response has id)
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
                logger.info("Resolved user id via /auth/me (SDK)")
        except Exception as e:
            logger.warning("/auth/me via SDK failed: %s", e)

    # 3. Try local users table email lookup
    if not uid and email:
        try:
            row = users_repo.get_by_email(email)
            if row:
                uid = _pick_id(row)
                if uid:
                    logger.info("Resolved user id via users table email lookup")
        except Exception as e:
            logger.warning("users.get_by_email failed: %s", e)

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
            response = await _call_pyrocore(client.auth.sign_up, email, req.password)
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

        session_cookie = _extract_session_cookie(client)
        resolved = _resolve_user_after_auth(client, response, email, session_cookie)
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
            response = await _call_pyrocore(client.auth.sign_in, email, req.password)
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

        session_cookie = _extract_session_cookie(client)
        resolved = _resolve_user_after_auth(client, response, email, session_cookie)
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
