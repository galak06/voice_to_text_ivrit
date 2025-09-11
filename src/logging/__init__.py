"""
Logging Module
Centralized logging configuration for the entire application
"""

from .logger import Logger
from .logging_service import LoggingService

# Create singleton instance
_logger_instance = Logger()

def initialize_logging_with_config(config_manager=None):
    """Initialize logging with ConfigManager if available"""
    if config_manager and hasattr(config_manager, 'config') and config_manager.config.output:
        # Use ConfigManager to get log paths
        import os
        logs_dir = config_manager.config.output.logs_dir
        log_file_name = config_manager.config.output.log_file
        log_file_path = os.path.join(logs_dir, log_file_name)
        
        # Ensure log directory exists
        from pathlib import Path
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Get log level from config
        import logging
        log_level = getattr(logging, config_manager.config.output.log_level.upper(), logging.INFO)
        
        _logger_instance.initialize(
            log_level=log_level,
            log_file=log_file_path
        )
    else:
        # Fallback initialization without ConfigManager
        _initialize_default_logging()

def _initialize_default_logging():
    """Fallback initialization without ConfigManager"""
    from pathlib import Path
    import os
    try:
        from definition import LOGS_DIR
        default_log_file = os.path.join(LOGS_DIR, "transcription.log")
    except ImportError:
        default_log_file = "output/logs/transcription.log"
        
    Path(default_log_file).parent.mkdir(parents=True, exist_ok=True)
    _logger_instance.initialize(log_file=default_log_file)

# Initialize with default logging for immediate availability
# This will be overridden when ConfigManager is available
_initialize_default_logging()

__all__ = [
    'Logger',
    'LoggingService',
    'initialize_logging_with_config'
] 