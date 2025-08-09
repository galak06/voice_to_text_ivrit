"""
Speakers Data Extractor Interface
Defines the contract for extracting speakers data from transcription data
"""

from typing import Any, Dict, List, Protocol


class SpeakersDataExtractorInterface(Protocol):
    """Protocol for extracting speakers data"""
    
    def extract(self, data: Any) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract speakers data from transcription data
        
        Args:
            data: The transcription data to extract speakers from
            
        Returns:
            Dictionary mapping speaker names to their segments
        """
        ... 