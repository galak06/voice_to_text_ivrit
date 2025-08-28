#!/usr/bin/env python3
"""
Speaker Enhancement Factory
Creates speaker enhancement orchestrators following Factory Pattern and dependency injection
"""

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from src.core.orchestrator.transcription_service import TranscriptionService as SpeakerTranscriptionService
from src.core.services.speaker_enhancement_orchestrator import SpeakerEnhancementOrchestrator, SpeakerEnhancementInterface

logger = logging.getLogger(__name__)


class SpeakerEnhancementFactoryInterface(ABC):
    """Interface for speaker enhancement factory following Interface Segregation Principle"""
    
    @abstractmethod
    def create_orchestrator(self, speaker_service: SpeakerTranscriptionService, **kwargs) -> SpeakerEnhancementOrchestrator:
        """Create a speaker enhancement orchestrator"""
        pass
    
    @abstractmethod
    def create_strategy(self, strategy_type: str, speaker_service: SpeakerTranscriptionService, **kwargs) -> SpeakerEnhancementInterface:
        """Create a specific enhancement strategy"""
        pass


class SpeakerEnhancementFactory(SpeakerEnhancementFactoryInterface):
    """Factory for creating speaker enhancement components following Factory Pattern"""
    
    def __init__(self):
        """Initialize the factory with available strategies"""
        self._available_strategies = {
            'chunked': 'ChunkedSpeakerEnhancementStrategy',
            'default': 'ChunkedSpeakerEnhancementStrategy'
        }
    
    def create_orchestrator(self, speaker_service: SpeakerTranscriptionService, **kwargs) -> SpeakerEnhancementOrchestrator:
        """
        Create a speaker enhancement orchestrator with dependency injection
        
        Args:
            speaker_service: Injected speaker transcription service
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured SpeakerEnhancementOrchestrator instance
        """
        try:
            logger.info("🏭 Creating speaker enhancement orchestrator")
            
            # Validate speaker service
            if not speaker_service:
                raise ValueError("Speaker service is required for enhancement orchestrator")
            
            # Create orchestrator with injected dependencies
            orchestrator = SpeakerEnhancementOrchestrator(speaker_service)
            
            logger.info("✅ Speaker enhancement orchestrator created successfully")
            return orchestrator
            
        except Exception as e:
            logger.error(f"❌ Error creating speaker enhancement orchestrator: {e}")
            raise
    
    def create_strategy(self, strategy_type: str, speaker_service: SpeakerTranscriptionService, **kwargs) -> SpeakerEnhancementInterface:
        """
        Create a specific enhancement strategy
        
        Args:
            strategy_type: Type of strategy to create
            speaker_service: Injected speaker transcription service
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured enhancement strategy instance
        """
        try:
            logger.info(f"🏭 Creating speaker enhancement strategy: {strategy_type}")
            
            if strategy_type not in self._available_strategies:
                logger.warning(f"⚠️ Unknown strategy type '{strategy_type}', using default")
                strategy_type = 'default'
            
            # Import the strategy class dynamically
            from src.core.services.speaker_enhancement_orchestrator import ChunkedSpeakerEnhancementStrategy
            
            strategy_class = ChunkedSpeakerEnhancementStrategy
            
            # Create strategy instance with injected dependencies
            strategy = strategy_class(speaker_service)
            
            logger.info(f"✅ Speaker enhancement strategy '{strategy_type}' created successfully")
            return strategy
            
        except Exception as e:
            logger.error(f"❌ Error creating speaker enhancement strategy: {e}")
            raise
    
    def get_available_strategies(self) -> list:
        """Get list of available enhancement strategies"""
        return list(self._available_strategies.keys())
    
    def is_strategy_supported(self, strategy_type: str) -> bool:
        """Check if a strategy type is supported"""
        return strategy_type in self._available_strategies
    
    def get_strategy_info(self, strategy_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific strategy"""
        if strategy_type not in self._available_strategies:
            return None
        
        return {
            'type': strategy_type,
            'class_name': self._available_strategies[strategy_type],
            'description': f'Speaker enhancement strategy for {strategy_type} processing'
        }


# Global factory instance for dependency injection
_speaker_enhancement_factory: Optional[SpeakerEnhancementFactory] = None


def get_speaker_enhancement_factory() -> SpeakerEnhancementFactory:
    """Get the global speaker enhancement factory instance following Singleton Pattern"""
    global _speaker_enhancement_factory
    
    if _speaker_enhancement_factory is None:
        _speaker_enhancement_factory = SpeakerEnhancementFactory()
    
    return _speaker_enhancement_factory


def create_speaker_enhancement_orchestrator(speaker_service: SpeakerTranscriptionService, **kwargs) -> SpeakerEnhancementOrchestrator:
    """Convenience function to create a speaker enhancement orchestrator"""
    factory = get_speaker_enhancement_factory()
    return factory.create_orchestrator(speaker_service, **kwargs)


def create_speaker_enhancement_strategy(strategy_type: str, speaker_service: SpeakerTranscriptionService, **kwargs) -> SpeakerEnhancementInterface:
    """Convenience function to create a specific enhancement strategy"""
    factory = get_speaker_enhancement_factory()
    return factory.create_strategy(strategy_type, speaker_service, **kwargs)
