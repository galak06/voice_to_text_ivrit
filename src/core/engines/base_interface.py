#!/usr/bin/env python3
"""
Transcription Engine Abstract Base Class
Pure abstract interface - no concrete logic
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from src.models import TranscriptionResult

logger = logging.getLogger(__name__)


class TranscriptionEngine(ABC):
    """Pure abstract base class for transcription engines - NO concrete logic"""
    
    @abstractmethod
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe audio file - to be implemented by each engine"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available"""
        pass
    
    @abstractmethod
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> TranscriptionResult:
        """Transcribe a single audio chunk - to be implemented by each engine"""
        pass
    
    @abstractmethod
    def cleanup_models(self) -> None:
        """Clean up loaded models and free memory"""
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine"""
        pass
