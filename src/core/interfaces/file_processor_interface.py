"""
File Processor Interface
Defines the contract for file processing operations
Following Interface Segregation Principle (ISP)
"""

from typing import Protocol, List
from pathlib import Path


class FileProcessorInterface(Protocol):
    """Protocol for file processing operations"""
    
    def validate_file_exists(self, file_path: Path) -> bool:
        """
        Validate that a file exists and is accessible
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file exists and is accessible, False otherwise
        """
        ...
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get the size of a file in bytes
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes
        """
        ...
    
    def list_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats
        
        Returns:
            List of supported file extensions
        """
        ...
