#!/usr/bin/env python3
"""
Job validation utility
Validates job input parameters and provides error messages
"""

from typing import Dict, Any, Optional
from src.core.factories.file_validator_factory import FileValidatorFactory
from src.models import AppConfig


class JobValidator:
    """
    Validates job input parameters following Single Responsibility Principle.
    
    This class now uses the unified FileValidator for file validation logic,
    eliminating code duplication and following the Composition over Inheritance principle.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the job validator
        
        Args:
            config: Application configuration
        """
        self.config = config
        # Use the unified FileValidator for file validation
        self.file_validator = FileValidatorFactory.create_audio_validator(config)
    
    def validate_job_input(self, job: Dict[str, Any]) -> Optional[str]:
        """
        Validate job input parameters following Single Responsibility Principle.
        
        Args:
            job: The job dictionary containing input parameters
            
        Returns:
            Error message if validation fails, None if valid
        """
        input_data = job.get('input', {}) if isinstance(job, dict) else {}
        datatype = input_data.get('type', None)
        engine = input_data.get('engine', 'custom-whisper')
        
        if not datatype:
            return "datatype field not provided. Should be 'blob', 'url', or 'file'."
        
        if datatype not in ['blob', 'url', 'file']:
            return f"datatype should be 'blob', 'url', or 'file', but is {datatype} instead."
        
        if engine not in ['stable-whisper', 'custom-whisper', 'optimized-whisper', 'speaker-diarization']:
            return f"engine should be 'stable-whisper', 'custom-whisper', or 'optimized-whisper', but is {engine} instead."
        
        return None
    
    def validate_audio_file(self, audio_file: str) -> Optional[str]:
        """
        Validate that the audio file exists and is accessible using the unified FileValidator
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not audio_file:
            return "No audio file specified"
        
        # Use the unified FileValidator for file validation
        validation_result = self.file_validator.validate_audio_file(audio_file)
        
        if not validation_result['valid']:
            # Map generic errors to expected messages in tests
            msg = validation_result['error']
            if msg.startswith('File does not exist'):
                return 'Audio file not found'
            if msg == 'File is empty':
                return 'Audio file is empty'
            return msg
        
        return None
    
    @staticmethod
    def validate_model_name(model_name: str) -> Optional[str]:
        """
        Validate model name format
        
        Args:
            model_name: Model name to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not model_name:
            return "Model name is required"
        
        if not isinstance(model_name, str):
            return "Model name must be a string"
        
        if len(model_name.strip()) == 0:
            return "Model name cannot be empty"
        
        return None 