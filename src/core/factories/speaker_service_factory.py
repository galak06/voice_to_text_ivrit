#!/usr/bin/env python3
"""
Factory for creating speaker services based on configuration
"""

import logging
from src.utils.config_manager import ConfigManager
from src.core.interfaces.transcription_protocols import SpeakerServiceProtocol
from src.core.models.basic_speaker_service import BasicSpeakerService
from src.core.models.advanced_speaker_service import AdvancedSpeakerService
from src.core.models.enhanced_speaker_service import EnhancedSpeakerService

logger = logging.getLogger(__name__)


class SpeakerServiceFactory:
    """Factory for creating speaker services based on configuration"""

    @staticmethod
    def create_service(config_manager: ConfigManager, transcription_engine=None, **kwargs) -> SpeakerServiceProtocol:
        """
        Create appropriate speaker service based on config with dependency injection
        
        Args:
            config_manager: Configuration manager instance (injected)
            transcription_engine: Transcription engine to inject (follows DIP)
            **kwargs: Additional dependencies to inject
            
        Returns:
            SpeakerServiceProtocol implementation
        """
        config = config_manager.config

        # Check if enhanced speaker features are enabled
        if hasattr(config, 'speaker') and config.speaker:
            speaker_config = config.speaker
            
            # Check for enhanced processing configuration
            if getattr(speaker_config, 'enhanced_processing', False):
                logger.info("🚀 Creating Enhanced Speaker Service with two-stage processing")
                return EnhancedSpeakerService(
                    config_manager=config_manager,
                    transcription_engine=transcription_engine,
                    **kwargs
                )
            
            # Check for advanced features
            elif getattr(speaker_config, 'advanced_features', False):
                logger.info("🔧 Creating Advanced Speaker Service")
                return AdvancedSpeakerService(
                    config_manager=config_manager,
                    transcription_engine=transcription_engine,
                    **kwargs
                )
        
        # Default to basic service
        logger.info("📝 Creating Basic Speaker Service")
        return BasicSpeakerService(
            config_manager=config_manager,
            transcription_engine=transcription_engine,
            **kwargs
        )

    @staticmethod
    def create_enhanced_service(config_manager: ConfigManager, **dependencies) -> EnhancedSpeakerService:
        """
        Factory method specifically for enhanced speaker service with full dependency injection
        
        Args:
            config_manager: Configuration manager instance
            **dependencies: All dependencies to inject
            
        Returns:
            EnhancedSpeakerService instance
        """
        logger.info("🚀 Creating Enhanced Speaker Service with full dependency injection")
        return EnhancedSpeakerService(config_manager=config_manager, **dependencies)
