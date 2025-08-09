#!/usr/bin/env python3
"""
Test script to run each transcription engine with base model and validate results
"""

import os
import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.engines.speaker_engines import TranscriptionEngineFactory
from src.models.speaker_models import SpeakerConfig
from src.utils.config_manager import ConfigManager

def create_test_config():
    """Create a test configuration for engine testing"""
    config = SpeakerConfig(
        min_speakers=1,
        max_speakers=2,
        silence_threshold=0.5,
        vad_enabled=True,
        chunk_duration=30.0,
        overlap_duration=2.0,
        language="en"
    )
    return config

def validate_transcription_result(result, engine_name):
    """Validate transcription result structure and content"""
    print(f"\n🔍 Validating {engine_name} result...")
    
    # Check basic structure
    required_fields = ['success', 'speakers', 'full_text', 'transcription_time', 'model_name', 'audio_file', 'speaker_count']
    for field in required_fields:
        if not hasattr(result, field):
            print(f"❌ Missing required field: {field}")
            return False
    
    # Check success status
    if not result.success:
        print(f"❌ Transcription failed: {getattr(result, 'error_message', 'Unknown error')}")
        return False
    
    # Check transcription time
    if result.transcription_time <= 0:
        print(f"❌ Invalid transcription time: {result.transcription_time}")
        return False
    
    # Check model name
    if not result.model_name:
        print(f"❌ Missing model name")
        return False
    
    # Check audio file path
    if not result.audio_file:
        print(f"❌ Missing audio file path")
        return False
    
    # Check speaker count
    if result.speaker_count < 0:
        print(f"❌ Invalid speaker count: {result.speaker_count}")
        return False
    
    # Check speakers data
    if not isinstance(result.speakers, dict):
        print(f"❌ Speakers should be a dictionary, got: {type(result.speakers)}")
        return False
    
    # Check full text
    if not result.full_text or not result.full_text.strip():
        print(f"⚠️  Warning: Empty or missing transcription text")
        return False
    
    # Check metadata if present
    if hasattr(result, 'metadata') and result.metadata:
        if not isinstance(result.metadata, dict):
            print(f"❌ Metadata should be a dictionary, got: {type(result.metadata)}")
            return False
    
    print(f"✅ {engine_name} validation passed!")
    print(f"   📊 Transcription time: {result.transcription_time:.2f}s")
    print(f"   🎤 Speaker count: {result.speaker_count}")
    print(f"   📝 Text length: {len(result.full_text)} characters")
    print(f"   🔧 Model used: {result.model_name}")
    
    return True

def test_engine(engine_type, config, audio_file_path, model_name="base"):
    """Test a specific engine with the given configuration"""
    print(f"\n🚀 Testing {engine_type} engine with {model_name} model...")
    print(f"   📁 Audio file: {audio_file_path}")
    
    try:
        # Create engine
        engine = TranscriptionEngineFactory.create_engine(engine_type, config)
        
        # Check if engine is available
        if not engine.is_available():
            print(f"❌ {engine_type} engine is not available")
            return False
        
        print(f"✅ {engine_type} engine is available")
        
        # Run transcription
        start_time = time.time()
        result = engine.transcribe(audio_file_path, model_name)
        total_time = time.time() - start_time
        
        # Validate result
        if validate_transcription_result(result, engine_type):
            print(f"✅ {engine_type} test completed successfully in {total_time:.2f}s")
            return True
        else:
            print(f"❌ {engine_type} test failed validation")
            return False
            
    except Exception as e:
        print(f"❌ {engine_type} test failed with error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Starting Engine Testing Suite")
    print("=" * 50)
    
    # Setup
    audio_file_path = "examples/audio/voice/meeting_2.wav"
    
    # Check if audio file exists
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return
    
    print(f"📁 Using audio file: {audio_file_path}")
    print(f"📏 File size: {os.path.getsize(audio_file_path) / (1024*1024):.1f} MB")
    
    # Create test configuration
    config = create_test_config()
    print(f"⚙️  Test configuration created")
    
    # Define engines to test
    engines = [
        "stable-whisper",
        "custom-whisper", 
        "optimized-whisper"
    ]
    
    # Test results
    results = {}
    
    # Test each engine
    for engine_type in engines:
        print(f"\n{'='*60}")
        success = test_engine(engine_type, config, audio_file_path, "base")
        results[engine_type] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(engines)
    
    for engine_type, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{engine_type:20} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} engines passed")
    
    if passed == total:
        print("🎉 All engines working correctly!")
    else:
        print("⚠️  Some engines failed - check the logs above")
    
    # Save results to file
    results_file = "engine_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'audio_file': audio_file_path,
            'model': 'base',
            'results': results,
            'summary': {
                'passed': passed,
                'total': total,
                'success_rate': f"{passed/total*100:.1f}%"
            }
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")

if __name__ == "__main__":
    main()

