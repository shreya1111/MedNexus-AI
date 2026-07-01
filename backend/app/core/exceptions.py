"""
Custom exceptions for MedNexus-AI backend.

Defines application-specific exceptions with appropriate status codes.
"""

from typing import Any, Optional


class MedNexusException(Exception):
    """Base exception for MedNexus-AI."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(MedNexusException):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(MedNexusException):
    """Authorization failed - insufficient permissions."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Any] = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(MedNexusException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(MedNexusException):
    """Validation error."""
    
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(message, status_code=422, details=details)


class ConflictError(MedNexusException):
    """Resource conflict."""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(message, status_code=409, details=details)


class RateLimitError(MedNexusException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(message, status_code=429, details=details)


class ServiceError(MedNexusException):
    """Internal service error."""
    
    def __init__(self, message: str = "Internal service error", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class ExternalServiceError(MedNexusException):
    """External service error (AI, Database, etc.)."""
    
    def __init__(self, message: str = "External service error", details: Optional[Any] = None):
        super().__init__(message, status_code=503, details=details)
