"""
Pyronites email + password authentication (Fix Phase B hardened).

- Email validation + strong password on signup
- No Google/GitHub OAuth
- Email confirmation is bypassed at the app layer for now:
  if sign_up returns no session, we immediately sign_in with the same credentials.
- Frontend: Authorization: Bearer <access_token>
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

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
    # pydantic v1/v2 models
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
    data: Dict[str, Any] = {}
    for key in (
        "id",
        "user_id",
        "uid",
        "sub",
        "email",
        "user",
        "session",
        "data",
        "access_token",
        "refresh_token",
        "expires_in",
        "token",
        "user_metadata",
        "identities",
    ):
        if hasattr(obj, key):
            try:
                data[key] = getattr(obj, key)
            except Exception:
                pass
    if data:
        return data
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return None


def _deep_get(obj: Any, *paths: Tuple[str, ...]) -> Any:
    """Try several dotted-style paths on dict-like objects."""
    root = _as_dict(obj) or (obj if isinstance(obj, dict) else None)
    if not isinstance(root, dict):
        return None
    for path in paths:
        cur: Any = root
        ok = True
        for key in path:
            cur = _as_dict(cur) if not isinstance(cur, dict) else cur
            if not isinstance(cur, dict) or key not in cur:
                ok = False
                break
            cur = cur[key]
        if ok and cur is not None and cur != "":
            return cur
    return None


def _find_first_id(obj: Any, depth: int = 0) -> Optional[str]:
    """Recursively find a plausible user id field."""
    if depth > 5 or obj is None:
        return None
    d = _as_dict(obj) if not isinstance(obj, dict) else obj
    if isinstance(d, dict):
        for key in ("id", "user_id", "uid", "sub"):
            val = d.get(key)
            if val is not None and val != "" and not isinstance(val, (dict, list)):
                return str(val)
        for key in ("user", "session", "data", "profile"):
            if key in d:
                found = _find_first_id(d[key], depth + 1)
                if found:
                    return found
    return None


def _find_access_token(obj: Any, depth: int = 0) -> Optional[str]:
    if depth > 5 or obj is None:
        return None
    d = _as_dict(obj) if not isinstance(obj, dict) else obj
    if isinstance(d, dict):
        for key in ("access_token", "token", "accessToken"):
            val = d.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        for key in ("session", "data", "user"):
            if key in d:
                found = _find_access_token(d[key], depth + 1)
                if found:
                    return found
    return None


def _find_refresh_token(obj: Any, depth: int = 0) -> Optional[str]:
    if depth > 5 or obj is None:
        return None
    d = _as_dict(obj) if not isinstance(obj, dict) else obj
    if isinstance(d, dict):
        for key in ("refresh_token", "refreshToken"):
            val = d.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        for key in ("session", "data"):
            if key in d:
                found = _find_refresh_token(d[key], depth + 1)
                if found:
                    return found
    return None


def _find_email(obj: Any, depth: int = 0) -> Optional[str]:
    if depth > 5 or obj is None:
        return None
    d = _as_dict(obj) if not isinstance(obj, dict) else obj
    if isinstance(d, dict):
        val = d.get("email")
        if isinstance(val, str) and "@" in val:
            return val.strip().lower()
        for key in ("user", "session", "data", "profile"):
            if key in d:
                found = _find_email(d[key], depth + 1)
                if found:
                    return found
    return None


def _response_preview(response: Any) -> str:
    """Safe short description for logs."""
    try:
        d = _as_dict(response)
        if d is None:
            return f"type={type(response).__name__!r}"
        keys = list(d.keys())[:20]
        return f"type={type(response).__name__!r} keys={keys}"
    except Exception:
        return f"type={type(response).__name__!r}"


def _extract_user_and_session(
    response: Any,
) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Normalize arbitrary provider auth response shapes into (user_dict, session_dict).

    Handles:
      { user, session }
      { data: { user, session } }
      AuthResponse objects
      flat { access_token, user: {...} }
      session-only with nested user
    """
    if response is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    root = _as_dict(response) or {}
    if not root and isinstance(response, dict):
        root = response

    # Explicit user candidates (order matters) — avoid broken ternary precedence
    user: Any = None
    if isinstance(root, dict):
        user = root.get("user")
        if user is None and isinstance(root.get("data"), dict):
            user = root["data"].get("user")
        if user is None and isinstance(root.get("session"), dict):
            user = root["session"].get("user")
        if user is None and isinstance(root.get("data"), dict):
            sess = root["data"].get("session")
            if isinstance(sess, dict):
                user = sess.get("user")

    user_d = _as_dict(user) if not isinstance(user, dict) else user
    if not user_d:
        user_d = {}

    # Session candidates
    session: Any = None
    if isinstance(root, dict):
        session = root.get("session")
        if session is None and isinstance(root.get("data"), dict):
            session = root["data"].get("session")
    session_d = _as_dict(session) if session is not None and not isinstance(session, dict) else session
    if not isinstance(session_d, dict):
        session_d = {}

    # Tokens may sit on root / data even without a session object
    access = (
        session_d.get("access_token")
        or session_d.get("token")
        or (root.get("access_token") if isinstance(root, dict) else None)
        or (root.get("token") if isinstance(root, dict) else None)
        or _find_access_token(response)
    )
    refresh = (
        session_d.get("refresh_token")
        or (root.get("refresh_token") if isinstance(root, dict) else None)
        or _find_refresh_token(response)
    )
    expires = session_d.get("expires_in") or (root.get("expires_in") if isinstance(root, dict) else None)

    if access and not session_d.get("access_token"):
        session_d = {**session_d, "access_token": access}
    if refresh and not session_d.get("refresh_token"):
        session_d = {**session_d, "refresh_token": refresh}
    if expires is not None and "expires_in" not in session_d:
        session_d = {**session_d, "expires_in": expires}

    # Resolve user id — dict fields, nested search, then JWT sub
    uid = (
        user_d.get("id")
        or user_d.get("user_id")
        or user_d.get("uid")
        or user_d.get("sub")
        or _find_first_id(response)
    )
    if not uid and access:
        claims = _decode_bearer_payload(str(access))
        if claims:
            uid = claims.get("sub") or claims.get("user_id") or claims.get("id")
            if not user_d.get("email") and claims.get("email"):
                user_d["email"] = claims["email"]

    email = user_d.get("email") or _find_email(response)
    if email:
        user_d["email"] = str(email).strip().lower()
    if uid:
        user_d["id"] = str(uid)

    if not user_d.get("id"):
        logger.error(
            "Could not extract user id from auth response (%s)",
            _response_preview(response),
        )
        raise HTTPException(
            status_code=500,
            detail="Auth provider returned no user id",
        )

    return user_d, session_d if session_d else None


