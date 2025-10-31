from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
import uuid


def install_error_handlers(app):
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        trace_id = str(uuid.uuid4())
        logger.error(f"[{trace_id}] {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "detail": "Something went wrong",
                "trace_id": trace_id,
            },
        )

    return app

"""
Typed error hierarchy for RAGGITY ZYZTEM.

Provides structured exceptions for better error handling,
logging, and user feedback.
"""


class RaggityError(Exception):
    """Base exception for all RAGGITY errors"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self):
        """Convert error to dictionary for JSON serialization"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class UserError(RaggityError):
    """
    User-provided invalid input.
    
    HTTP: 400 Bad Request
    Action: Return clear error message to user
    """
    pass


class NotFoundError(RaggityError):
    """
    Requested resource not found.
    
    HTTP: 404 Not Found
    Action: Inform user resource doesn't exist
    """
    pass


class ProviderError(RaggityError):
    """
    External provider (LLM, API) error.
    
    HTTP: 502 Bad Gateway
    Action: Log error, inform user of service issue
    """
    pass


class TransientError(RaggityError):
    """
    Temporary failure that may succeed on retry.
    
    Examples: Network timeout, rate limit, temporary unavailability
    HTTP: 503 Service Unavailable
    Action: Retry with exponential backoff
    """
    pass


class FatalError(RaggityError):
    """
    Unrecoverable error requiring intervention.
    
    Examples: Missing config, corrupted data, dependency not installed
    HTTP: 500 Internal Server Error
    Action: Log full traceback, alert admin
    """
    pass


class ConfigError(FatalError):
    """Configuration error (missing API keys, invalid settings)"""
    pass


class ValidationError(UserError):
    """Input validation failed"""
    pass


class TimeoutError(TransientError):
    """Operation timed out"""
    pass


class RateLimitError(TransientError):
    """Rate limit exceeded"""
    pass


def http_status_for_error(error: Exception) -> int:
    """
    Map exception to appropriate HTTP status code.
    
    Args:
        error: Exception instance
    
    Returns:
        HTTP status code
    """
    if isinstance(error, UserError):
        return 400
    elif isinstance(error, NotFoundError):
        return 404
    elif isinstance(error, ProviderError):
        return 502
    elif isinstance(error, TransientError):
        return 503
    elif isinstance(error, FatalError):
        return 500
    else:
        return 500  # Default to internal server error


def user_friendly_message(error: Exception) -> str:
    """
    Convert technical error to user-friendly message.
    
    Args:
        error: Exception instance
    
    Returns:
        User-friendly error message
    """
    if isinstance(error, UserError):
        return str(error)
    elif isinstance(error, NotFoundError):
        return f"Resource not found: {error}"
    elif isinstance(error, ProviderError):
        return "External service is currently unavailable. Please try again later."
    elif isinstance(error, TransientError):
        return "Service temporarily unavailable. Please retry in a moment."
    elif isinstance(error, FatalError):
        return "A system error occurred. Please contact support if this persists."
    else:
        return "An unexpected error occurred. Please try again."

