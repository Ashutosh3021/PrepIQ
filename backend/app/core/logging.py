import logging
import sys
from typing import Optional
from pathlib import Path
from .config import settings


def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None):
    """Set up structured logging for the application."""
    
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    if log_file is None:
        log_file = settings.LOG_FILE
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Set up handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        format=log_format,
        datefmt=date_format
    )
    
    # Suppress some noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Create default logger
logger = setup_logging()


class StructuredLogger:
    """Structured logger for consistent log formatting."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        if kwargs:
            self.logger.info(f"{message} | {self._format_kwargs(kwargs)}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        if kwargs:
            self.logger.warning(f"{message} | {self._format_kwargs(kwargs)}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        if kwargs:
            self.logger.error(f"{message} | {self._format_kwargs(kwargs)}")
        else:
            self.logger.error(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        if kwargs:
            self.logger.debug(f"{message} | {self._format_kwargs(kwargs)}")
        else:
            self.logger.debug(message)
    
    def _format_kwargs(self, kwargs: dict) -> str:
        """Format keyword arguments for logging."""
        return " ".join([f"{k}={v}" for k, v in kwargs.items()])


# Convenience function
def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)