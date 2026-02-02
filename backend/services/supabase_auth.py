from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr
import os
import uuid
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app import models
from typing import Optional

# Supabase client import with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b", bcrypt__rounds=12)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable must be set")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
REFRESH_TOKEN_EXPIRE_MINUTES = 43200  # 30 days

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Initialize Supabase client with error handling
supabase = None
if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        # Test the connection
        supabase.auth.get_user()  # This will test if the connection works
    except Exception as e:
        print(f"Warning: Could not connect to Supabase: {e}")
        print("Falling back to local database only mode")
        supabase = None
else:
    print("Supabase not configured - using local database only")
    supabase = None

# Models
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
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class SupabaseAuthService:
    @staticmethod
    async def signup(req: SignupRequest, db: Session):
        """Create a new user account with fallback to local database"""
        try:
            # First try to create user in local database
            existing_user = db.query(models.User).filter(models.User.email == req.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
            
            # Hash password
            hashed_password = SupabaseAuthService.hash_password(req.password)
            
            # Create user in local database
            user = models.User(
                id=str(uuid.uuid4()),
                email=req.email,
                password_hash=hashed_password,
                full_name=req.full_name,
                college_name=req.college_name,
                program=req.program,
                year_of_study=req.year_of_study
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Try to create user in Supabase if available
            if supabase:
                try:
                    supabase_response = supabase.auth.sign_up({
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
                    print(f"Supabase user created: {supabase_response}")
                except Exception as e:
                    print(f"Warning: Failed to create user in Supabase: {e}")
                    # Continue with local database user
            
            # Generate tokens
            access_token = SupabaseAuthService.create_access_token(data={"sub": user.id})
            refresh_token = SupabaseAuthService.create_refresh_token(data={"sub": user.id})
            
            return UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                college_name=user.college_name,
                program=user.program,
                year_of_study=user.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating user: {str(e)}"
            )

    @staticmethod
    async def login(req: LoginRequest, db: Session):
        """Authenticate user with fallback to local database"""
        try:
            # Try to find user in local database
            user = db.query(models.User).filter(models.User.email == req.email).first()
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not SupabaseAuthService.verify_password(req.password, user.password_hash):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            # Try to authenticate with Supabase if available
            if supabase:
                try:
                    supabase_response = supabase.auth.sign_in_with_password({
                        "email": req.email,
                        "password": req.password
                    })
                    print(f"Supabase authentication successful: {supabase_response}")
                except Exception as e:
                    print(f"Warning: Failed to authenticate with Supabase: {e}")
                    # Continue with local database authentication
            
            # Generate tokens
            access_token = SupabaseAuthService.create_access_token(data={"sub": user.id})
            refresh_token = SupabaseAuthService.create_refresh_token(data={"sub": user.id})
            
            return UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                college_name=user.college_name,
                program=user.program,
                year_of_study=user.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error during login: {str(e)}"
            )

    @staticmethod
    async def logout(token: str):
        """Logout user"""
        if supabase:
            try:
                supabase.auth.sign_out()
            except Exception as e:
                print(f"Warning: Failed to logout from Supabase: {e}")
        
        return {"message": "Successfully logged out"}

    @staticmethod
    async def get_current_user(token: str, db: Session):
        """Get current user from token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return user
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with fallback mechanism"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            print(f"Password hashing error: {e}")
            # Fallback to simple hash if bcrypt fails
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password with fallback mechanism"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            print(f"Password verification error: {e}")
            # Fallback to simple comparison if bcrypt fails
            import hashlib
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    @staticmethod
    def create_access_token(data: dict):
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict):
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt