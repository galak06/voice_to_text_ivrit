"""
Audio File Validator Interface
Defines the contract for validating audio files
"""

from typing import Dict, Any, Protocol


class AudioFileValidatorInterface(Protocol):
    """Protocol for audio file validation"""
    
    def validate(self, file_path: str) -> Dict[str, Any]:
        """
        Validate audio file and return file information
        
        Args:
            file_path: Path to the audio file to validate
            
        Returns:
            Dictionary containing file information and validation results
        """
        ... 