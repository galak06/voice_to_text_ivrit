"""
Core module for voice-to-text transcription
Contains the main application logic and orchestration
"""

from .engines.consolidated_transcription_engine import ConsolidatedTranscriptionEngine
from .engines.strategies.chunked_transcription_strategy import ChunkedTranscriptionStrategy
from .engines.strategies.chunking_strategy import (
    ChunkingStrategy,
    OverlappingChunkingStrategy,
    ChunkingStrategyFactory
)
from .engines.utilities.model_manager import ModelManager
from .interfaces.transcription_engine_interface import ITranscriptionEngine
from .logic.input_validator_service import InputValidatorService
from .processors.output_processor import OutputProcessor
from .services.chunk_management_service import ChunkManagementService

__all__ = [
    'ConsolidatedTranscriptionEngine',
    'ChunkedTranscriptionStrategy',
    'ChunkingStrategy',
    'OverlappingChunkingStrategy',
    'ChunkingStrategyFactory',
    'ModelManager',
    'ITranscriptionEngine',
    'InputValidatorService',
    'OutputProcessor',
    'ChunkManagementService'
] 