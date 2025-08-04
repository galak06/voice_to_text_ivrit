"""
Logging Module
Centralized logging configuration for the entire application
"""

from .logger import Logger
from .logging_service import LoggingService

# Create singleton instance and initialize global logging
_logger_instance = Logger()
_logger_instance.initialize()

__all__ = [
    'Logger',
    'LoggingService'
] 