#!/usr/bin/env python3
"""
Logger
Centralized logging configuration for the entire application
"""

import sys
import threading
from typing import Optional
from pathlib import Path


class Logger:
    """Global logging manager for the entire application (Thread-Safe Singleton)"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _loggers = {}
    
    def __new__(cls):
        """Ensure only one instance of Logger exists (Thread-Safe Singleton pattern)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the singleton instance only once"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialized = True
                    self._loggers = {}
    
    @classmethod
    def get_instance(cls) -> 'Logger':
        """Get the singleton instance of Logger"""
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    def initialize(self, 
                   log_level: int = None,
                   log_file: Optional[str] = None,
                   log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
        """Initialize global logging configuration"""
        if hasattr(self, '_logging_initialized') and self._logging_initialized:
            return
        
        # Import logging here to avoid circular import
        import logging
        
        # Set default log level if not provided
        if log_level is None:
            log_level = logging.INFO
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Create file handler if log file specified
        file_handler = None
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        root_logger.addHandler(console_handler)
        if file_handler:
            root_logger.addHandler(file_handler)
        
        # Configure src logger
        src_logger = logging.getLogger('src')
        src_logger.setLevel(log_level)
        
        self._logging_initialized = True
    
    def get_logger(self, name: str):
        """Get a logger instance for the given name"""
        if not hasattr(self, '_logging_initialized') or not self._logging_initialized:
            self.initialize()
        
        if name not in self._loggers:
            import logging
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def set_level(self, level: int):
        """Set logging level for all loggers"""
        if not hasattr(self, '_logging_initialized') or not self._logging_initialized:
            self.initialize()
        
        import logging
        for logger in self._loggers.values():
            logger.setLevel(level) 