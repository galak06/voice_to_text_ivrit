#!/usr/bin/env python3
"""
Test script for the new configuration system
Tests base, development, and production configurations
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_manager import ConfigManager, Environment

def test_base_configuration():
    """Test base configuration"""
    print("🧪 Testing Base Configuration")
    print("=" * 50)
    
    # Set environment to base
    os.environ['ENVIRONMENT'] = 'base'
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    print(f"Environment: {config.environment.value}")
    print(f"Default Model: {config.transcription.default_model}")
    print(f"Beam Size: {config.transcription.beam_size}")
    print(f"Debug Mode: {config.system.debug}")
    print(f"Log Level: {config.output.log_level}")
    
    return True

def test_development_configuration():
    """Test development configuration"""
    print("\n🧪 Testing Development Configuration")
    print("=" * 50)
    
    # Set environment to development
    os.environ['ENVIRONMENT'] = 'development'
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    print(f"Environment: {config.environment.value}")
    print(f"Default Model: {config.transcription.default_model}")
    print(f"Beam Size: {config.transcription.beam_size}")
    print(f"Debug Mode: {config.system.debug}")
    print(f"Log Level: {config.output.log_level}")
    print(f"Timeout: {config.system.timeout_seconds}s")
    
    # Verify development-specific settings
    assert config.system.debug == True, "Development should have debug enabled"
    assert config.system.dev_mode == True, "Development should have dev_mode enabled"
    assert config.output.log_level == "DEBUG", "Development should have DEBUG log level"
    
    return True

def test_production_configuration():
    """Test production configuration"""
    print("\n🧪 Testing Production Configuration")
    print("=" * 50)
    
    # Set environment to production
    os.environ['ENVIRONMENT'] = 'production'
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    print(f"Environment: {config.environment.value}")
    print(f"Default Model: {config.transcription.default_model}")
    print(f"Beam Size: {config.transcription.beam_size}")
    print(f"Debug Mode: {config.system.debug}")
    print(f"Log Level: {config.output.log_level}")
    print(f"Max Workers: {config.system.max_workers}")
    print(f"Timeout: {config.system.timeout_seconds}s")
    
    # Verify production-specific settings
    assert config.system.debug == False, "Production should have debug disabled"
    assert config.system.dev_mode == False, "Production should have dev_mode disabled"
    assert config.output.log_level == "WARNING", "Production should have WARNING log level"
    assert config.transcription.beam_size == 7, "Production should have higher beam size"
    
    return True

def test_environment_variable_override():
    """Test environment variable overrides"""
    print("\n🧪 Testing Environment Variable Overrides")
    print("=" * 50)
    
    # Set environment to base
    os.environ['ENVIRONMENT'] = 'base'
    
    # Override with environment variables
    os.environ['DEFAULT_MODEL'] = 'test-model-override'
    os.environ['DEBUG'] = 'true'
    os.environ['LOG_LEVEL'] = 'ERROR'
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    print(f"Default Model: {config.transcription.default_model}")
    print(f"Debug Mode: {config.system.debug}")
    print(f"Log Level: {config.output.log_level}")
    
    # Verify overrides
    assert config.transcription.default_model == 'test-model-override', "Environment variable should override default model"
    assert config.system.debug == True, "Environment variable should override debug setting"
    assert config.output.log_level == "ERROR", "Environment variable should override log level"
    
    # Clean up
    del os.environ['DEFAULT_MODEL']
    del os.environ['DEBUG']
    del os.environ['LOG_LEVEL']
    
    return True

def test_configuration_validation():
    """Test configuration validation"""
    print("\n🧪 Testing Configuration Validation")
    print("=" * 50)
    
    # Test without required variables
    os.environ['ENVIRONMENT'] = 'base'
    if 'RUNPOD_API_KEY' in os.environ:
        del os.environ['RUNPOD_API_KEY']
    if 'RUNPOD_ENDPOINT_ID' in os.environ:
        del os.environ['RUNPOD_ENDPOINT_ID']
    
    config_manager = ConfigManager()
    is_valid = config_manager.validate()
    
    print(f"Configuration valid: {is_valid}")
    
    # Test with required variables
    os.environ['RUNPOD_API_KEY'] = 'test-key'
    os.environ['RUNPOD_ENDPOINT_ID'] = 'test-endpoint'
    
    config_manager = ConfigManager()
    is_valid = config_manager.validate()
    
    print(f"Configuration valid (with vars): {is_valid}")
    
    # Clean up
    del os.environ['RUNPOD_API_KEY']
    del os.environ['RUNPOD_ENDPOINT_ID']
    
    return True

def test_speaker_config_integration():
    """Test speaker configuration integration"""
    print("\n🧪 Testing Speaker Configuration Integration")
    print("=" * 50)
    
    os.environ['ENVIRONMENT'] = 'base'
    config_manager = ConfigManager()
    
    # Test getting speaker config
    speaker_config = config_manager.get_speaker_config("default")
    print(f"Default speaker config - min_speakers: {speaker_config.min_speakers}")
    print(f"Default speaker config - max_speakers: {speaker_config.max_speakers}")
    
    speaker_config = config_manager.get_speaker_config("conversation")
    print(f"Conversation speaker config - silence_threshold: {speaker_config.silence_threshold}")
    
    return True

def demonstrate_configuration_structure():
    """Demonstrate the configuration structure"""
    print("\n📋 Configuration Structure Demonstration")
    print("=" * 50)
    
    os.environ['ENVIRONMENT'] = 'base'
    config_manager = ConfigManager()
    config = config_manager.config
    
    print("🔧 Configuration Sections:")
    print("   • Transcription - Engine and model settings")
    print("   • Speaker - Speaker diarization settings")
    print("   • RunPod - Cloud service settings")
    print("   • Output - File and logging settings")
    print("   • System - Performance and debug settings")
    print()
    
    print("🌍 Environment Support:")
    print("   • base.json - Base configuration")
    print("   • development.json - Development overrides")
    print("   • production.json - Production overrides")
    print()
    
    print("⚙️  Environment Variable Overrides:")
    print("   • DEFAULT_MODEL - Override default model")
    print("   • DEBUG - Enable/disable debug mode")
    print("   • LOG_LEVEL - Set logging level")
    print("   • RUNPOD_API_KEY - Set API key")
    print("   • RUNPOD_ENDPOINT_ID - Set endpoint ID")

def main():
    """Run all configuration tests"""
    print("🔧 Configuration System Tests")
    print("=" * 60)
    
    results = []
    
    # Test different environments
    results.append(test_base_configuration())
    results.append(test_development_configuration())
    results.append(test_production_configuration())
    
    # Test environment variable overrides
    results.append(test_environment_variable_override())
    
    # Test validation
    results.append(test_configuration_validation())
    
    # Test speaker config integration
    results.append(test_speaker_config_integration())
    
    # Demonstrate structure
    demonstrate_configuration_structure()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All configuration tests passed!")
        print("The new configuration system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 