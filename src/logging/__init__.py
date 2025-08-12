"""
Logging Module
Centralized logging configuration for the entire application
"""

from .logger import Logger
from .logging_service import LoggingService

# Don't initialize during import to avoid circular imports
# The logger will be initialized when first accessed

__all__ = [
    'Logger',
    'LoggingService'
] 