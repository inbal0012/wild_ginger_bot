"""
Base service class for all services in the Wild Ginger Event Management System.
Provides common functionality and interface for all services.
"""

from typing import Any, Dict, Optional
import logging
import os
from logging.handlers import RotatingFileHandler


class BaseService:
    """Base class for all services in the system."""
    
    _logger_configured = False
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the base service with optional logger."""
        if not BaseService._logger_configured:
            BaseService._configure_logging()
            
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @classmethod
    def _configure_logging(cls):
        """Configure logging for the entire application."""
        if cls._logger_configured:
            return
            
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Create rotating file handler (max 10MB per file, keep 5 backup files)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'wild_ginger_bot.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )

        # Create console handler
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Get the root logger and configure it
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        cls._logger_configured = True
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        pass
    
    async def shutdown(self) -> None:
        """Clean up resources when shutting down the service."""
        pass
    
    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message with optional context."""
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log an error message with optional context."""
        self.logger.error(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message with optional context."""
        self.logger.warning(message, extra=kwargs) 