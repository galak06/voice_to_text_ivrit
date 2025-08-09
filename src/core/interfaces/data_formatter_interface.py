"""
Data Formatter Interface
Defines the contract for data formatting operations
Following Interface Segregation Principle (ISP)
"""

from typing import Protocol, Dict, Any, List


class DataFormatterInterface(Protocol):
    """Protocol for data formatting operations"""
    
    def format_segments(self, segments: List[Dict[str, Any]]) -> str:
        """
        Format transcription segments into a single text string
        
        Args:
            segments: List of transcription segments
            
        Returns:
            Formatted text string
        """
        ...
    
    def format_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format metadata for output
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Formatted metadata dictionary
        """
        ...
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats
        
        Returns:
            List of supported format names
        """
        ...
