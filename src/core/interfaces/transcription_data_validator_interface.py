"""
Transcription Data Validator Interface
Defines the contract for validating transcription data structures
"""

from typing import Any, Protocol


class TranscriptionDataValidatorInterface(Protocol):
    """Protocol for transcription data validation"""
    
    def validate(self, data: Any) -> bool:
        """
        Validate transcription data structure
        
        Args:
            data: The data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        ... 