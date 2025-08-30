#!/usr/bin/env python3
"""
Example of using the enhanced speaker service with dependency injection
"""

from src.utils.dependency_injection import DependencyContainer, SpeakerServiceInjector
from src.utils.config_manager import ConfigManager
from src.core.models.enhanced_speaker_service import EnhancedSpeakerService

def main():
    """Demonstrate dependency injection with enhanced speaker service"""
    
    # Create dependency container
    container = DependencyContainer()
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Create speaker service injector
    speaker_injector = SpeakerServiceInjector(container)
    
    # Create enhanced speaker service with full injection
    speaker_service = speaker_injector.create_enhanced_speaker_service(
        config_manager=config_manager,
        transcription_engine=None,  # Will be injected later
        custom_parameter="value"    # Additional injected dependency
    )
    
    # Use the service
    result = speaker_service.speaker_diarization("audio.wav", chunk_duration=30)
    
    print(f"Speaker service created successfully: {type(speaker_service).__name__}")
    print(f"Processing result: {result.success}")

if __name__ == "__main__":
    main()
