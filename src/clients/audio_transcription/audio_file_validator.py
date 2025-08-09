"""
Audio file validation implementations
"""

from typing import Dict, Any
from src.models import AppConfig
from src.core.factories.file_validator_factory import FileValidatorFactory


class DefaultAudioFileValidator:
    """
    Default implementation of audio file validator using the unified FileValidator.
    
    This class now follows the Composition over Inheritance principle by using
    the FileValidator as a component rather than duplicating validation logic.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        # Use the factory to create an audio-specific validator
        self._validator = FileValidatorFactory.create_audio_validator(config)
    
    def validate(self, file_path: str) -> Dict[str, Any]:
        """
        Validate audio file and return file information
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing validation results and file information
        """
        # Use the unified validator for audio-specific validation
        result = self._validator.validate_audio_file(file_path)
        
        # Maintain backward compatibility with existing return format
        if result['valid']:
            return {
                'path': result['file_path'],
                'size': result['file_size'],
                'size_mb': result['file_size_mb']
            }
        else:
            # Raise exception for backward compatibility
            raise FileNotFoundError(result['error']) if 'not found' in result['error'].lower() else ValueError(result['error']) 