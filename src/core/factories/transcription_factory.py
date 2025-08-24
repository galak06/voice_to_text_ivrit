#!/usr/bin/env python3
"""
Transcription Factory
Factory pattern implementation for creating transcription services
"""

from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from src.core.interfaces.transcription_service_interface import TranscriptionServiceInterface
from src.models.base_models import ErrorInfo

logger = logging.getLogger(__name__)


class TranscriptionServiceFactory:
    """
    Factory for creating transcription services
    
    This class follows the Factory pattern and Open/Closed Principle:
    - Open for extension: New services can be added without modifying existing code
    - Closed for modification: Existing factory logic doesn't need to change
    """
    
    def __init__(self):
        """Initialize the factory with available services"""
        self._services: Dict[str, Type[TranscriptionServiceInterface]] = {}
        self._register_default_services()
    
    def register_service(self, service_type: str, service_class: Type[TranscriptionServiceInterface]) -> None:
        """
        Register a new transcription service
        
        Args:
            service_type: Type identifier for the service
            service_class: Class implementing TranscriptionServiceInterface
        """
        self._services[service_type] = service_class
        logger.info(f"Registered transcription service: {service_type}")
    
    def create_service(self, service_type: str, **kwargs) -> Optional[TranscriptionServiceInterface]:
        """
        Create a transcription service instance
        
        Args:
            service_type: Type of service to create
            **kwargs: Constructor arguments for the service
            
        Returns:
            Service instance or None if creation fails
        """
        try:
            if service_type not in self._services:
                logger.error(f"Unknown transcription service type: {service_type}")
                return None
            
            service_class = self._services[service_type]
            service_instance = service_class(**kwargs)
            
            logger.info(f"Created transcription service: {service_type}")
            return service_instance
            
        except Exception as e:
            logger.error(f"Failed to create transcription service {service_type}: {e}")
            return None
    
    def get_available_services(self) -> Dict[str, str]:
        """
        Get list of available service types
        
        Returns:
            Dictionary mapping service types to descriptions
        """
        return {
            'speaker-diarization': 'Speaker diarization with transcription',
            'custom-whisper': 'Custom Whisper model transcription',
            'ctranslate2-whisper': 'CTranslate2 optimized Whisper transcription',
            'stable-whisper': 'Stable Whisper transcription',
            'faster-whisper': 'Faster Whisper transcription'
        }
    
    def validate_service_type(self, service_type: str) -> bool:
        """
        Validate if a service type is supported
        
        Args:
            service_type: Service type to validate
            
        Returns:
            True if supported, False otherwise
        """
        return service_type in self._services
    
    def _register_default_services(self) -> None:
        """Register default transcription services"""
        try:
            # Import and register default services
            from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService
            from src.core.orchestrator.transcription_service import TranscriptionService
            
            self.register_service('speaker-diarization', SpeakerTranscriptionService)
            self.register_service('stable-whisper', TranscriptionService)
            
            # Register additional services if available
            self._register_optional_services()
            
        except ImportError as e:
            logger.warning(f"Some transcription services not available: {e}")
    
    def _register_optional_services(self) -> None:
        """Register optional transcription services"""
        try:
            # Custom Whisper service
            from src.core.engines import CustomWhisperEngine
            self.register_service('custom-whisper', CustomWhisperEngine)
        except ImportError:
            logger.debug("Custom Whisper service not available")
        
        try:
            # CTranslate2 Whisper service
            from src.core.engines import ConsolidatedTranscriptionEngine
            self.register_service('ctranslate2-whisper', ConsolidatedTranscriptionEngine)
        except ImportError:
            logger.debug("CTranslate2 Whisper service not available")


class TranscriptionServiceBuilder:
    """
    Builder pattern for creating transcription services with complex configuration
    
    This class follows the Builder pattern to construct complex transcription services
    with optional parameters and validation.
    """
    
    def __init__(self, factory: TranscriptionServiceFactory):
        """
        Initialize the builder
        
        Args:
            factory: Factory instance for creating services
        """
        self.factory = factory
        self.service_type: Optional[str] = None
        self.config: Optional[Dict[str, Any]] = None
        self.model: Optional[str] = None
        self.engine: Optional[str] = None
        self.language: str = "he"
        self.word_timestamps: bool = True
        self.vad_enabled: bool = True
    
    def with_service_type(self, service_type: str) -> 'TranscriptionServiceBuilder':
        """Set the service type"""
        self.service_type = service_type
        return self
    
    def with_config(self, config: Dict[str, Any]) -> 'TranscriptionServiceBuilder':
        """Set the configuration"""
        self.config = config
        return self
    
    def with_model(self, model: str) -> 'TranscriptionServiceBuilder':
        """Set the model"""
        self.model = model
        return self
    
    def with_engine(self, engine: str) -> 'TranscriptionServiceBuilder':
        """Set the engine"""
        self.engine = engine
        return self
    
    def with_language(self, language: str) -> 'TranscriptionServiceBuilder':
        """Set the language"""
        self.language = language
        return self
    
    def with_word_timestamps(self, enabled: bool) -> 'TranscriptionServiceBuilder':
        """Set word timestamps option"""
        self.word_timestamps = enabled
        return self
    
    def with_vad(self, enabled: bool) -> 'TranscriptionServiceBuilder':
        """Set Voice Activity Detection option"""
        self.vad_enabled = enabled
        return self
    
    def build(self) -> Optional[TranscriptionServiceInterface]:
        """
        Build the transcription service
        
        Returns:
            Configured service instance or None if build fails
        """
        try:
            # Validate required parameters
            if not self.service_type:
                logger.error("Service type is required")
                return None
            
            if not self.factory.validate_service_type(self.service_type):
                logger.error(f"Invalid service type: {self.service_type}")
                return None
            
            # Prepare constructor arguments
            kwargs = {}
            if self.config:
                kwargs['config'] = self.config
            if self.model:
                kwargs['model'] = self.model
            if self.engine:
                kwargs['engine'] = self.engine
            
            # Create service instance
            service = self.factory.create_service(self.service_type, **kwargs)
            
            if service:
                logger.info(f"Built transcription service: {self.service_type}")
                return service
            else:
                logger.error(f"Failed to build transcription service: {self.service_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error building transcription service: {e}")
            return None
    
    def validate(self) -> Optional[ErrorInfo]:
        """
        Validate the builder configuration
        
        Returns:
            ErrorInfo if validation fails, None if valid
        """
        if not self.service_type:
            return ErrorInfo(
                code="MISSING_SERVICE_TYPE",
                message="Service type is required",
                timestamp=datetime.now()
            )
        
        if not self.factory.validate_service_type(self.service_type):
            return ErrorInfo(
                code="INVALID_SERVICE_TYPE",
                message=f"Invalid service type: {self.service_type}",
                timestamp=datetime.now()
            )
        
        return None
