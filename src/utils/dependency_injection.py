#!/usr/bin/env python3
"""
Dependency Injection Container for the application
Follows SOLID principles with proper dependency management
"""

import logging
from typing import Dict, Any, Optional, Type
from src.core.interfaces.transcription_protocols import SpeakerServiceProtocol
from src.core.models.enhanced_speaker_service import EnhancedSpeakerService

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency injection container that manages service creation and injection
    
    This follows the Dependency Inversion Principle (DIP) from SOLID principles
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_service(self, service_name: str, service_class: Type, **dependencies) -> None:
        """
        Register a service class with its dependencies
        
        Args:
            service_name: Name to register the service under
            service_class: Class to instantiate
            **dependencies: Dependencies to inject
        """
        self._factories[service_name] = (service_class, dependencies)
        logger.info(f"�� Registered service: {service_name} -> {service_class.__name__}")
    
    def register_singleton(self, service_name: str, service_class: Type, **dependencies) -> None:
        """
        Register a singleton service that will be created once
        
        Args:
            service_name: Name to register the service under
            service_class: Class to instantiate
            **dependencies: Dependencies to inject
        """
        self._factories[service_name] = (service_class, dependencies)
        self._singletons[service_name] = None
        logger.info(f"🔧 Registered singleton: {service_name} -> {service_class.__name__}")
    
    def get_service(self, service_name: str, **additional_dependencies) -> Any:
        """
        Get a service instance with dependency injection
        
        Args:
            service_name: Name of the service to retrieve
            **additional_dependencies: Additional dependencies to inject
            
        Returns:
            Service instance
        """
        if service_name not in self._factories:
            raise ValueError(f"Service '{service_name}' not registered")
        
        # Check if singleton already exists
        if service_name in self._singletons and self._singletons[service_name] is not None:
            return self._singletons[service_name]
        
        # Get factory and dependencies
        service_class, dependencies = self._factories[service_name]
        
        # Merge dependencies
        all_dependencies = {**dependencies, **additional_dependencies}
        
        # Create service instance
        try:
            service_instance = service_class(**all_dependencies)
            
            # Store singleton if applicable
            if service_name in self._singletons:
                self._singletons[service_name] = service_instance
            
            logger.info(f"✅ Created service instance: {service_name}")
            return service_instance
            
        except Exception as e:
            logger.error(f"❌ Failed to create service '{service_name}': {e}")
            raise
    
    def inject_dependencies(self, target_object: Any, **dependencies) -> None:
        """
        Inject dependencies into an existing object
        
        Args:
            target_object: Object to inject dependencies into
            **dependencies: Dependencies to inject
        """
        for attr_name, dependency in dependencies.items():
            if hasattr(target_object, attr_name):
                setattr(target_object, attr_name, dependency)
                logger.info(f"💉 Injected dependency '{attr_name}' into {type(target_object).__name__}")
            else:
                logger.warning(f"⚠️ Cannot inject '{attr_name}' - attribute not found on {type(target_object).__name__}")


class SpeakerServiceInjector:
    """
    Specialized injector for speaker services with proper dependency management
    """
    
    def __init__(self, container: DependencyContainer):
        self.container = container
    
    def create_enhanced_speaker_service(self, config_manager, transcription_engine=None, **kwargs) -> EnhancedSpeakerService:
        """
        Create enhanced speaker service with full dependency injection
        
        Args:
            config_manager: Configuration manager instance
            transcription_engine: Transcription engine to inject
            **kwargs: Additional dependencies
            
        Returns:
            EnhancedSpeakerService instance
        """
        # Register the service if not already registered
        service_name = "enhanced_speaker_service"
        
        if service_name not in self.container._factories:
            self.container.register_service(
                service_name,
                EnhancedSpeakerService,
                config_manager=config_manager,
                transcription_engine=transcription_engine,
                **kwargs
            )
        
        # Get the service instance
        return self.container.get_service(service_name)
    
    def inject_into_transcription_service(self, transcription_service, speaker_service: SpeakerServiceProtocol) -> None:
        """
        Inject speaker service into transcription service
        
        Args:
            transcription_service: Transcription service to inject into
            speaker_service: Speaker service to inject
        """
        self.container.inject_dependencies(
            transcription_service,
            speaker_service=speaker_service
        )
