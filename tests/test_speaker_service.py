#!/usr/bin/env python3
"""
Test script for SpeakerTranscriptionService class
Demonstrates different configurations and usage patterns
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.speaker_transcription_service import SpeakerTranscriptionService, SpeakerConfig

def test_default_configuration():
    """Test with default configuration"""
    print("🧪 Testing Default Configuration")
    print("=" * 50)
    
    # Create service with default config
    service = SpeakerTranscriptionService()
    
    # Test transcription
    result = service.speaker_diarization(
        "examples/audio/voice/rachel_1.wav",
        "test-model",
        save_output=True
    )
    
    if result.success:
        print("✅ Default configuration test passed")
        print(f"   Speakers detected: {result.speaker_count}")
        print(f"   Transcription time: {result.transcription_time:.2f}s")
    else:
        print(f"❌ Default configuration test failed: {result.error_message}")
    
    return result.success

def test_custom_configuration():
    """Test with custom configuration"""
    print("\n🧪 Testing Custom Configuration")
    print("=" * 50)
    
    # Create custom configuration
    custom_config = SpeakerConfig(
        min_speakers=1,
        max_speakers=3,
        silence_threshold=1.5,  # More sensitive to speaker changes
        vad_enabled=True,
        word_timestamps=True,
        language="he",
        beam_size=3,  # Faster but less accurate
        vad_min_silence_duration_ms=300
    )
    
    # Create service with custom config
    service = SpeakerTranscriptionService(custom_config)
    
    # Test transcription
    result = service.speaker_diarization(
        "examples/audio/voice/rachel_1.wav",
        "test-model",
        save_output=True
    )
    
    if result.success:
        print("✅ Custom configuration test passed")
        print(f"   Speakers detected: {result.speaker_count}")
        print(f"   Transcription time: {result.transcription_time:.2f}s")
        print(f"   Config used: min_speakers={custom_config.min_speakers}, max_speakers={custom_config.max_speakers}")
    else:
        print(f"❌ Custom configuration test failed: {result.error_message}")
    
    return result.success

def test_conversation_configuration():
    """Test configuration optimized for conversations"""
    print("\n🧪 Testing Conversation Configuration")
    print("=" * 50)
    
    # Configuration optimized for conversations
    conversation_config = SpeakerConfig(
        min_speakers=2,
        max_speakers=6,
        silence_threshold=1.0,  # Very sensitive to speaker changes
        vad_enabled=True,
        word_timestamps=True,
        language="he",
        beam_size=5,
        vad_min_silence_duration_ms=200
    )
    
    # Create service with conversation config
    service = SpeakerTranscriptionService(conversation_config)
    
    # Test transcription
    result = service.speaker_diarization(
        "examples/audio/voice/rachel_1.wav",
        "test-model",
        save_output=True
    )
    
    if result.success:
        print("✅ Conversation configuration test passed")
        print(f"   Speakers detected: {result.speaker_count}")
        print(f"   Transcription time: {result.transcription_time:.2f}s")
        print(f"   Config used: silence_threshold={conversation_config.silence_threshold}s")
    else:
        print(f"❌ Conversation configuration test failed: {result.error_message}")
    
    return result.success

def test_interview_configuration():
    """Test configuration optimized for interviews"""
    print("\n🧪 Testing Interview Configuration")
    print("=" * 50)
    
    # Configuration optimized for interviews
    interview_config = SpeakerConfig(
        min_speakers=2,
        max_speakers=4,
        silence_threshold=2.5,  # Less sensitive, allows for thinking pauses
        vad_enabled=True,
        word_timestamps=True,
        language="he",
        beam_size=7,  # Higher accuracy for interviews
        vad_min_silence_duration_ms=800
    )
    
    # Create service with interview config
    service = SpeakerTranscriptionService(interview_config)
    
    # Test transcription
    result = service.speaker_diarization(
        "examples/audio/voice/rachel_1.wav",
        "test-model",
        save_output=True
    )
    
    if result.success:
        print("✅ Interview configuration test passed")
        print(f"   Speakers detected: {result.speaker_count}")
        print(f"   Transcription time: {result.transcription_time:.2f}s")
        print(f"   Config used: beam_size={interview_config.beam_size}, silence_threshold={interview_config.silence_threshold}s")
    else:
        print(f"❌ Interview configuration test failed: {result.error_message}")
    
    return result.success

def demonstrate_configuration_options():
    """Demonstrate different configuration options"""
    print("\n📋 Configuration Options Demonstration")
    print("=" * 50)
    
    print("Available configuration parameters:")
    print()
    
    # Show default config
    default_config = SpeakerConfig()
    print("🔧 Default Configuration:")
    print(f"   min_speakers: {default_config.min_speakers}")
    print(f"   max_speakers: {default_config.max_speakers}")
    print(f"   silence_threshold: {default_config.silence_threshold}s")
    print(f"   vad_enabled: {default_config.vad_enabled}")
    print(f"   word_timestamps: {default_config.word_timestamps}")
    print(f"   language: {default_config.language}")
    print(f"   beam_size: {default_config.beam_size}")
    print(f"   vad_min_silence_duration_ms: {default_config.vad_min_silence_duration_ms}")
    print()
    
    print("🎯 Use Cases:")
    print("   • Default: Balanced for most scenarios")
    print("   • Conversation: Sensitive to quick speaker changes")
    print("   • Interview: Allows for thinking pauses")
    print("   • Custom: Tailored to specific needs")
    print()
    
    print("⚙️  Key Parameters:")
    print("   • silence_threshold: Time gap to detect speaker change")
    print("   • beam_size: Higher = more accurate but slower")
    print("   • min_speakers/max_speakers: Speaker count constraints")
    print("   • vad_min_silence_duration_ms: Voice activity detection sensitivity")

def main():
    """Run all tests"""
    print("🎤 Speaker Transcription Service Tests")
    print("=" * 60)
    
    results = []
    
    # Test different configurations
    results.append(test_default_configuration())
    results.append(test_custom_configuration())
    results.append(test_conversation_configuration())
    results.append(test_interview_configuration())
    
    # Demonstrate configuration options
    demonstrate_configuration_options()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! SpeakerTranscriptionService is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 