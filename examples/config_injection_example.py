#!/usr/bin/env python3
"""
Example demonstrating ConfigManager injection in TranscriptionApplication

This example shows different ways to initialize the TranscriptionApplication
with ConfigManager dependency injection.
"""

from src.core.application import TranscriptionApplication
from src.utils.config_manager import ConfigManager
from src.models import Environment


def example_default_config():
    """Example using default configuration"""
    print("🔧 Example 1: Default Configuration")
    print("=" * 50)
    
    # Uses default ConfigManager (loads from config/ directory)
    with TranscriptionApplication() as app:
        print(f"✅ Application initialized with default config")
        print(f"   Environment: {app.config_manager.environment}")
        print(f"   Config directory: {app.config_manager.config_dir}")
        print(f"   Session ID: {app.current_session_id}")
        print()


def example_custom_config_path():
    """Example using custom configuration path"""
    print("🔧 Example 2: Custom Configuration Path")
    print("=" * 50)
    
    # Uses custom config path
    with TranscriptionApplication(config_path="config/environments/development.json") as app:
        print(f"✅ Application initialized with custom config path")
        print(f"   Environment: {app.config_manager.environment}")
        print(f"   Config directory: {app.config_manager.config_dir}")
        print(f"   Session ID: {app.current_session_id}")
        print()


def example_injected_config_manager():
    """Example using injected ConfigManager"""
    print("🔧 Example 3: Injected ConfigManager")
    print("=" * 50)
    
    # Create custom ConfigManager
    config_manager = ConfigManager(
        config_dir="config",
        environment=Environment.DEVELOPMENT
    )
    
    # Inject the ConfigManager
    with TranscriptionApplication(config_manager=config_manager) as app:
        print(f"✅ Application initialized with injected ConfigManager")
        print(f"   Environment: {app.config_manager.environment}")
        print(f"   Config directory: {app.config_manager.config_dir}")
        print(f"   Session ID: {app.current_session_id}")
        print()


def example_config_validation():
    """Example showing configuration validation"""
    print("🔧 Example 4: Configuration Validation")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    # Validate configuration
    if config_manager.validate():
        print("✅ Configuration is valid")
        
        # Print configuration summary
        print("\n📋 Configuration Summary:")
        print(f"   Transcription Model: {config_manager.config.transcription.default_model}")
        print(f"   Transcription Engine: {config_manager.config.transcription.default_engine}")
        print(f"   Output Directory: {config_manager.config.output.output_dir}")
        print(f"   Min Speakers: {config_manager.config.speaker.min_speakers}")
        print(f"   Max Speakers: {config_manager.config.speaker.max_speakers}")
        print(f"   Debug Mode: {config_manager.config.system.debug}")
    else:
        print("❌ Configuration validation failed")
    print()


def example_component_config_access():
    """Example showing how components access configuration"""
    print("🔧 Example 5: Component Configuration Access")
    print("=" * 50)
    
    with TranscriptionApplication() as app:
        print("✅ Application components have full config access:")
        
        # InputProcessor configuration
        input_formats = app.input_processor.supported_formats
        print(f"   InputProcessor supported formats: {input_formats}")
        
        # OutputProcessor configuration
        output_formats = app.output_processor.supported_formats
        print(f"   OutputProcessor supported formats: {output_formats}")
        
        # TranscriptionOrchestrator configuration
        print(f"   TranscriptionOrchestrator has config access: {app.transcription_orchestrator.config_manager is not None}")
        
        # LoggingService configuration
        print(f"   LoggingService has config access: {app.logging_service.config_manager is not None}")
        print()


def main():
    """Run all examples"""
    print("🎤 TranscriptionApplication ConfigManager Injection Examples")
    print("=" * 70)
    print()
    
    try:
        example_default_config()
        example_custom_config_path()
        example_injected_config_manager()
        example_config_validation()
        example_component_config_access()
        
        print("🎉 All examples completed successfully!")
        print()
        print("💡 Key Benefits of ConfigManager Injection:")
        print("   • Flexible configuration management")
        print("   • Easy testing with mock ConfigManager")
        print("   • Environment-specific configurations")
        print("   • All components have full config access")
        print("   • Better separation of concerns")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 