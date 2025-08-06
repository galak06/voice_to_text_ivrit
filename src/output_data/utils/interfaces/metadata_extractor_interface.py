"""
Metadata Extractor Interface
Defines the contract for extracting metadata from transcription data
"""

from typing import Any, Protocol


class MetadataExtractorInterface(Protocol):
    """Protocol for extracting metadata"""
    
    def get_model_name(self, data: Any) -> str:
        """
        Extract model name from transcription data
        
        Args:
            data: The transcription data to extract model name from
            
        Returns:
            Model name as string
        """
        ...
    
    def get_audio_file(self, data: Any) -> str:
        """
        Extract audio file path from transcription data
        
        Args:
            data: The transcription data to extract audio file from
            
        Returns:
            Audio file path as string
        """
        ... 