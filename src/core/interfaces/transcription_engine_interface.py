#!/usr/bin/env python3
"""
Base interface for transcription engines
This interface defines the contract that all transcription engines must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from ...models.speaker_models import SpeakerConfig, TranscriptionResult, TranscriptionSegment


class ITranscriptionEngine(ABC):
    """
    Base interface for transcription engines
    
    This interface defines the contract that all transcription engines must implement.
    It follows the Interface Segregation Principle (ISP) from SOLID principles.
    """
    
    @abstractmethod
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """
        Transcribe audio file with speaker diarization
        
        Args:
            audio_file_path: Path to the audio file
            model_name: Name of the model to use for transcription
            
        Returns:
            TranscriptionResult: The transcription result with segments and speakers
            
        Raises:
            Exception: If transcription fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the engine is available and can be used
        
        Returns:
            bool: True if the engine is available, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup_models(self):
        """
        Clean up loaded models and free memory
        
        This method should be called when the engine is no longer needed
        to free up system resources.
        """
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the engine
        
        Returns:
            Dict[str, Any]: Engine information including name, version, capabilities
        """
        pass


class IChunkableTranscriptionEngine:
    """
    Interface for engines that support chunk-based processing
    
    This interface extends the base transcription engine interface
    for engines that can process audio in chunks for better memory management.
    """
    
    @abstractmethod
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, 
                         chunk_end: float, model_name: str) -> 'TranscriptionResult':
        """
        Transcribe a single audio chunk
        
        Args:
            audio_chunk: The audio chunk data
            chunk_count: Sequential number of the chunk
            chunk_start: Start time of the chunk in seconds
            chunk_end: End time of the chunk in seconds
            model_name: Name of the model to use
            
        Returns:
            TranscriptionResult: The transcription result with segments and speakers
        """
        pass
    
    @abstractmethod
    def _merge_chunks(self, chunks_data: List[Dict[str, Any]], 
                     audio_file_path: str, model_name: str) -> Dict[str, Any]:
        """
        Merge multiple transcribed chunks into a single result
        
        Args:
            chunks_data: List of chunk data dictionaries
            audio_file_path: Path to the original audio file
            model_name: Name of the model used
            
        Returns:
            Dict[str, Any]: Merged transcription data
        """
        pass


class IMemoryManagedTranscriptionEngine:
    """
    Interface for engines that require explicit memory management
    
    This interface is for engines that use GPU memory or large models
    and need explicit cleanup methods.
    """
    
    @abstractmethod
    def _cleanup_model_memory(self):
        """
        Clean up model memory (GPU, CPU cache, etc.)
        
        This method should be called after processing to free up memory.
        """
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage information
        
        Returns:
            Dict[str, float]: Memory usage in MB for different types (GPU, CPU, etc.)
        """
        pass


class IConfigurableTranscriptionEngine:
    """
    Interface for engines that support configuration
    
    This interface is for engines that can be configured with different
    parameters and settings.
    """
    
    @abstractmethod
    def update_config(self, config: SpeakerConfig):
        """
        Update engine configuration
        
        Args:
            config: New configuration settings
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported model names
        
        Returns:
            List[str]: List of supported model names
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default model name for this engine
        
        Returns:
            str: Default model name
        """
        pass
