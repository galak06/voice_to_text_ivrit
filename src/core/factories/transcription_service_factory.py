#!/usr/bin/env python3
"""
Factory for creating transcription services based on configuration
Follows Factory Pattern and Dependency Injection principles
"""

from src.core.interfaces.transcription_protocols import TranscriptionServiceProtocol
from src.core.models.basic_transcription_service import BasicTranscriptionService
from src.core.models.enhanced_transcription_service import EnhancedTranscriptionService
from src.core.factories.engine_selection_factory import EngineSelectionStrategyFactory


class TranscriptionServiceFactory:
    """Factory for creating transcription services based on configuration"""

    @staticmethod
    def create_service(config_manager, output_manager, transcription_engine=None) -> TranscriptionServiceProtocol:
        """
        Create appropriate transcription service based on config

        Args:
            config_manager: Configuration manager instance
            output_manager: Output manager instance
            transcription_engine: Transcription engine to inject (follows DIP)

        Returns:
            TranscriptionServiceProtocol implementation
        """
        config = config_manager.config

        # Create engine selection strategy
        engine_selection_strategy = EngineSelectionStrategyFactory.create_strategy_from_config(
            config.dict() if hasattr(config, 'dict') else {}
        )

        # Check if enhanced features are enabled
        if hasattr(config, 'enhanced_features') and config.enhanced_features:
            return EnhancedTranscriptionService(
                config_manager, 
                output_manager, 
                transcription_engine,
                engine_selection_strategy
            )
        else:
            return BasicTranscriptionService(
                config_manager, 
                output_manager, 
                transcription_engine,
                engine_selection_strategy
            )
