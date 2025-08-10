"""
Result Display Interface
Defines the contract for displaying transcription results
"""

from typing import Dict, Any, List, Protocol


class ResultDisplayInterface(Protocol):
    """Protocol for displaying transcription results"""
    
    def display(self, segments: List[Dict[str, Any]]) -> None:
        """
        Display transcription results
        
        Args:
            segments: List of transcription segments to display
        """
        ... 