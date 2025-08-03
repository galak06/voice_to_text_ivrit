"""
Input Processor
Responsible for handling input file discovery, validation, and processing
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from src.utils.output_manager import OutputManager


class InputProcessor:
    """
    Handles input file processing and validation
    
    This class follows the Single Responsibility Principle by focusing
    solely on input-related operations.
    """
    
    def __init__(self, config: Any, output_manager: OutputManager):
        """
        Initialize the input processor
        
        Args:
            config: Application configuration
            output_manager: Output manager instance for logging
        """
        self.config = config
        self.output_manager = output_manager
        self.logger = logging.getLogger('input-processor')
        
        # Supported audio formats
        self.supported_formats = {
            '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.wma'
        }
    
    def discover_files(self, input_directory: str) -> List[str]:
        """
        Discover audio files in the specified directory
        
        Args:
            input_directory: Directory to search for audio files
            
        Returns:
            List of discovered audio file paths
        """
        try:
            input_path = Path(input_directory)
            
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_directory}")
                return []
            
            if not input_path.is_dir():
                self.logger.error(f"Input path is not a directory: {input_directory}")
                return []
            
            # Find all audio files recursively
            audio_files = []
            for file_path in input_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    audio_files.append(str(file_path))
            
            # Sort files for consistent processing order
            audio_files.sort()
            
            self.logger.info(f"Discovered {len(audio_files)} audio files in {input_directory}")
            return audio_files
            
        except Exception as e:
            self.logger.error(f"Error discovering files in {input_directory}: {e}")
            return []
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a single audio file
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing validation results
        """
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return {
                    'valid': False,
                    'error': f"File does not exist: {file_path}"
                }
            
            # Check if it's a file
            if not path.is_file():
                return {
                    'valid': False,
                    'error': f"Path is not a file: {file_path}"
                }
            
            # Check file format
            if path.suffix.lower() not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f"Unsupported file format: {path.suffix}"
                }
            
            # Check file size
            file_size = path.stat().st_size
            if file_size == 0:
                return {
                    'valid': False,
                    'error': "File is empty"
                }
            
            # Check if file is readable
            try:
                with open(path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to test readability
            except Exception as e:
                return {
                    'valid': False,
                    'error': f"File is not readable: {e}"
                }
            
            return {
                'valid': True,
                'file_path': str(path),
                'file_name': path.name,
                'file_size': file_size,
                'file_format': path.suffix.lower(),
                'last_modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Validation error: {e}"
            }
    
    def process_input(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single input file
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing processing results
        """
        try:
            self.logger.info(f"Processing input file: {file_path}")
            
            # Validate the file
            validation_result = self.validate_file(file_path)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'file_path': file_path
                }
            
            # Read file metadata
            metadata = self._extract_metadata(validation_result)
            
            # Prepare input data
            input_data = {
                'file_path': file_path,
                'file_name': validation_result['file_name'],
                'file_size': validation_result['file_size'],
                'file_format': validation_result['file_format']
            }
            
            self.logger.info(f"Input processing completed: {file_path}")
            
            return {
                'success': True,
                'data': input_data,
                'metadata': metadata,
                'validation': validation_result
            }
            
        except Exception as e:
            self.logger.error(f"Error processing input file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _extract_metadata(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from validation result
        
        Args:
            validation_result: Result from file validation
            
        Returns:
            Dictionary containing file metadata
        """
        return {
            'file_name': validation_result['file_name'],
            'file_size': validation_result['file_size'],
            'file_format': validation_result['file_format'],
            'last_modified': validation_result['last_modified'],
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats
        
        Returns:
            List of supported file extensions
        """
        return list(self.supported_formats)
    
    def add_supported_format(self, format_extension: str):
        """
        Add a new supported audio format
        
        Args:
            format_extension: File extension to add (e.g., '.mp4')
        """
        if format_extension.startswith('.'):
            self.supported_formats.add(format_extension.lower())
            self.logger.info(f"Added supported format: {format_extension}")
        else:
            self.logger.warning(f"Format extension should start with '.': {format_extension}")
    
    def remove_supported_format(self, format_extension: str):
        """
        Remove a supported audio format
        
        Args:
            format_extension: File extension to remove
        """
        if format_extension.lower() in self.supported_formats:
            self.supported_formats.remove(format_extension.lower())
            self.logger.info(f"Removed supported format: {format_extension}")
        else:
            self.logger.warning(f"Format not in supported list: {format_extension}") 