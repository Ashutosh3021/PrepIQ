"""
Supabase-first authentication approach for PrepIQ
This replaces local database auth with Supabase as the primary auth system
"""

import os
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

# Supabase setup (lazy initialization)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Supabase credentials are required for this auth approach")

# Initialize client lazily
_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        print("Creating Supabase client...")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client created successfully")
    return _supabase_client

# JWT configuration for local tokens (optional, Supabase handles auth)
SECRET_KEY = os.getenv("JWT_SECRET", "fallback-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

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
    access_token: str  # Supabase JWT token
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class SupabaseFirstAuthService:
    @staticmethod
    async def signup(req: SignupRequest):
        """Create user directly in Supabase (no local database)"""
        try:
            print(f"📝 Creating user in Supabase: {req.email}")
            
            supabase = get_supabase_client()
            
            # First, sign up the user normally
            response = supabase.auth.sign_up({
                "email": req.email,
                "password": req.password,
                "options": {
                    "data": {
                        "full_name": req.full_name,
                        "college_name": req.college_name,
                        "program": req.program,
                        "year_of_study": req.year_of_study
                    }
                }
            })
            
            print(f"Supabase create_user response type: {type(response)}")
            print(f"Supabase sign_up response attributes: {dir(response) if hasattr(response, '__dict__') else 'No __dict__'}")
            
            # Handle different response formats from Supabase client
            if hasattr(response, 'data') and 'user' in response.data:
                user_data = response.data['user']
                print(f"Using response.data['user'] path")
            elif hasattr(response, 'user'):
                user_data = response.user
                print(f"Using response.user path")
            elif hasattr(response, 'data') and hasattr(response.data, 'user'):
                user_data = response.data.user
                print(f"Using response.data.user path")
            else:
                print(f"Response structure: {response}")
                raise Exception("Unexpected response format from Supabase")
            
            print(f"User data type: {type(user_data)}")
            print(f"User data attributes: {dir(user_data) if hasattr(user_data, '__dict__') else 'No __dict__'}")
            
            # Access user attributes correctly based on type
            if hasattr(user_data, 'id'):
                user_id = user_data.id
                user_email = user_data.email
            elif isinstance(user_data, dict):
                user_id = user_data.get('id') or (user_data.get('user', {}).get('id') if 'user' in user_data else None)
                user_email = user_data.get('email') or (user_data.get('user', {}).get('email') if 'user' in user_data else None)
                # If user is in a nested user object
                if not user_id and 'user' in user_data:
                    nested_user = user_data['user']
                    user_id = nested_user.get('id')
                    user_email = nested_user.get('email')
            else:
                print(f"User data structure: {user_data}")
                raise Exception("Unexpected user data format")
            
            # Check if user needs confirmation
            if hasattr(user_data, 'email_confirmed_at') and not user_data.email_confirmed_at:
                print("⚠️ User needs email confirmation")
            elif isinstance(user_data, dict) and not user_data.get('email_confirmed_at'):
                print("⚠️ User needs email confirmation")
            
            print(f"✅ User created in Supabase: {user_id}")
            
            # For new signups, the session might already be available in the response
            if hasattr(response, 'data') and 'session' in response.data:
                session = response.data['session']
                print(f"Session found in signup response")
            elif hasattr(response, 'session'):
                session = response.session
                print(f"Session found in signup response")
            else:
                # If no session in signup response, sign in manually
                print("Signing in user after signup...")
                sign_in_response = supabase.auth.sign_in_with_password({
                    "email": req.email,
                    "password": req.password
                })
                
                # Handle sign-in response
                if hasattr(sign_in_response, 'data') and 'session' in sign_in_response.data:
                    session = sign_in_response.data['session']
                    print(f"Using sign_in_response.data['session'] path")
                elif hasattr(sign_in_response, 'session'):
                    session = sign_in_response.session
                    print(f"Using sign_in_response.session path")
                else:
                    print(f"Sign-in response structure: {sign_in_response}")
                    raise Exception("Unexpected sign-in response format from Supabase")
            
            # Access session attributes correctly
            if hasattr(session, 'access_token'):
                access_token = session.access_token
                refresh_token = session.refresh_token
                expires_in = session.expires_in
            elif isinstance(session, dict):
                access_token = session.get('access_token')
                refresh_token = session.get('refresh_token')
                expires_in = session.get('expires_in', 3600)  # Default to 1 hour
            else:
                print(f"Session structure: {session}")
                raise Exception("Unexpected session format")
            
            user_response = UserResponse(
                id=user_id,
                email=user_email,
                full_name=req.full_name,
                college_name=req.college_name,
                program=req.program,
                year_of_study=req.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=expires_in
            )
            
            print(f"Created UserResponse object: {type(user_response)}")
            print(f"UserResponse attributes: {dir(user_response)}")
            
            return user_response
            
        except Exception as e:
            print(f"❌ Supabase signup failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=400,
                detail=f"Signup failed: {str(e)}"
            )

    @staticmethod
    async def login(req: LoginRequest):
        """Authenticate user with Supabase"""
        try:
            print(f"🔑 Authenticating user: {req.email}")
            
            supabase = get_supabase_client()
            
            # Authenticate with Supabase
            response = supabase.auth.sign_in_with_password({
                "email": req.email,
                "password": req.password
            })
            
            # Handle different response formats
            if hasattr(response, 'data') and 'session' in response.data:
                session = response.data['session']
                user = response.data['user']
            elif hasattr(response, 'session') and hasattr(response, 'user'):
                session = response.session
                user = response.user
            else:
                raise Exception("Unexpected response format from Supabase")
            
            # Get user metadata
            metadata = user.get('user_metadata', {})
            
            print(f"✅ User authenticated: {user['id']}")
            
            return UserResponse(
                id=user['id'],
                email=user['email'],
                full_name=metadata.get('full_name', ''),
                college_name=metadata.get('college_name', ''),
                program=metadata.get('program', ''),
                year_of_study=metadata.get('year_of_study', 1),
                access_token=session['access_token'],
                refresh_token=session['refresh_token'],
                token_type="bearer",
                expires_in=session['expires_in']
            )
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

    @staticmethod
    async def get_current_user(token: str):
        """Verify Supabase JWT token and get user info"""
        try:
            supabase = get_supabase_client()
            
            # Verify the Supabase token
            user_response = supabase.auth.get_user(token)
            
            # Handle different response formats
            if hasattr(user_response, 'data') and 'user' in user_response.data:
                user = user_response.data['user']
            elif hasattr(user_response, 'user'):
                user = user_response.user
            else:
                raise Exception("Unexpected user response format from Supabase")
            
            # Get user metadata
            metadata = user.get('user_metadata', {})
            
            return {
                "id": user['id'],
                "email": user['email'],
                "full_name": metadata.get('full_name', ''),
                "college_name": metadata.get('college_name', ''),
                "program": metadata.get('program', ''),
                "year_of_study": metadata.get('year_of_study', 1)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

# Dependency for protected routes
async def get_current_user_from_token(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        token = authorization.split(" ")[1]  # Bearer <token>
        return await SupabaseFirstAuthService.get_current_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")