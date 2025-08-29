#!/usr/bin/env python3
"""
Simple Text Processor Implementation
Basic text processing operations for transcription
"""

from typing import List
from src.core.interfaces.text_processor_interface import ITextProcessor


class SimpleTextProcessor(ITextProcessor):
    """Simple text processor implementation"""
    
    def get_language_suppression_tokens(self, language: str, *args, **kwargs) -> List[int]:
        """Return empty list for language suppression tokens"""
        return []
    
    def filter_language_only(self, text: str, language: str, *args, **kwargs) -> str:
        """Simple text filter - return text as is"""
        return text
    
    def validate_transcription_quality(self, text: str) -> bool:
        """Simple quality validation - return True if text exists"""
        return bool(text and text.strip())
