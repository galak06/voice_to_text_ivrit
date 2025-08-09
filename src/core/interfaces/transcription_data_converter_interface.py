"""
Transcription Data Converter Interface
Defines the contract for converting transcription data to dictionary format
"""

from typing import Any, Dict, Protocol


class TranscriptionDataConverterInterface(Protocol):
    """Protocol for transcription data conversion"""
    
    def convert(self, data: Any) -> Dict[str, Any]:
        """
        Convert transcription data to dictionary format
        
        Args:
            data: The transcription data to convert
            
        Returns:
            Dictionary representation of the transcription data
        """
        ... 