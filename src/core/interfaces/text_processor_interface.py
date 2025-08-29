#!/usr/bin/env python3
"""
Text Processor Interface
Defines the contract for text processing operations
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class ITextProcessor(ABC):
    """Interface for text processing operations"""
    
    @abstractmethod
    def get_language_suppression_tokens(self, language: str, *args, **kwargs) -> List[int]:
        """Get language-specific suppression tokens"""
        pass
    
    @abstractmethod
    def filter_language_only(self, text: str, language: str, *args, **kwargs) -> str:
        """Filter text to contain only the specified language"""
        pass
    
    @abstractmethod
    def validate_transcription_quality(self, text: str) -> bool:
        """Validate the quality of transcribed text"""
        pass
