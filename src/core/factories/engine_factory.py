#!/usr/bin/env python3
"""
Engine Factory
Creates appropriate transcription engines based on configuration
"""

from src.core.engines import (
    TranscriptionEngine,
    ConsolidatedTranscriptionEngine
)

# Engine mapping
ENGINE_MAP = {
    'consolidated': ConsolidatedTranscriptionEngine,
    'optimized-whisper': ConsolidatedTranscriptionEngine,  # Now uses consolidated engine
    'ctranslate2': ConsolidatedTranscriptionEngine,  # Alias for consolidated engine
    'whisper': ConsolidatedTranscriptionEngine,  # Default to consolidated engine
    'speaker-diarization': ConsolidatedTranscriptionEngine,  # Uses consolidated engine with speaker diarization
}

def create_engine(engine_type: str, config, app_config=None) -> TranscriptionEngine:
    """
    Create a transcription engine based on type
    
    Args:
        engine_type: Type of engine to create
        config: Configuration for the engine
        app_config: Application configuration
        
    Returns:
        TranscriptionEngine instance
        
    Raises:
        ValueError: If engine type is not supported
    """
    if engine_type not in ENGINE_MAP:
        raise ValueError(f"Unsupported engine type: {engine_type}. Supported types: {list(ENGINE_MAP.keys())}")
    
    engine_class = ENGINE_MAP[engine_type]
    engine = engine_class(config, app_config)
    
    # Set engine type for proper identification
    engine.engine_type = engine_type
    
    return engine

def get_supported_engines() -> list:
    """Get list of supported engine types"""
    return list(ENGINE_MAP.keys())

def is_engine_supported(engine_type: str) -> bool:
    """Check if an engine type is supported"""
    return engine_type in ENGINE_MAP
