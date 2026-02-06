from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets

from .config import settings
from .exceptions import AuthenticationError, AuthorizationError
from ..database import get_db_session
from ..models import User


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db_session)
) -> User:
    """Get the current authenticated user from the token."""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Invalid authentication credentials")
            
        # Get user from database
        user = await db.get(User, user_id)
        if user is None:
            raise AuthenticationError("User not found")
            
        return user
        
    except Exception as e:
        if isinstance(e, AuthenticationError):
            raise e
        raise AuthenticationError("Could not validate credentials")


def verify_user_role(user: User, required_role: str) -> bool:
    """Verify that a user has the required role."""
    # Implement role-based access control
    # This is a simple implementation - you might want to use a more sophisticated RBAC system
    user_roles = getattr(user, 'roles', [])
    return required_role in user_roles or required_role == "user"  # Default user role


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise AuthorizationError("Inactive user")
    return current_user


async def get_current_user_with_role(required_role: str):
    """Dependency to get current user with role verification."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not verify_user_role(current_user, required_role):
            raise AuthorizationError(f"Insufficient permissions. Required role: {required_role}")
        return current_user
    return role_checker


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class PermissionChecker:
    """Class to check user permissions."""
    
    def __init__(self, required_permissions: list):
        self.required_permissions = required_permissions
    
    async def __call__(self, current_user: User = Depends(get_current_user)) -> bool:
        user_permissions = getattr(current_user, 'permissions', [])
        
        # Check if user has all required permissions
        missing_permissions = set(self.required_permissions) - set(user_permissions)
        if missing_permissions:
            raise AuthorizationError(
                f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return True


# Common permission checkers
admin_required = PermissionChecker(["admin"])
moderator_required = PermissionChecker(["admin", "moderator"])
editor_required = PermissionChecker(["admin", "moderator", "editor"])


def create_password_reset_token(email: str) -> str:
    """Create a password reset token."""
    delta = timedelta(hours=1)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now.timestamp(), "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email."""
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def rate_limit_key_func(request) -> str:
    """Generate a key for rate limiting based on user or IP."""
    # Try to get user ID from token
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
    except:
        pass
    
    # Fallback to IP address
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"