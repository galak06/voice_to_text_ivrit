#!/usr/bin/env python3
"""
Transcription Service Interface
Defines the contract for transcription services following Interface Segregation Principle
"""

from typing import Protocol, Dict, Any, Generator, Optional
from datetime import datetime

from src.models.base_models import ProcessingResult, ErrorInfo


class TranscriptionServiceInterface(Protocol):
    """Protocol defining the interface for transcription services"""
    
    def transcribe(self, job: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Transcribe audio file and return segments
        
        Args:
            job: Job dictionary containing input parameters
            
        Yields:
            Transcription segments or error messages
        """
        ...
    
    def validate_job(self, job: Dict[str, Any]) -> Optional[ErrorInfo]:
        """
        Validate job parameters
        
        Args:
            job: Job dictionary to validate
            
        Returns:
            ErrorInfo if validation fails, None if valid
        """
        ...
    
    def get_supported_engines(self) -> Dict[str, str]:
        """
        Get supported transcription engines
        
        Returns:
            Dictionary mapping engine names to descriptions
        """
        ...
    
    def get_supported_models(self) -> Dict[str, str]:
        """
        Get supported transcription models
        
        Returns:
            Dictionary mapping model names to descriptions
        """
        ...


class TranscriptionOrchestratorInterface(Protocol):
    """Protocol defining the interface for transcription orchestrators"""
    
    def transcribe(self, input_data: Dict[str, Any], **kwargs) -> ProcessingResult:
        """
        Perform transcription on input data
        
        Args:
            input_data: Input data containing file information
            **kwargs: Additional transcription parameters
            
        Returns:
            ProcessingResult containing transcription results
        """
        ...
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics
        
        Returns:
            Dictionary containing processing statistics
        """
        ...
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        ...
    
    def cleanup(self) -> None:
        """Cleanup orchestrator resources"""
        ...


class AudioProcessorInterface(Protocol):
    """Protocol defining the interface for audio processors"""
    
    def prepare_audio_file(self, job: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """
        Prepare audio file for processing
        
        Args:
            job: Job dictionary containing file information
            
        Returns:
            Tuple of (temp_dir, audio_file_path) or (None, error_message)
        """
        ...
    
    def cleanup_temp_files(self, temp_dir: str) -> None:
        """
        Clean up temporary files
        
        Args:
            temp_dir: Temporary directory to clean up
        """
        ...
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate audio file format and accessibility
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if valid, False otherwise
        """
        ...


class JobValidatorInterface(Protocol):
    """Protocol defining the interface for job validators"""
    
    def validate_job_input(self, job: Dict[str, Any]) -> Optional[str]:
        """
        Validate job input parameters
        
        Args:
            job: Job dictionary to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        ...
    
    def validate_audio_file(self, file_path: str) -> Optional[str]:
        """
        Validate audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Error message if validation fails, None if valid
        """
        ...
    
    def validate_model_engine_combination(self, model: str, engine: str) -> bool:
        """
        Validate model and engine combination
        
        Args:
            model: Model name
            engine: Engine name
            
        Returns:
            True if combination is valid, False otherwise
        """
        ...
