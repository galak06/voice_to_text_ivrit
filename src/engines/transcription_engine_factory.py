#!/usr/bin/env python3
"""
Factory for creating transcription engines
Implements the Factory Pattern for transcription engine creation and caching
"""

from typing import Dict
from src.engines.interfaces import TranscriptionEngineInterface
from src.engines.transcription_engine import StableWhisperEngine

class TranscriptionEngineFactory:
    """Factory for creating transcription engines following Factory Pattern"""
    
    _engines: Dict[str, TranscriptionEngineInterface] = {}
    
    @classmethod
    def get_engine(cls, engine_type: str, model_name: str) -> TranscriptionEngineInterface:
        """Get or create a transcription engine instance"""
        cache_key = f"{engine_type}_{model_name}"
        
        if cache_key not in cls._engines:
            if engine_type == 'stable-whisper':
                cls._engines[cache_key] = StableWhisperEngine(model_name)
            else:
                raise ValueError(f"Unsupported engine type: {engine_type}")
        
        return cls._engines[cache_key]
    
    @classmethod
    def clear_cache(cls):
        """Clear the engine cache"""
        cls._engines.clear()
    
    @classmethod
    def get_cached_engines(cls) -> Dict[str, str]:
        """Get list of cached engines"""
        return {key: type(engine).__name__ for key, engine in cls._engines.items()} 