#!/usr/bin/env python3
"""
Services Module
Contains service layer components following clean architecture principles
"""

from .speaker_enhancement_orchestrator import (
    SpeakerEnhancementOrchestrator,
    SpeakerEnhancementInterface,
    ChunkedSpeakerEnhancementStrategy,
    EnhancementContext
)

from .chunk_enhancement_strategies import (
    ChunkEnhancementStrategy,
    ChunkEnhancementContext as ChunkContext,
    ChunkEnhancementStrategyFactory,
    NoEnhancementStrategy,
    BasicSpeakerEnhancementStrategy,
    AdvancedSpeakerEnhancementStrategy
)

from .chunk_management_service import (
    ChunkManagementService,
    ChunkManager,
    OverlappingChunkManager,
    FixedDurationChunkManager
)

from .chunk_processing_service import (
    ChunkProcessingService,
    ChunkProcessor,
    AudioChunkProcessor
)

__all__ = [
    'SpeakerEnhancementOrchestrator',
    'SpeakerEnhancementInterface', 
    'ChunkedSpeakerEnhancementStrategy',
    'EnhancementContext',
    'ChunkEnhancementStrategy',
    'ChunkContext',
    'ChunkEnhancementStrategyFactory',
    'NoEnhancementStrategy',
    'BasicSpeakerEnhancementStrategy',
    'AdvancedSpeakerEnhancementStrategy',
    'ChunkManagementService',
    'ChunkManager',
    'OverlappingChunkManager',
    'FixedDurationChunkManager',
    'ChunkProcessingService',
    'ChunkProcessor',
    'AudioChunkProcessor'
]
