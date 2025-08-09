"""
Result Validator Interface
Defines the contract for result validation operations
Following Interface Segregation Principle (ISP)
"""

from typing import Protocol, List, Dict, Any


class ResultValidatorInterface(Protocol):
    """Protocol for result validation operations"""
    
    def validate_segments(self, segments: List[Dict[str, Any]]) -> bool:
        """
        Validate transcription segments structure and content
        
        Args:
            segments: List of transcription segments to validate
            
        Returns:
            True if segments are valid, False otherwise
        """
        ...
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate metadata structure and required fields
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            True if metadata is valid, False otherwise
        """
        ...
    
    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors from last validation
        
        Returns:
            List of validation error messages
        """
        ...
