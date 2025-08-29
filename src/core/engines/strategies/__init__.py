#!/usr/bin/env python3
"""
Transcription Strategy Implementations
"""

from .base_strategy import BaseTranscriptionStrategy
from .transcription_strategy_factory import TranscriptionStrategyFactory
from .direct_transcription_strategy import DirectTranscriptionStrategy
from .chunked_transcription_strategy import ChunkedTranscriptionStrategy
from .existing_chunks_strategy import ExistingChunksStrategy
# Chunking strategies module
# Follows SOLID principles with dependency injection

from .chunking_strategy import (
    ChunkingStrategy,
    OverlappingChunkingStrategy,
    ChunkingStrategyFactory
)

__all__ = [
    'BaseTranscriptionStrategy',
    'TranscriptionStrategyFactory',
    'DirectTranscriptionStrategy',
    'ChunkedTranscriptionStrategy',
    'ExistingChunksStrategy',
    'ChunkingStrategy',
    'OverlappingChunkingStrategy',
    'ChunkingStrategyFactory'
]
