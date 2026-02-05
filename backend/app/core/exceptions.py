from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class PrepIQException(Exception):
    """Base exception class for PrepIQ application."""
    
    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(PrepIQException):
    """Exception raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, error_code="AUTH_ERROR")


class AuthorizationError(PrepIQException):
    """Exception raised for authorization failures."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, error_code="AUTHZ_ERROR")


class ValidationError(PrepIQException):
    """Exception raised for data validation errors."""
    
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        self.details = details
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, error_code="VALIDATION_ERROR")


class NotFoundError(PrepIQException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str = "Resource"):
        message = f"{resource} not found"
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, error_code="NOT_FOUND")


class DatabaseError(PrepIQException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_code="DB_ERROR")


class MLModelError(PrepIQException):
    """Exception raised for machine learning model errors."""
    
    def __init__(self, message: str = "ML model error"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_code="ML_ERROR")


class FileProcessingError(PrepIQException):
    """Exception raised for file processing errors."""
    
    def __init__(self, message: str = "File processing error"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, error_code="FILE_ERROR")


class RateLimitError(PrepIQException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=status.HTTP_429_TOO_MANY_REQUESTS, error_code="RATE_LIMIT")


class ExternalServiceError(PrepIQException):
    """Exception raised for external service failures."""
    
    def __init__(self, service: str = "External service", message: str = "Service unavailable"):
        full_message = f"{service}: {message}"
        super().__init__(full_message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, error_code="EXTERNAL_SERVICE_ERROR")


# Exception handlers for FastAPI
async def prep_iq_exception_handler(request, exc: PrepIQException):
    """Global exception handler for PrepIQ exceptions."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.message,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request, exc):
    """Handler for Pydantic validation errors."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "Validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )


async def http_exception_handler(request, exc: HTTPException):
    """Handler for HTTP exceptions."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# Utility functions
def raise_not_found(resource: str = "Resource"):
    """Raise a NotFoundError with the specified resource."""
    raise NotFoundError(resource)


def raise_validation_error(message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
    """Raise a ValidationError with the specified message and details."""
    raise ValidationError(message, details)


def raise_authentication_error(message: str = "Authentication failed"):
    """Raise an AuthenticationError with the specified message."""
    raise AuthenticationError(message)


def raise_authorization_error(message: str = "Access denied"):
    """Raise an AuthorizationError with the specified message."""
    raise AuthorizationError(message)


def raise_database_error(message: str = "Database error"):
    """Raise a DatabaseError with the specified message."""
    raise DatabaseError(message)


def raise_ml_model_error(message: str = "ML model error"):
    """Raise an MLModelError with the specified message."""
    raise MLModelError(message)


def raise_file_processing_error(message: str = "File processing error"):
    """Raise a FileProcessingError with the specified message."""
    raise FileProcessingError(message)


def raise_rate_limit_error(message: str = "Rate limit exceeded"):
    """Raise a RateLimitError with the specified message."""
    raise RateLimitError(message)