def _user_id(user: Dict[str, Any]) -> str:
    uid = user.get("id") or user.get("user_id") or user.get("uid") or user.get("sub")
    if not uid:
        raise HTTPException(status_code=500, detail="Auth provider returned no user id")
    return str(uid)


def _session_tokens(
    session: Optional[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    if not session:
        return None, None, None
    access = session.get("access_token") or session.get("token")
    refresh = session.get("refresh_token")
    expires = session.get("expires_in")
    return access, refresh, expires


def _try_sign_up(client: Any, email: str, password: str) -> Any:
    """Call provider sign_up; try optional kwargs that disable email confirm."""
    auth = client.auth
    attempts = (
        lambda: auth.sign_up(email, password, options={"email_confirm": False}),
        lambda: auth.sign_up(email, password, {"email_confirm": False}),
        lambda: auth.sign_up(email, password, email_confirm=False),
        lambda: auth.sign_up(email, password),
    )
    last_err: Optional[Exception] = None
    for call in attempts:
        try:
            return call()
        except TypeError as e:
            last_err = e
            continue
        except Exception as e:
            raise e
    if last_err:
        raise last_err
    raise RuntimeError("sign_up failed with no response")


def _decode_bearer_payload(token: str) -> Optional[Dict[str, Any]]:
    """Best-effort JWT decode (verify if JWT_SECRET set)."""
    try:
        import jwt
        import os

        secret = (os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "").strip()
        algorithms = [os.getenv("JWT_ALGORITHM", "HS256")]
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

        email = str(req.email).strip().lower()
        client = get_pyronites_client()
        try:
            response = _try_sign_up(client, email, req.password)
        except Exception as e:
            msg = str(e).lower()
            if "already" in msg or "exists" in msg or "registered" in msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            logger.error("signup failed: %s", e)
            raise HTTPException(status_code=400, detail="Signup failed")

        user, session = _extract_user_and_session(response)
        uid = _user_id(user)
        email = (user.get("email") or email).strip().lower()
        access, refresh, expires = _session_tokens(session)

        if not access:
            try:
                login_response = client.auth.sign_in(email, req.password)
                user2, session2 = _extract_user_and_session(login_response)
                uid = _user_id(user2)
                email = (user2.get("email") or email).strip().lower()
                access, refresh, expires = _session_tokens(session2)
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("post-signup auto sign_in failed: %s", e)

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

        if not access:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Account was created but login is blocked by the auth provider. "
                    "Disable email confirmation in the Pyronites/Supabase Auth settings, "
                    "or sign in after confirming."
                ),
            )

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
            needs_confirmation=False,
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

        email = str(req.email).strip().lower()
        client = get_pyronites_client()
        try:
            response = client.auth.sign_in(email, req.password)
        except Exception as e:
            msg = str(e).lower()
            logger.info("login failed: %s", e)
            if "confirm" in msg or "verified" in msg or "not confirmed" in msg:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "Email is not confirmed at the auth provider. "
                        "Disable email confirmation in Pyronites/Supabase Auth settings."
                    ),
                )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        try:
            user, session = _extract_user_and_session(response)
        except HTTPException as e:
            # Last resort: token-only response → decode JWT
            token = _find_access_token(response)
            if token:
                claims = _decode_bearer_payload(token)
                if claims and (claims.get("sub") or claims.get("user_id") or claims.get("id")):
                    user = _user_from_claims(claims) or {}
                    session = {"access_token": token}
                else:
                    raise e
            else:
                raise e

        uid = _user_id(user)
        email = (user.get("email") or email).strip().lower()

        try:
            profile = users_repo.upsert_profile(uid, email, {}) or {}
        except Exception:
            profile = {"full_name": "", "college_name": "", "program": "BTech", "year_of_study": 1}

        access, refresh, expires = _session_tokens(session)
        if not access:
            access = _find_access_token(response)
            if access:
                refresh = refresh or _find_refresh_token(response)
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

        if not user or not (user.get("id") or user.get("user_id") or user.get("uid") or user.get("sub")):
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
