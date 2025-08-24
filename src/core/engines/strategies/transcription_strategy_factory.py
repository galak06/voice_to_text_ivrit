#!/usr/bin/env python3
"""
Factory for creating transcription strategies
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.engines.strategies.base_strategy import BaseTranscriptionStrategy

if TYPE_CHECKING:
    from src.core.engines.strategies.direct_transcription_strategy import DirectTranscriptionStrategy
    from src.core.engines.strategies.chunked_transcription_strategy import ChunkedTranscriptionStrategy
    from src.core.engines.strategies.existing_chunks_strategy import ExistingChunksStrategy

logger = logging.getLogger(__name__)


class TranscriptionStrategyFactory:
    """Factory for creating appropriate transcription strategies"""
    
    def __init__(self, config, app_config=None):
        self.config = config
        self.app_config = app_config
    
    def create_strategy(self, audio_file_path: str) -> BaseTranscriptionStrategy:
        """Create appropriate strategy based on file characteristics"""
        # First check if file is large enough to require chunking
        if self._is_large_file(audio_file_path):
            from .chunked_transcription_strategy import ChunkedTranscriptionStrategy
            logger.info(f"📁 Large file detected ({self._get_file_size_mb(audio_file_path):.1f}MB), using ChunkedTranscriptionStrategy")
            return ChunkedTranscriptionStrategy(self.config, self.app_config)
        # Then check if there are existing chunks (for resuming interrupted processing)
        elif self._has_existing_chunks():
            from .existing_chunks_strategy import ExistingChunksStrategy
            logger.info("📁 Existing chunks found, using ExistingChunksStrategy")
            return ExistingChunksStrategy(self.config, self.app_config)
        else:
            from .direct_transcription_strategy import DirectTranscriptionStrategy
            logger.info("📁 Small file, using DirectTranscriptionStrategy")
            return DirectTranscriptionStrategy(self.config, self.app_config)
    
    def _has_existing_chunks(self) -> bool:
        """Check if audio chunks directory exists and contains files"""
        chunks_dir = Path("examples/audio/voice/audio_chunks")
        return chunks_dir.exists() and any(chunks_dir.glob("audio_chunk_*.wav"))
    
    def _is_large_file(self, audio_file_path: str) -> bool:
        """Determine if file is large enough to require chunking"""
        file_size_mb = self._get_file_size_mb(audio_file_path)
        return file_size_mb > 100
    
    def _get_file_size_mb(self, audio_file_path: str) -> float:
        """Get file size in MB"""
        try:
            return Path(audio_file_path).stat().st_size / (1024 * 1024)
        except Exception:
            return 0.0
