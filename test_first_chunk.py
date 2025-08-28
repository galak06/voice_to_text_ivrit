#!/usr/bin/env python3
"""
Test script to process just the first chunk and compare results
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.config_manager import ConfigManager
from src.core.engines.utilities.cleanup_manager import CleanupManager

def test_first_chunk():
    """Test processing of just the first chunk"""
    try:
        print("🧪 Testing first chunk processing...")
        
        # Initialize configuration
        config_file = "config/environments/production.json"
        env_name = Path(config_file).stem
        from src.models.environment import Environment
        environment = Environment(env_name) if hasattr(Environment, env_name.upper()) else Environment.PRODUCTION
        config_manager = ConfigManager(str(Path(config_file).parent), environment=environment)
        
        # Create cleanup manager and inject it
        cleanup_manager = CleanupManager(config_manager)
        
        # Initialize application with injected dependencies
        app = TranscriptionApplication(
            config_manager=config_manager,
            cleanup_manager=cleanup_manager
        )
        
        # Set default values from production config
        default_model = "ivrit-ai/whisper-large-v3-ct2"
        default_engine = "ctranslate2-whisper"
        
        print(f"🚀 Processing with model: {default_model}")
        print(f"🔧 Engine: {default_engine}")
        print("-" * 60)
        
        # Run transcription
        with app:
            result = app.process_single_file(
                "examples/audio/voice/פגישה שלישית.wav", 
                model=default_model, 
                engine=default_engine
            )
            
            print("📊 RESULT STRUCTURE:")
            print("=" * 60)
            print(f"Success: {result.get('success')}")
            print(f"Keys: {list(result.keys())}")
            
            if result.get('transcription'):
                print(f"\nTranscription keys: {list(result['transcription'].keys())}")
                if result['transcription'].get('segments'):
                    print(f"Segments: {result['transcription']['segments']}")
            
            print("=" * 60)
            
            return result
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_first_chunk()
