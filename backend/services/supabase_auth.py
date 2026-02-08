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
import asyncio
from contextlib import asynccontextmanager

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

# Connection pool and retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

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
    async def _execute_with_retry(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
        """Execute a function with retry mechanism"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
        
        raise last_exception

    @staticmethod
    def _safe_supabase_operation(operation_func, *args, **kwargs):
        """Execute Supabase operation with enhanced error handling"""
        if not supabase:
            return None, "Supabase not configured"
        
        try:
            result = operation_func(*args, **kwargs)
            return result, None
        except Exception as e:
            error_msg = f"Supabase operation failed: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    @staticmethod
    async def signup(req: SignupRequest, db: Session):
        """Create a new user account with robust Supabase integration and fallback to local database"""
        logger.info(f"Attempting signup for: {req.email}")
        print(f"📝 Signup attempt for: {req.email}")
            
        try:
            # First try to create user in Supabase (primary method)
            supabase_success = False
            supabase_user_id = None
            supabase_error = None
                
            if supabase:
                try:
                    logger.info(f"Attempting to create user in Supabase: {req.email}")
                    print(f"🔄 Attempting Supabase user creation for: {req.email}")
                        
                    # Use admin.create_user() with retry mechanism
                    def create_supabase_user():
                        return supabase.auth.admin.create_user({
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
                        
                    supabase_response, error = await SupabaseAuthService._execute_with_retry(
                        SupabaseAuthService._safe_supabase_operation,
                        create_supabase_user,
                        max_retries=3
                    )
                        
                    if error:
                        supabase_error = error
                        logger.warning(f"Supabase user creation failed: {error}")
                    else:
                        supabase_user_id = supabase_response.data['user']['id']
                        logger.info(f"✅ Supabase user created successfully: {supabase_user_id}")
                        print(f"✅ Supabase user created successfully: {supabase_user_id}")
                        supabase_success = True
                            
                except Exception as e:
                    supabase_error = str(e)
                    logger.error(f"❌ Failed to create user in Supabase: {e}")
                    print(f"❌ Supabase user creation failed: {e}")
            else:
                logger.warning("⚠️  Supabase client not available")
                print("⚠️  Supabase not configured - proceeding with local database only")
                
            # Create user in local database (always)
            existing_user = db.query(models.User).filter(models.User.email == req.email).first()
            if existing_user:
                logger.warning(f"User already exists locally: {req.email}")
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
                
            # Hash password
            hashed_password = SupabaseAuthService.hash_password(req.password)
                
            # Create user in local database
            user = models.User(
                id=supabase_user_id or str(uuid.uuid4()),  # Use Supabase ID if available, otherwise generate new
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
        """Authenticate user with robust Supabase integration and local database fallback"""
        logger.info(f"Attempting login for: {req.email}")
        print(f"🔑 Login attempt for: {req.email}")
            
        try:
            # Try Supabase authentication first (primary method)
            supabase_success = False
            supabase_error = None
            supabase_user_data = None
                
            if supabase:
                try:
                    logger.info(f"Attempting to authenticate with Supabase: {req.email}")
                    print(f"🔄 Attempting Supabase authentication for: {req.email}")
                        
                    def authenticate_supabase_user():
                        return supabase.auth.sign_in_with_password({
                            "email": req.email,
                            "password": req.password
                        })
                        
                    supabase_response, error = await SupabaseAuthService._execute_with_retry(
                        SupabaseAuthService._safe_supabase_operation,
                        authenticate_supabase_user,
                        max_retries=3
                    )
                        
                    if error:
                        supabase_error = error
                        logger.warning(f"Supabase authentication failed: {error}")
                    else:
                        supabase_user_data = supabase_response.data.get('user', {})
                        logger.info(f"✅ Supabase authentication successful: {supabase_user_data.get('id')}")
                        print(f"✅ Supabase authentication successful")
                        supabase_success = True
                            
                except Exception as e:
                    supabase_error = str(e)
                    logger.error(f"❌ Failed to authenticate with Supabase: {e}")
                    print(f"❌ Supabase authentication failed: {e}")
                
            # Try to find user in local database
            user = db.query(models.User).filter(models.User.email == req.email).first()
            if not user:
                logger.warning(f"User not found locally: {req.email}")
                # If user exists in Supabase but not locally, create local record
                if supabase_success and supabase_user_data:
                    try:
                        # Create local user record from Supabase data
                        user = models.User(
                            id=supabase_user_data.get('id'),
                            email=req.email,
                            password_hash=SupabaseAuthService.hash_password(req.password),  # Hash the provided password
                            full_name=supabase_user_data.get('user_metadata', {}).get('full_name', ''),
                            college_name=supabase_user_data.get('user_metadata', {}).get('college_name', ''),
                            program=supabase_user_data.get('user_metadata', {}).get('program', 'BTech'),
                            year_of_study=supabase_user_data.get('user_metadata', {}).get('year_of_study', 1)
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        logger.info(f"✅ Local user record created from Supabase data: {user.id}")
                        print(f"✅ Local user record synchronized from Supabase")
                    except Exception as e:
                        logger.error(f"Failed to create local user from Supabase data: {e}")
                        raise HTTPException(
                            status_code=401,
                            detail="Invalid email or password"
                        )
                else:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid email or password"
                    )
                
            # Verify password for local database user
            if not SupabaseAuthService.verify_password(req.password, user.password_hash):
                logger.warning(f"Password verification failed for: {req.email}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
                
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
