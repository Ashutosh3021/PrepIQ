import logging
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Supabase setup
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase client initialized successfully")
    else:
        supabase = None
        logger.warning("⚠️  Supabase credentials not found in environment variables")
        print("⚠️  Supabase credentials not found - users will only be stored locally")
        
except ImportError:
    supabase = None
    logger.warning("⚠️  Supabase library not available")
    print("⚠️  Supabase library not available - users will only be stored locally")
except Exception as e:
    supabase = None
    logger.error(f"❌ Supabase client initialization failed: {e}")
    print(f"❌ Supabase client initialization failed: {e}")

from .. import models

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable must be set")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

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
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=30)  # 30 days
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def signup(req: SignupRequest, db: Session):
        """Create a new user account with fallback to local database"""
        logger.info(f"Attempting signup for: {req.email}")
        print(f"📝 Signup attempt for: {req.email}")
        
        try:
            # First try to create user in local database
            existing_user = db.query(models.User).filter(models.User.email == req.email).first()
            if existing_user:
                logger.warning(f"User already exists: {req.email}")
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
            
            logger.info(f"✅ Local user created: {user.id}")
            print(f"✅ Local user created successfully: {user.email}")
            
            # Try to create user in Supabase if available
            supabase_success = False
            if supabase:
                try:
                    logger.info(f"Attempting to create user in Supabase: {req.email}")
                    print(f"🔄 Attempting Supabase sync for: {req.email}")
                    
                    # Use admin.create_user() instead of sign_up() for service key
                    supabase_response = supabase.auth.admin.create_user({
                        "email": req.email,
                        "password": req.password,
                        "email_confirm": True,  # Skip email confirmation for immediate visibility
                        "user_metadata": {
                            "full_name": req.full_name,
                            "college_name": req.college_name,
                            "program": req.program,
                            "year_of_study": req.year_of_study
                        }
                    })
                    
                    supabase_user_id = supabase_response.data['user']['id']
                    logger.info(f"✅ Supabase user created successfully: {supabase_user_id}")
                    print(f"✅ Supabase user created successfully: {supabase_user_id}")
                    supabase_success = True
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create user in Supabase: {e}")
                    print(f"❌ Supabase sync failed: {e}")
                    print("⚠️  User will only exist in local database")
                    # Don't fail the signup process - local database user is sufficient
            else:
                logger.warning("⚠️  Supabase client not available - user only in local database")
                print("⚠️  Supabase not configured - user only in local database")
            
            # Generate tokens
            access_token = SupabaseAuthService.create_access_token(data={"sub": user.id})
            refresh_token = SupabaseAuthService.create_refresh_token(data={"sub": user.id})
            
            response = UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                college_name=user.college_name,
                program=user.program,
                year_of_study=user.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            logger.info(f"✅ Signup completed for: {req.email} (Supabase: {'Success' if supabase_success else 'Failed'})")
            return response
            
        except Exception as e:
            db.rollback()
            logger.error(f"Signup failed for {req.email}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Signup failed: {str(e)}"
            )

    @staticmethod
    async def login(req: LoginRequest, db: Session):
        """Authenticate user with fallback to local database"""
        logger.info(f"Attempting login for: {req.email}")
        print(f"🔑 Login attempt for: {req.email}")
        
        try:
            # Try to find user in local database
            user = db.query(models.User).filter(models.User.email == req.email).first()
            if not user:
                logger.warning(f"User not found: {req.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not SupabaseAuthService.verify_password(req.password, user.password_hash):
                logger.warning(f"Password verification failed for: {req.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            # Try to authenticate with Supabase if available
            supabase_success = False
            if supabase:
                try:
                    logger.info(f"Attempting to authenticate with Supabase: {req.email}")
                    print(f"🔄 Attempting Supabase authentication for: {req.email}")
                    
                    supabase_response = supabase.auth.sign_in_with_password({
                        "email": req.email,
                        "password": req.password
                    })
                    
                    logger.info(f"✅ Supabase authentication successful: {supabase_response}")
                    print(f"✅ Supabase authentication successful: {supabase_response}")
                    supabase_success = True
                    
                except Exception as e:
                    logger.error(f"❌ Failed to authenticate with Supabase: {e}")
                    print(f"❌ Supabase authentication failed: {e}")
                    print("⚠️  Falling back to local database authentication")
                    # Continue with local database authentication
            
            # Generate tokens
            access_token = SupabaseAuthService.create_access_token(data={"sub": user.id})
            refresh_token = SupabaseAuthService.create_refresh_token(data={"sub": user.id})
            
            response = UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                college_name=user.college_name,
                program=user.program,
                year_of_study=user.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            logger.info(f"✅ Login completed for: {req.email} (Supabase: {'Success' if supabase_success else 'Failed'})")
            return response
            
        except Exception as e:
            logger.error(f"Login failed for {req.email}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Login failed: {str(e)}"
            )

    @staticmethod
    async def logout(token: str):
        """Logout user"""
        if supabase:
            try:
                supabase.auth.sign_out()
            except Exception as e:
                logger.error(f"❌ Failed to logout from Supabase: {e}")
                print(f"❌ Failed to logout from Supabase: {e}")
        
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
