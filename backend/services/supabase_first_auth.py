"""
Supabase-first authentication approach for PrepIQ
This replaces local database auth with Supabase as the primary auth system
"""

import os
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from supabase import create_client

# Supabase setup (lazy initialization)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# If credentials are not provided, the service is considered disabled.
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)

# Initialize client lazily
_supabase_client = None


def get_supabase_client():
    global _supabase_client
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase is not configured on the server")

    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    college_name: str
    program: str = "BTech"
    year_of_study: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    college_name: str
    program: str
    year_of_study: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = None
    needs_confirmation: bool = False


class SupabaseFirstAuthService:
    @staticmethod
    async def signup(req: SignupRequest):
        """Create user directly in Supabase (no local database)"""
        try:
            supabase = get_supabase_client()

            # Sign up the user
            response = supabase.auth.sign_up({
                "email": req.email,
                "password": req.password,
                "options": {
                    "data": {
                        "full_name": req.full_name,
                        "college_name": req.college_name,
                        "program": req.program,
                        "year_of_study": req.year_of_study,
                    }
                }
            })

            # Extract user object from possible response shapes
            user_data = None
            if hasattr(response, "data") and isinstance(response.data, dict) and "user" in response.data:
                user_data = response.data["user"]
            elif hasattr(response, "user"):
                user_data = response.user
            elif hasattr(response, "data") and hasattr(response.data, "user"):
                # pydantic model with attribute access
                user_data = response.data.user

            if not user_data:
                raise Exception("Unexpected response format from Supabase during signup")

            # Determine id and email safely
            if hasattr(user_data, "id"):
                user_id = getattr(user_data, "id")
                user_email = getattr(user_data, "email", None)
            elif isinstance(user_data, dict):
                user_id = user_data.get("id") or (user_data.get("user", {}) or {}).get("id")
                user_email = user_data.get("email") or (user_data.get("user", {}) or {}).get("email")
            else:
                raise Exception("Unexpected user data format from Supabase")

            # Try to read session if present
            session = None
            if hasattr(response, "data") and isinstance(response.data, dict) and "session" in response.data:
                session = response.data.get("session")
            elif hasattr(response, "session"):
                session = response.session

            # Detect whether confirmation is required
            needs_confirmation = False
            try:
                if hasattr(user_data, "email_confirmed_at"):
                    if not getattr(user_data, "email_confirmed_at"):
                        needs_confirmation = True
                elif isinstance(user_data, dict) and not user_data.get("email_confirmed_at"):
                    needs_confirmation = True
            except Exception:
                pass

            # Prepare tokens if session exists
            access_token = None
            refresh_token = None
            expires_in = None
            if session:
                if isinstance(session, dict):
                    access_token = session.get("access_token")
                    refresh_token = session.get("refresh_token")
                    expires_in = session.get("expires_in")
                else:
                    access_token = getattr(session, "access_token", None)
                    refresh_token = getattr(session, "refresh_token", None)
                    expires_in = getattr(session, "expires_in", None)

            return UserResponse(
                id=user_id,
                email=user_email,
                full_name=req.full_name,
                college_name=req.college_name,
                program=req.program,
                year_of_study=req.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                needs_confirmation=needs_confirmation or (session is None),
            )

        except HTTPException:
            # propagate service-not-configured
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Signup failed due to server error: {str(e)}")

    @staticmethod
    async def login(req: LoginRequest):
        """Authenticate user with Supabase"""
        try:
            supabase = get_supabase_client()

            response = supabase.auth.sign_in_with_password({
                "email": req.email,
                "password": req.password,
            })

            session = None
            user = None
            if hasattr(response, "data") and isinstance(response.data, dict):
                session = response.data.get("session")
                user = response.data.get("user")
            elif hasattr(response, "session") and hasattr(response, "user"):
                session = response.session
                user = response.user

            if not session or not user:
                # Could be invalid credentials or email not confirmed
                raise HTTPException(status_code=401, detail="Invalid credentials or email not confirmed")

            metadata = {}
            try:
                metadata = user.get("user_metadata", {}) if isinstance(user, dict) else getattr(user, "user_metadata", {}) or {}
            except Exception:
                metadata = {}

            # Extract tokens
            if isinstance(session, dict):
                access = session.get("access_token")
                refresh = session.get("refresh_token")
                expires = session.get("expires_in")
            else:
                access = getattr(session, "access_token", None)
                refresh = getattr(session, "refresh_token", None)
                expires = getattr(session, "expires_in", None)

            return UserResponse(
                id=user.get("id") if isinstance(user, dict) else getattr(user, "id"),
                email=user.get("email") if isinstance(user, dict) else getattr(user, "email"),
                full_name=metadata.get("full_name", "") if isinstance(metadata, dict) else getattr(metadata, "full_name", ""),
                college_name=metadata.get("college_name", "") if isinstance(metadata, dict) else getattr(metadata, "college_name", ""),
                program=metadata.get("program", "") if isinstance(metadata, dict) else getattr(metadata, "program", ""),
                year_of_study=metadata.get("year_of_study", 1) if isinstance(metadata, dict) else getattr(metadata, "year_of_study", 1),
                access_token=access,
                refresh_token=refresh,
                expires_in=expires,
                needs_confirmation=False,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login failed due to server error: {str(e)}")

    @staticmethod
    async def get_current_user(token: str):
        """Verify Supabase JWT token and get user info"""
        try:
            supabase = get_supabase_client()

            user_response = supabase.auth.get_user(token)

            user = None
            if hasattr(user_response, "data") and isinstance(user_response.data, dict) and "user" in user_response.data:
                user = user_response.data["user"]
            elif hasattr(user_response, "user"):
                user = user_response.user

            if not user:
                raise Exception("Unexpected user response format from Supabase")

            metadata = user.get("user_metadata", {}) if isinstance(user, dict) else getattr(user, "user_metadata", {}) or {}

            return {
                "id": user.get("id") if isinstance(user, dict) else getattr(user, "id"),
                "email": user.get("email") if isinstance(user, dict) else getattr(user, "email"),
                "full_name": metadata.get("full_name", "") if isinstance(metadata, dict) else getattr(metadata, "full_name", ""),
                "college_name": metadata.get("college_name", "") if isinstance(metadata, dict) else getattr(metadata, "college_name", ""),
                "program": metadata.get("program", "") if isinstance(metadata, dict) else getattr(metadata, "program", ""),
                "year_of_study": metadata.get("year_of_study", 1) if isinstance(metadata, dict) else getattr(metadata, "year_of_study", 1),
            }

        except Exception:
            raise HTTPException(status_code=401, detail="Invalid authentication token")


# Dependency for protected routes
async def get_current_user_from_token(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        token = authorization.split(" ")[1]  # Bearer <token>
        return await SupabaseFirstAuthService.get_current_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
