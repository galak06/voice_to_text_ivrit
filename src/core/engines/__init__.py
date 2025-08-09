#!/usr/bin/env python3
"""
Transcription Engines Package

This package contains all transcription engine implementations and related components.
It provides a modular architecture for different transcription engines with a common interface.
"""

# Import from the main speaker_engines.py file which contains all implementations
from .speaker_engines import (
    TranscriptionEngine,
    CustomWhisperEngine,
    StableWhisperEngine,
    OptimizedWhisperEngine,
    TranscriptionEngineFactory
)

# Import interfaces from the interfaces module
from ..interfaces.transcription_engine_interface import (
    ITranscriptionEngine,
    IChunkableTranscriptionEngine,
    IMemoryManagedTranscriptionEngine,
    IConfigurableTranscriptionEngine
)

__all__ = [
    # Base class
    'TranscriptionEngine',
    
    # Engine implementations
    'CustomWhisperEngine',
    'StableWhisperEngine', 
    'OptimizedWhisperEngine',
    
    # Factory
    'TranscriptionEngineFactory',
    
    # Interfaces (for type hints and contracts)
    'ITranscriptionEngine',
    'IChunkableTranscriptionEngine',
    'IMemoryManagedTranscriptionEngine',
    'IConfigurableTranscriptionEngine'
]

# Version information
__version__ = "1.0.0"
__author__ = "Voice to Text Team"
__description__ = "Modular transcription engines with common interface"
