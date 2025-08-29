#!/usr/bin/env python3
"""
Input Validator Service
Provides comprehensive input validation using Pydantic models before processing
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging

from src.models import (
    InputType,
    TranscriptionEngine,
    AudioFileValidation,
    JobInputValidation,
    InputValidationRequest,
    BatchInputValidation
)
from src.core.factories.file_validator_factory import FileValidatorFactory
from src.models import AppConfig


class InputValidatorService:
    """
    Comprehensive input validation service using Pydantic models.
    
    This service follows the Single Responsibility Principle by focusing solely on input validation,
    and the Open/Closed Principle by being extensible for different validation rules.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the input validator service
        
        Args:
            config: Application configuration containing validation settings
        """
        self.config = config
        self.logger = logging.getLogger('input-validator-service')
        
        # Use the unified FileValidator for file validation logic
        self.file_validator = FileValidatorFactory.create_audio_validator(config)
    
    def validate_job_input(self, job_data: Dict[str, Any]) -> InputValidationRequest:
        """
        Validate job input using Pydantic models
        
        Args:
            job_data: Job dictionary containing input parameters
            
        Returns:
            Validated InputValidationRequest object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Extract and validate job input
            input_data = job_data.get('input', {})
            
            # Create JobInputValidation model
            job_input = JobInputValidation(
                datatype=input_data.get('type', 'file'),
                engine=input_data.get('engine', 'custom-whisper'),
                model=input_data.get('model'),
                audio_file=input_data.get('audio_file'),
                url=input_data.get('url'),
                blob_data=input_data.get('blob_data')
            )
            
            # Create base InputValidationRequest
            request = InputValidationRequest(
                job_input=job_input,
                priority=job_data.get('priority', 1),
                config_overrides=job_data.get('config_overrides')
            )
            
            # Validate audio file if applicable
            if job_input.datatype == InputType.FILE and job_input.audio_file:
                audio_validation = self._validate_audio_file(job_input.audio_file)
                request.audio_validation = audio_validation
            
            # Check for validation errors
            validation_errors = request.get_validation_errors()
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                raise ValueError(f"Input validation failed: {error_msg}")
            
            self.logger.info(f"✅ Job input validation successful for {job_input.datatype}")
            return request
            
        except Exception as e:
            self.logger.error(f"❌ Job input validation failed: {e}")
            raise ValueError(f"Input validation failed: {e}")
    
    def validate_batch_input(self, batch_data: Dict[str, Any]) -> BatchInputValidation:
        """
        Validate batch processing input using Pydantic models
        
        Args:
            batch_data: Batch processing configuration
            
        Returns:
            Validated BatchInputValidation object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Create BatchInputValidation model
            batch_input = BatchInputValidation(
                input_directory=batch_data.get('input_directory', 'examples/audio/voice'),
                file_patterns=batch_data.get('file_patterns', ["*.wav", "*.mp3", "*.m4a"]),
                recursive=batch_data.get('recursive', True),
                max_files=batch_data.get('max_files'),
                engine=batch_data.get('engine', 'custom-whisper'),
                model=batch_data.get('model')
            )
            
            self.logger.info(f"✅ Batch input validation successful for directory: {batch_input.input_directory}")
            return batch_input
            
        except Exception as e:
            self.logger.error(f"❌ Batch input validation failed: {e}")
            raise ValueError(f"Batch input validation failed: {e}")
    
    def validate_audio_file(self, file_path: str) -> AudioFileValidation:
        """
        Validate audio file using Pydantic models
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Validated AudioFileValidation object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Use existing FileValidator for file validation
            validation_result = self.file_validator.validate_audio_file(file_path)
            
            # Create AudioFileValidation model
            audio_validation = AudioFileValidation(
                file_path=validation_result.get('file_path', file_path),
                file_name=validation_result.get('file_name', Path(file_path).name),
                file_size=validation_result.get('file_size', 0),
                file_format=validation_result.get('file_format', Path(file_path).suffix),
                valid=validation_result.get('valid', False),
                error=validation_result.get('error')
            )
            
            if not audio_validation.valid:
                raise ValueError(f"Audio file validation failed: {audio_validation.error}")
            
            self.logger.info(f"✅ Audio file validation successful: {file_path}")
            return audio_validation
            
        except Exception as e:
            self.logger.error(f"❌ Audio file validation failed: {e}")
            raise ValueError(f"Audio file validation failed: {e}")
    
    def _validate_audio_file(self, file_path: str) -> AudioFileValidation:
        """
        Internal method for audio file validation (used by validate_job_input)
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioFileValidation object (may contain validation errors)
        """
        try:
            validation_result = self.file_validator.validate_audio_file(file_path)
            
            return AudioFileValidation(
                file_path=validation_result.get('file_path', file_path),
                file_name=validation_result.get('file_name', Path(file_path).name),
                file_size=validation_result.get('file_size', 0),
                file_format=validation_result.get('file_format', Path(file_path).suffix),
                valid=validation_result.get('valid', False),
                error=validation_result.get('error')
            )
        except Exception as e:
            return AudioFileValidation(
                file_path=file_path,
                file_name=Path(file_path).name,
                file_size=0,
                file_format=Path(file_path).suffix,
                valid=False,
                error=str(e)
            )
    
    def validate_transcription_request(self, request: InputValidationRequest) -> bool:
        """
        Validate a complete input validation request
        
        Args:
            request: InputValidationRequest object to validate
            
        Returns:
            True if request is valid and ready for processing
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Check if request is ready for processing
            if not request.is_ready_for_processing():
                validation_errors = request.get_validation_errors()
                raise ValueError(f"Request not ready for processing: {'; '.join(validation_errors)}")
            
            self.logger.info("✅ Transcription request validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Transcription request validation failed: {e}")
            raise ValueError(f"Request validation failed: {e}")
    
    def get_validation_summary(self, request: InputValidationRequest) -> Dict[str, Any]:
        """
        Get a summary of validation results
        
        Args:
            request: InputValidationRequest object
            
        Returns:
            Dictionary containing validation summary
        """
        return {
            'valid': len(request.get_validation_errors()) == 0,
            'ready_for_processing': request.is_ready_for_processing(),
            'input_type': request.job_input.datatype,
            'engine': request.job_input.engine,
            'model': request.job_input.model,
            'priority': request.priority,
            'validation_errors': request.get_validation_errors(),
            'audio_validation': request.audio_validation.model_dump() if request.audio_validation else None,
            'timestamp': request.request_timestamp.isoformat()
        }
