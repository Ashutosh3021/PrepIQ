"""
Supabase-first authentication approach for PrepIQ
This replaces local database auth with Supabase as the primary auth system
Includes lazy user creation in application database
"""

import os
from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from supabase import create_client
from sqlalchemy.orm import Session

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
    college_name: str = ""
    program: str = "BTech"
    year_of_study: str = "1st Year"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    college_name: str
    program: str
    year_of_study: str
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
            session = None
            
            # Debug: Log the actual response
            print(f"[DEBUG] Supabase signup response type: {type(response)}")
            print(f"[DEBUG] Supabase response dir: {[x for x in dir(response) if not x.startswith('_')]}")
            
            # Try different response formats
            # The response is gotrue.types.AuthResponse with .user and .session directly
            if hasattr(response, "user"):
                user_data = response.user
            elif hasattr(response, "data") and hasattr(response.data, "user"):
                user_data = response.data.user
            
            # Also try if response itself is the user object (some Supabase versions)
            if not user_data and hasattr(response, "id"):
                user_data = response
                
            # Get session if present
            if hasattr(response, "session"):
                session = response.session
            elif hasattr(response, "data") and hasattr(response.data, "session"):
                session = response.data.session

            if not user_data:
                print(f"[DEBUG] Full response: {response}")
                raise Exception("Unexpected response format from Supabase during signup")

            # Determine id and email safely
            if hasattr(user_data, "id"):
                user_id = getattr(user_data, "id")
                user_email = getattr(user_data, "email", None)
            elif isinstance(user_data, dict):
                user_id = user_data.get("id") or (user_data.get("user", {}) or {}).get("id")
                user_email = user_data.get("email") or (user_data.get("user", {}) or {}).get("email")
            else:
                print(f"[DEBUG] user_data type: {type(user_data)}")
                print(f"[DEBUG] user_data: {user_data}")
                raise Exception("Unexpected user data format from Supabase")

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

            try:
                response = supabase.auth.sign_in_with_password({
                    "email": req.email,
                    "password": req.password,
                })
            except Exception as auth_error:
                # Supabase library throws on auth failure
                error_msg = str(auth_error)
                if "Invalid login credentials" in error_msg or "401" in error_msg:
                    raise HTTPException(status_code=401, detail="Invalid email or password")
                elif "Email not confirmed" in error_msg:
                    raise HTTPException(status_code=401, detail="Please confirm your email address")
                else:
                    raise HTTPException(status_code=401, detail=f"Login failed: {error_msg}")

            # AuthResponse has .session and .user directly
            print(f"[DEBUG] Login response type: {type(response)}")
            print(f"[DEBUG] Login response user: {response.user}")
            print(f"[DEBUG] Login response session: {response.session}")
            
            user = None
            session = None
            
            if hasattr(response, "user"):
                user = response.user
            elif hasattr(response, "data") and hasattr(response.data, "user"):
                user = response.data.user
                
            if hasattr(response, "session"):
                session = response.session
            elif hasattr(response, "data") and hasattr(response.data, "session"):
                session = response.data.session

            if not session or not user:
                # Could be invalid credentials or email not confirmed
                raise HTTPException(status_code=401, detail="Invalid credentials or email not confirmed")

            metadata = {}
            try:
                # user_metadata is directly on the user object
                if hasattr(user, "user_metadata"):
                    metadata = getattr(user, "user_metadata", {}) or {}
                elif isinstance(user, dict):
                    metadata = user.get("user_metadata", {})
                
                # Fallback: try app_metadata
                if not metadata and hasattr(user, "app_metadata"):
                    metadata = getattr(user, "app_metadata", {}) or {}
                elif not metadata and isinstance(user, dict):
                    metadata = user.get("app_metadata", {})
            except Exception:
                metadata = {}

            # Extract tokens
            access = getattr(session, "access_token", None) or (session.get("access_token") if isinstance(session, dict) else None)
            refresh = getattr(session, "refresh_token", None) or (session.get("refresh_token") if isinstance(session, dict) else None)
            expires = getattr(session, "expires_in", None) or (session.get("expires_in") if isinstance(session, dict) else None)

            return UserResponse(
                id=getattr(user, "id", "") or (user.get("id") if isinstance(user, dict) else ""),
                email=getattr(user, "email", "") or (user.get("email") if isinstance(user, dict) else ""),
                full_name=metadata.get("full_name", "") if isinstance(metadata, dict) else getattr(metadata, "full_name", ""),
                college_name=metadata.get("college_name", "") if isinstance(metadata, dict) else getattr(metadata, "college_name", ""),
                program=metadata.get("program", "BTech") if isinstance(metadata, dict) else getattr(metadata, "program", "BTech"),
                year_of_study=str(metadata.get("year_of_study", "1st Year")) if isinstance(metadata, dict) else str(getattr(metadata, "year_of_study", "1st Year")),
                access_token=access,
                refresh_token=refresh,
                expires_in=expires,
                needs_confirmation=False,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

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


# Dependency for protected routes with lazy user creation
async def get_current_user_from_token(authorization: str = None, db: Session = None):
    """
    Validate JWT with Supabase and ensure user exists in application database.
    If user doesn't exist in local DB, creates them (lazy creation).
    
    Args:
        authorization: Bearer token from Authorization header
        db: Database session (optional, for lazy creation)
    
    Returns:
        dict: User data with all fields from application database
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Extract token
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()
        
        # Get user from Supabase
        supabase_user = await SupabaseFirstAuthService.get_current_user(token)
        
        # If no database session provided, return Supabase user only
        if db is None:
            return supabase_user
        
        # Import models here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.models import User
        
        # Check if user exists in application database
        db_user = db.query(User).filter(User.id == supabase_user["id"]).first()
        
        if not db_user:
            # LAZY CREATION: User exists in Supabase but not in app DB
            logger.info(f"Lazy-creating user {supabase_user['id']} in application database")
            
            db_user = User(
                id=supabase_user["id"],
                email=supabase_user["email"],
                full_name=supabase_user.get("full_name", "Unknown"),
                college_name=supabase_user.get("college_name", "Unknown"),
                password_hash="supabase_managed",  # Password managed by Supabase
                program=supabase_user.get("program", "BTech"),
                year_of_study=supabase_user.get("year_of_study", 1),
                wizard_completed=False
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"User {supabase_user['id']} created successfully in application database")
        
        # Return combined user data from database
        return {
            "id": str(db_user.id),
            "email": db_user.email,
            "full_name": db_user.full_name,
            "college_name": db_user.college_name,
            "program": db_user.program,
            "year_of_study": db_user.year_of_study,
            "wizard_completed": db_user.wizard_completed,
            "exam_name": db_user.exam_name,
            "days_until_exam": db_user.days_until_exam,
            "focus_subjects": db_user.focus_subjects or [],
            "study_hours_per_day": db_user.study_hours_per_day,
            "target_score": db_user.target_score,
            "preparation_level": db_user.preparation_level,
            "exam_date": db_user.exam_date,
            "supabase_user": supabase_user  # Include original Supabase data if needed
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=401, 
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )
