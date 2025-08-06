"""
Transcription Payload Builder Interface
Defines the contract for building transcription payloads
"""

from typing import Dict, Any, Protocol
from ..models import TranscriptionRequest


class TranscriptionPayloadBuilderInterface(Protocol):
    """Protocol for building transcription payloads"""
    
    def build(self, request: TranscriptionRequest) -> Dict[str, Any]:
        """
        Build payload for transcription request
        
        Args:
            request: The transcription request to build payload for
            
        Returns:
            Dictionary containing the built payload
        """
        ... 