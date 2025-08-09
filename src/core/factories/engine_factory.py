#!/usr/bin/env python3
"""
Engine Factory for creating transcription engines
Implements Factory Pattern for engine creation
"""

import logging
from typing import Dict, List, Type, Any
from ...models.speaker_models import SpeakerConfig
from src.core.interfaces.transcription_engine_interface import ITranscriptionEngine
from src.core.engines.speaker_engines import (
    CustomWhisperEngine,
    StableWhisperEngine,
    OptimizedWhisperEngine
)

logger = logging.getLogger(__name__)


class TranscriptionEngineFactory:
    """
    Factory for creating transcription engines
    
    This factory implements the Factory Pattern to create different types
    of transcription engines based on the engine type string. It provides
    a centralized way to manage engine creation and configuration.
    """
    
    # Registry of available engines
    _engines: Dict[str, Type[ITranscriptionEngine]] = {
        'custom-whisper': CustomWhisperEngine,
        'stable-whisper': StableWhisperEngine,
        'optimized-whisper': OptimizedWhisperEngine,
        'ctranslate2': OptimizedWhisperEngine,  # Alias for optimized-whisper
        'speaker-diarization': CustomWhisperEngine  # Default for speaker diarization
    }
    
    @classmethod
    def register_engine(cls, engine_type: str, engine_class: Type[ITranscriptionEngine]):
        """
        Register a new engine type
        
        Args:
            engine_type: String identifier for the engine
            engine_class: Class that implements ITranscriptionEngine
        """
        cls._engines[engine_type] = engine_class
        logger.info(f"🔧 Registered engine: {engine_type} -> {engine_class.__name__}")
    
    @classmethod
    def create_engine(cls, engine_type: str, config: SpeakerConfig, app_config=None) -> ITranscriptionEngine:
        """
        Create a transcription engine instance
        
        Args:
            engine_type: Type of engine to create
            config: Speaker configuration
            app_config: Application configuration (optional)
            
        Returns:
            ITranscriptionEngine: Engine instance
            
        Raises:
            ValueError: If engine type is not supported
        """
        if engine_type not in cls._engines:
            available_engines = list(cls._engines.keys())
            raise ValueError(f"Unknown engine type: {engine_type}. Available engines: {available_engines}")
        
        engine_class = cls._engines[engine_type]
        logger.info(f"🏭 Creating engine: {engine_type} ({engine_class.__name__})")
        
        return engine_class(config, app_config)
    
    @classmethod
    def get_available_engines(cls, config: SpeakerConfig) -> List[ITranscriptionEngine]:
        """
        Get list of all available engines
        
        Args:
            config: Speaker configuration
            
        Returns:
            List[ITranscriptionEngine]: List of available engine instances
        """
        available_engines = []
        
        for engine_type, engine_class in cls._engines.items():
            try:
                engine = engine_class(config)
                if engine.is_available():
                    available_engines.append(engine)
                    logger.debug(f"✅ Engine available: {engine_type}")
                else:
                    logger.debug(f"❌ Engine not available: {engine_type}")
            except Exception as e:
                logger.warning(f"⚠️ Error checking engine {engine_type}: {e}")
        
        logger.info(f"📊 Found {len(available_engines)} available engines")
        return available_engines
    
    @classmethod
    def get_engine_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered engines
        
        Returns:
            Dict[str, Dict[str, Any]]: Engine information
        """
        engine_info = {}
        
        for engine_type, engine_class in cls._engines.items():
            engine_info[engine_type] = {
                'class_name': engine_class.__name__,
                'module': engine_class.__module__,
                'description': getattr(engine_class, '__doc__', 'No description available')
            }
        
        return engine_info
    
    @classmethod
    def get_supported_engine_types(cls) -> List[str]:
        """
        Get list of supported engine types
        
        Returns:
            List[str]: List of supported engine type strings
        """
        return list(cls._engines.keys())
    
    @classmethod
    def get_default_engine_type(cls) -> str:
        """
        Get the default engine type
        
        Returns:
            str: Default engine type
        """
        return 'speaker-diarization'
    
    @classmethod
    def validate_engine_type(cls, engine_type: str) -> bool:
        """
        Validate if an engine type is supported
        
        Args:
            engine_type: Engine type to validate
            
        Returns:
            bool: True if engine type is supported
        """
        return engine_type in cls._engines
