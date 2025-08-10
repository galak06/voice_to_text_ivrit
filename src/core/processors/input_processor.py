"""
Input Processor
Responsible for handling input file discovery, validation, and processing
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
import logging
from datetime import datetime

from src.utils.config_manager import ConfigManager
from src.core.factories.file_validator_factory import FileValidatorFactory

if TYPE_CHECKING:
    from src.output_data import OutputManager
from src.core.logic.result_builder import ResultBuilder


class InputProcessor:
    """
    Handles input file processing and validation
    
    This class follows the Single Responsibility Principle by focusing
    solely on input-related operations.
    """
    
    def __init__(self, config_manager: ConfigManager, output_manager: 'OutputManager'):
        """
        Initialize the input processor
        
        Args:
            config_manager: Configuration manager instance
            output_manager: Output manager instance for logging
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.output_manager = output_manager
        self.logger = logging.getLogger('input-processor')
        
        # Use the unified FileValidator instead of duplicating validation logic
        self.file_validator = FileValidatorFactory.create_audio_validator(self.config)
        # Expose supported_formats for backwards-compatibility with older tests
        try:
            self.supported_formats = set(self.file_validator.get_supported_formats())
        except Exception:
            self.supported_formats = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
    
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
            
        except (OSError, IOError) as e:
            self.logger.error(f"File system error discovering files in {input_directory}: {e}")
            return []
        except (ValueError, TypeError) as e:
            self.logger.error(f"Validation error discovering files in {input_directory}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error discovering files in {input_directory}: {e}")
            return []
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a single audio file using the unified FileValidator
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing validation results
        """
        # Use the unified FileValidator for all validation logic
        return self.file_validator.validate_audio_file(file_path)
    
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
                return (ResultBuilder()
                        .success(False)
                        .error(validation_result['error'])
                        .file_path(file_path)
                        .build())
            
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
            
            return (ResultBuilder()
                    .success(True)
                    .data(input_data)
                    .metadata(metadata)
                    .validation(validation_result)
                    .build())
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Validation error processing input file {file_path}: {e}")
            return (ResultBuilder()
                    .success(False)
                    .error(str(e))
                    .file_path(file_path)
                    .build())
        except (OSError, IOError) as e:
            self.logger.error(f"File system error processing input file {file_path}: {e}")
            return (ResultBuilder()
                    .success(False)
                    .error(str(e))
                    .file_path(file_path)
                    .build())
        except Exception as e:
            self.logger.error(f"Unexpected error processing input file {file_path}: {e}")
            return (ResultBuilder()
                    .success(False)
                    .error(str(e))
                    .file_path(file_path)
                    .build())
    
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
        return self.file_validator.get_supported_formats()
    
    def add_supported_format(self, format_extension: str):
        """
        Add a new supported audio format
        
        Args:
            format_extension: File extension to add (e.g., '.mp4')
        """
        self.file_validator.add_supported_format(format_extension)
        # Keep local cache in sync
        if format_extension.startswith('.'):
            self.supported_formats.add(format_extension.lower())
    
    def remove_supported_format(self, format_extension: str):
        """
        Remove a supported audio format
        
        Args:
            format_extension: File extension to remove
        """
        self.file_validator.remove_supported_format(format_extension)
        # Keep local cache in sync
        if format_extension.lower() in self.supported_formats:
            self.supported_formats.remove(format_extension.lower())