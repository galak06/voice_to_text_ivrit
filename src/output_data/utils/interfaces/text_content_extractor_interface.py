"""
Text Content Extractor Interface
Defines the contract for extracting text content from transcription data
"""

from typing import Any, Protocol


class TextContentExtractorInterface(Protocol):
    """Protocol for extracting text content"""
    
    def extract(self, data: Any) -> str:
        """
        Extract text content from transcription data
        
        Args:
            data: The transcription data to extract text from
            
        Returns:
            Extracted text content as string
        """
        ... 