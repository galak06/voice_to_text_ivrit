"""
Output Saver Interface
Defines the contract for saving transcription outputs
Refactored to follow Interface Segregation Principle (ISP)
"""

from typing import Dict, Any, List, Protocol
from pathlib import Path


class OutputSaverInterface(Protocol):
    """Protocol for saving transcription outputs - focused on saving operations only"""
    
    def save_text(self, output_path: Path, text_content: str) -> Path:
        """
        Save text content to file
        
        Args:
            output_path: Path where to save the text file
            text_content: Text content to save
            
        Returns:
            Path to the saved file
        """
        ...
    
    def save_json(self, output_path: Path, data: Dict[str, Any]) -> Path:
        """
        Save data as JSON file
        
        Args:
            output_path: Path where to save the JSON file
            data: Data to save as JSON
            
        Returns:
            Path to the saved file
        """
        ...
    
    def create_output_directory(self, base_path: Path, filename: str) -> Path:
        """
        Create output directory for saving files
        
        Args:
            base_path: Base directory path
            filename: Name of the file (used to generate directory name)
            
        Returns:
            Path to the created directory
        """
        ... 