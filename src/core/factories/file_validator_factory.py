"""
File Validator Factory
Factory for creating FileValidator instances with different configurations
"""

from typing import Optional, Set
from src.core.logic.file_validator import FileValidator
from src.models import AppConfig


class FileValidatorFactory:
    """
    Factory for creating FileValidator instances.
    
    This class follows the Factory pattern to provide a centralized way
    to create FileValidator instances with different configurations.
    """
    
    @staticmethod
    def create_audio_validator(config: AppConfig) -> FileValidator:
        """
        Create a FileValidator configured for audio file validation
        
        Args:
            config: Application configuration
            
        Returns:
            FileValidator instance configured for audio files
        """
        audio_formats = {
            '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.webm'
        }
        return FileValidator(config, supported_formats=audio_formats)
    
    @staticmethod
    def create_general_validator(config: AppConfig, supported_formats: Optional[Set[str]] = None) -> FileValidator:
        """
        Create a general-purpose FileValidator
        
        Args:
            config: Application configuration
            supported_formats: Set of supported file extensions (optional)
            
        Returns:
            FileValidator instance
        """
        return FileValidator(config, supported_formats=supported_formats)
    
    @staticmethod
    def create_video_validator(config: AppConfig) -> FileValidator:
        """
        Create a FileValidator configured for video file validation
        
        Args:
            config: Application configuration
            
        Returns:
            FileValidator instance configured for video files
        """
        video_formats = {
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v'
        }
        return FileValidator(config, supported_formats=video_formats)
    
    @staticmethod
    def create_document_validator(config: AppConfig) -> FileValidator:
        """
        Create a FileValidator configured for document file validation
        
        Args:
            config: Application configuration
            
        Returns:
            FileValidator instance configured for document files
        """
        document_formats = {
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'
        }
        return FileValidator(config, supported_formats=document_formats)
    
    @staticmethod
    def create_custom_validator(config: AppConfig, supported_formats: Set[str]) -> FileValidator:
        """
        Create a FileValidator with custom supported formats
        
        Args:
            config: Application configuration
            supported_formats: Set of supported file extensions
            
        Returns:
            FileValidator instance with custom formats
        """
        return FileValidator(config, supported_formats=supported_formats)
