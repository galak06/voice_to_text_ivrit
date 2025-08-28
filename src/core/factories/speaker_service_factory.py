#!/usr/bin/env python3
"""
Factory for creating speaker services based on configuration
"""

from src.utils.config_manager import ConfigManager
from src.core.interfaces.transcription_protocols import SpeakerServiceProtocol
from src.core.models.basic_speaker_service import BasicSpeakerService
from src.core.models.advanced_speaker_service import AdvancedSpeakerService


class SpeakerServiceFactory:
    """Factory for creating speaker services based on configuration"""

    @staticmethod
    def create_service(config_manager: ConfigManager, transcription_engine=None) -> SpeakerServiceProtocol:
        """
        Create appropriate speaker service based on config
        
        Args:
            config_manager: Configuration manager instance
            transcription_engine: Transcription engine to inject (follows DIP)
            
        Returns:
            SpeakerServiceProtocol implementation
        """
        config = config_manager.config

        # Check if advanced speaker features are enabled
        if hasattr(config, 'speaker') and config.speaker and getattr(config.speaker, 'advanced_features', False):
            return AdvancedSpeakerService(config_manager, transcription_engine)
        else:
            return BasicSpeakerService(config_manager, transcription_engine)
