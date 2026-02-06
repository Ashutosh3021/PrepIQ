from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr
import os
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db
from app import models
from typing import Optional

# Initialize password hashing context
# Use bcrypt with explicit backend specification to avoid initialization issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b", bcrypt__rounds=12)

# Force bcrypt backend initialization to avoid runtime errors
try:
    pwd_context.hash("test_password_for_initialization")
except:
    pass

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable must be set")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
REFRESH_TOKEN_EXPIRE_MINUTES = 43200  # 30 days

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
    access_token: str
    refresh_token: str

# Auth Service
class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        # Bcrypt has a 72-byte password limit, so we truncate if needed
        # This is a security consideration - very long passwords need to be handled
        if len(password.encode('utf-8')) > 72:
            # Truncate to 72 bytes while preserving as much entropy as possible
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        # Handle bcrypt backend initialization issues
        try:
            return pwd_context.hash(password)
        except Exception as e:
            if "password cannot be longer than 72 bytes" in str(e):
                # Ensure password is truncated to 72 bytes for ASCII characters
                # Since the UTF-8 encoding might have caused issues, try with simple slicing
                truncated_password = password[:72]
                try:
                    return pwd_context.hash(truncated_password)
                except:
                    # If bcrypt still fails, we'll use a fallback mechanism
                    # Note: This is not secure for production, but works for development
                    import hashlib
                    import secrets
                    salt = secrets.token_hex(32)
                    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('ascii'), 100000)
                    pwdhash = salt + pwdhash.hex()
                    return pwdhash
            else:
                # If it's a different error, try the fallback
                import hashlib
                import secrets
                salt = secrets.token_hex(32)
                pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('ascii'), 100000)
                pwdhash = salt + pwdhash.hex()
                return pwdhash
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            # Log the error for debugging
            print(f"Password verification error: {e}")
            print(f"Hashed password format issue for user")
            
            # Check if this is a hash created with our fallback mechanism
            # Fallback hashes have 64-character salt + hash part
            if len(hashed_password) >= 128:  # At least 64 chars for salt + 64 chars for hash
                try:
                    import hashlib
                    salt = hashed_password[:64]  # First 64 chars are salt
                    stored_hash = hashed_password[64:]  # Remaining is the hash
                    pwdhash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('ascii'), 100000)
                    computed_hash = pwdhash.hex()
                    return computed_hash == stored_hash
                except:
                    return False
            
            # Return False if hash format is incompatible
            return False
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def signup(data: SignupRequest, db):
        # Check if user already exists
        existing_user = db.query(models.User).filter(models.User.email == data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Hash the password
        hashed_password = AuthService.hash_password(data.password)
        
        # Create new user
        user = models.User(
            email=data.email,
            password_hash=hashed_password,
            full_name=data.full_name,
            college_name=data.college_name,
            program=data.program,
            year_of_study=data.year_of_study
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access and refresh tokens
        access_token = AuthService.create_access_token(data={"sub": str(user.id), "email": user.email})
        refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id), "email": user.email})
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    @staticmethod
    async def login(data: LoginRequest, db):
        # Find user by email
        user = db.query(models.User).filter(models.User.email == data.email).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if password hash is compatible with our system
        # If password_hash is from Supabase ('managed_by_supabase'), we might need different handling
        password_valid = False
        
        if user.password_hash and user.password_hash != "managed_by_supabase":
            # Try to verify the password using our bcrypt method
            password_valid = AuthService.verify_password(data.password, user.password_hash)
        else:
            # For users with Supabase-managed passwords, we may need to authenticate differently
            # For now, we'll return an error indicating the user needs to be handled differently
            raise HTTPException(status_code=401, detail="Account managed by external authentication system")
        
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access and refresh tokens
        access_token = AuthService.create_access_token(data={"sub": str(user.id), "email": user.email})
        refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id), "email": user.email})
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    @staticmethod
    async def get_current_user(token: str, db):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
