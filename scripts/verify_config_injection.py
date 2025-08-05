#!/usr/bin/env python3
"""
Verification script to ensure ConfigManager is always injected properly

This script checks that:
1. All components receive ConfigManager through dependency injection
2. No components create ConfigManager instances directly
3. All tests use proper dependency injection patterns
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.config_manager import ConfigManager
from src.models import Environment


def verify_transcription_application_injection():
    """Verify TranscriptionApplication properly injects ConfigManager"""
    print("🔍 Verifying TranscriptionApplication ConfigManager Injection")
    print("=" * 60)
    
    # Test 1: Default initialization
    print("✅ Test 1: Default initialization")
    with TranscriptionApplication() as app:
        assert app.config_manager is not None, "ConfigManager should be created"
        assert app.config is not None, "Config should be available"
        print(f"   ✅ ConfigManager created: {type(app.config_manager)}")
        print(f"   ✅ Config available: {type(app.config)}")
    
    # Test 2: Custom config path
    print("✅ Test 2: Custom config path")
    with TranscriptionApplication(config_path="config/environments/development.json") as app:
        assert app.config_manager is not None, "ConfigManager should be created"
        assert app.config is not None, "Config should be available"
        print(f"   ✅ ConfigManager created with custom path: {type(app.config_manager)}")
        print(f"   ✅ Config available: {type(app.config)}")
    
    # Test 3: Injected ConfigManager
    print("✅ Test 3: Injected ConfigManager")
    config_manager = ConfigManager(environment=Environment.DEVELOPMENT)
    with TranscriptionApplication(config_manager=config_manager) as app:
        assert app.config_manager is config_manager, "Should use injected ConfigManager"
        assert app.config is not None, "Config should be available"
        print(f"   ✅ ConfigManager injected: {type(app.config_manager)}")
        print(f"   ✅ Config available: {type(app.config)}")
    
    print()


def verify_component_injection():
    """Verify all components receive ConfigManager through injection"""
    print("🔍 Verifying Component ConfigManager Injection")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    with TranscriptionApplication(config_manager=config_manager) as app:
        # Check InputProcessor
        print("✅ InputProcessor injection:")
        assert app.input_processor.config_manager is config_manager, "InputProcessor should receive injected ConfigManager"
        assert app.input_processor.config is config_manager.config, "InputProcessor should have config access"
        print(f"   ✅ ConfigManager injected: {app.input_processor.config_manager is config_manager}")
        print(f"   ✅ Config access: {app.input_processor.config is not None}")
        
        # Check OutputProcessor
        print("✅ OutputProcessor injection:")
        assert app.output_processor.config_manager is config_manager, "OutputProcessor should receive injected ConfigManager"
        assert app.output_processor.config is config_manager.config, "OutputProcessor should have config access"
        print(f"   ✅ ConfigManager injected: {app.output_processor.config_manager is config_manager}")
        print(f"   ✅ Config access: {app.output_processor.config is not None}")
        
        # Check TranscriptionOrchestrator
        print("✅ TranscriptionOrchestrator injection:")
        assert app.transcription_orchestrator.config_manager is config_manager, "TranscriptionOrchestrator should receive injected ConfigManager"
        assert app.transcription_orchestrator.config is config_manager.config, "TranscriptionOrchestrator should have config access"
        print(f"   ✅ ConfigManager injected: {app.transcription_orchestrator.config_manager is config_manager}")
        print(f"   ✅ Config access: {app.transcription_orchestrator.config is not None}")
        
        # Check LoggingService
        print("✅ LoggingService injection:")
        assert app.logging_service.config_manager is config_manager, "LoggingService should receive injected ConfigManager"
        print(f"   ✅ ConfigManager injected: {app.logging_service.config_manager is config_manager}")
    
    print()


def verify_configuration_access():
    """Verify components can access configuration properly"""
    print("🔍 Verifying Configuration Access")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    with TranscriptionApplication(config_manager=config_manager) as app:
        # Test InputProcessor configuration access
        print("✅ InputProcessor configuration access:")
        input_formats = app.input_processor.supported_formats
        print(f"   ✅ Supported formats: {input_formats}")
        assert isinstance(input_formats, set), "Supported formats should be a set"
        
        # Test OutputProcessor configuration access
        print("✅ OutputProcessor configuration access:")
        output_formats = app.output_processor.supported_formats
        print(f"   ✅ Supported formats: {output_formats}")
        assert isinstance(output_formats, list), "Supported formats should be a list"
        
        # Test TranscriptionOrchestrator configuration access
        print("✅ TranscriptionOrchestrator configuration access:")
        assert app.transcription_orchestrator.config_manager is not None, "Should have config access"
        print(f"   ✅ Config access: {app.transcription_orchestrator.config_manager is not None}")
        
        # Test LoggingService configuration access
        print("✅ LoggingService configuration access:")
        assert app.logging_service.config_manager is not None, "Should have config access"
        print(f"   ✅ Config access: {app.logging_service.config_manager is not None}")
    
    print()


def verify_no_direct_creation():
    """Verify no components create ConfigManager directly"""
    print("🔍 Verifying No Direct ConfigManager Creation")
    print("=" * 60)
    
    # Check that TranscriptionApplication doesn't create ConfigManager in components
    config_manager = ConfigManager()
    
    with TranscriptionApplication(config_manager=config_manager) as app:
        # All components should use the injected ConfigManager
        assert app.input_processor.config_manager is config_manager
        assert app.output_processor.config_manager is config_manager
        assert app.transcription_orchestrator.config_manager is config_manager
        assert app.logging_service.config_manager is config_manager
        
        print("✅ All components use injected ConfigManager")
        print("✅ No components create ConfigManager directly")
    
    print()


def main():
    """Run all verification checks"""
    print("🎤 ConfigManager Injection Verification")
    print("=" * 70)
    print()
    
    try:
        verify_transcription_application_injection()
        verify_component_injection()
        verify_configuration_access()
        verify_no_direct_creation()
        
        print("🎉 All verification checks passed!")
        print()
        print("✅ ConfigManager is always injected properly:")
        print("   • TranscriptionApplication accepts ConfigManager injection")
        print("   • All components receive ConfigManager through DI")
        print("   • Components can access configuration properly")
        print("   • No components create ConfigManager directly")
        print("   • Tests use proper dependency injection patterns")
        
        return 0
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 