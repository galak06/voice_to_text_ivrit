#!/usr/bin/env python3
"""
Logging Service
Handles application-specific logging utilities and events
"""

import logging
from typing import Optional
from .logger import Logger


class LoggingService:
    """Service for application-specific logging utilities"""
    
    def __init__(self):
        """Initialize logging service with singleton logger"""
        self._logger = Logger()
    
    def log_transcription_start(self, audio_file: str, model: str, engine: str):
        """Log transcription start event"""
        logger = self._logger.get_logger('transcription')
        logger.info(f"Starting transcription: {audio_file} with {model} ({engine})")
    
    def log_transcription_complete(self, audio_file: str, model: str, engine: str, success: bool):
        """Log transcription completion event"""
        logger = self._logger.get_logger('transcription')
        status = "completed successfully" if success else "failed"
        logger.info(f"Transcription {status}: {audio_file} with {model} ({engine})")
    
    def log_file_save(self, file_path: str, file_type: str, success: bool):
        """Log file save operation"""
        logger = self._logger.get_logger('file_operations')
        status = "saved" if success else "failed to save"
        logger.info(f"{file_type.upper()} file {status}: {file_path}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        logger = self._logger.get_logger('errors')
        error_msg = f"Error in {context}: {str(error)}" if context else str(error)
        logger.error(error_msg)
    
    def log_application_start(self, app_name: str = "Transcription Application"):
        """Log application start"""
        logger = self._logger.get_logger('application')
        logger.info(f"🚀 {app_name} Started")
    
    def log_application_shutdown(self, app_name: str = "Transcription Application"):
        """Log application shutdown"""
        logger = self._logger.get_logger('application')
        logger.info(f"🛑 {app_name} Shutdown")
    
    def log_configuration_loaded(self, config_file: str):
        """Log configuration file loaded"""
        logger = self._logger.get_logger('configuration')
        logger.info(f"Configuration loaded from: {config_file}")
    
    def log_model_loaded(self, model_name: str, engine: str):
        """Log model loading"""
        logger = self._logger.get_logger('models')
        logger.info(f"Model loaded: {model_name} ({engine})")
    
    def log_processing_start(self, file_count: int, batch_mode: bool = False):
        """Log processing start"""
        logger = self._logger.get_logger('processing')
        mode = "batch" if batch_mode else "single"
        logger.info(f"Starting {mode} processing of {file_count} file(s)")
    
    def log_processing_complete(self, success_count: int, total_count: int, batch_mode: bool = False):
        """Log processing completion"""
        logger = self._logger.get_logger('processing')
        mode = "batch" if batch_mode else "single"
        logger.info(f"{mode.capitalize()} processing completed: {success_count}/{total_count} successful") 