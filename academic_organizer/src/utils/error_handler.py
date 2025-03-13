"""Centralized error handling and logging system."""
from typing import Type, Optional, Any
from functools import wraps
import logging
import traceback
from pathlib import Path

class ApplicationError(Exception):
    """Base exception class for application errors."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class DatabaseError(ApplicationError):
    """Database-related errors."""
    pass

class ValidationError(ApplicationError):
    """Data validation errors."""
    pass

class ConfigurationError(ApplicationError):
    """Configuration-related errors."""
    pass

def setup_logging(log_path: Path) -> logging.Logger:
    """Configure application-wide logging."""
    logger = logging.getLogger('academic_organizer')
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_path / 'app.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def handle_errors(error_type: Type[Exception] = Exception):
    """Decorator for consistent error handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                logger = logging.getLogger('academic_organizer')
                logger.error(
                    f"Error in {func.__name__}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                raise ApplicationError(
                    f"Operation failed: {str(e)}",
                    error_code=type(e).__name__
                )
        return wrapper
    return decorator