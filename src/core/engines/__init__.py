#!/usr/bin/env python3
"""
Transcription Engines Package
Refactored architecture following SOLID principles
"""

from .base_interface import TranscriptionEngine
from .consolidated_transcription_engine import ConsolidatedTranscriptionEngine
from .strategies.transcription_strategy_factory import TranscriptionStrategyFactory
from .strategies.base_strategy import BaseTranscriptionStrategy
from .strategies.direct_transcription_strategy import DirectTranscriptionStrategy
from .strategies.chunked_transcription_strategy import ChunkedTranscriptionStrategy
from .strategies.existing_chunks_strategy import ExistingChunksStrategy
from .utilities.cleanup_manager import CleanupManager
from .utilities.model_manager import ModelManager
from .utilities.text_processor import TextProcessor

__all__ = [
    'TranscriptionEngine',
    'ConsolidatedTranscriptionEngine',
    'TranscriptionStrategyFactory',
    'BaseTranscriptionStrategy',
    'DirectTranscriptionStrategy',
    'ChunkedTranscriptionStrategy',
    'ExistingChunksStrategy',
    'CleanupManager',
    'ModelManager',
    'TextProcessor'
]
