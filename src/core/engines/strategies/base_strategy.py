#!/usr/bin/env python3
"""
Base Transcription Strategy
Abstract interface for transcription strategies
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.models.speaker_models import TranscriptionResult

if TYPE_CHECKING:
    from src.core.engines.base_interface import TranscriptionEngine

logger = logging.getLogger(__name__)


class BaseTranscriptionStrategy(ABC):
    """Abstract base class for transcription strategies"""
    
    def __init__(self, config_manager):
        """Initialize strategy with ConfigManager dependency injection"""
        if not config_manager:
            raise ValueError("ConfigManager is required")
        if not hasattr(config_manager, 'config'):
            raise ValueError("ConfigManager must have a config attribute")
        self.config_manager = config_manager
        self.config = config_manager.config
    
    @abstractmethod
    def execute(self, audio_file_path: str, model_name: str, engine: 'TranscriptionEngine') -> TranscriptionResult:
        """Execute the transcription strategy"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        pass
