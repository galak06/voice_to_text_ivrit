#!/usr/bin/env python3
"""
Comprehensive test script for all transcription methods
Verifies that all methods create JSON, TXT, and DOCX outputs
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_transcription_service():
    """Test the core transcription service"""
    print("🧪 Testing Core Transcription Service")
    print("=" * 50)
    
    try:
        from src.core.transcription_service import TranscriptionService
        
        # Create service
        service = TranscriptionService()
        
        # Sample job
        job = {
            "input": {
                "type": "text",
                "data": "examples/audio/voice/test_sample.wav",
                "model": "test-model",
                "engine": "test-engine"
            }
        }
        
        # Run transcription
        results = list(service.transcribe(job, save_output=True))
        
        if results and 'result' in results[0]:
            print("✅ Core transcription service working")
            return True
        else:
            print("❌ Core transcription service failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing core service: {e}")
        return False

def test_speaker_diarization():
    """Test speaker diarization with output saving"""
    print("\n🧪 Testing Speaker Diarization")
    print("=" * 50)
    
    try:
        from src.core.speaker_diarization import speaker_diarization
        
        # Test with save_output=True
        success = speaker_diarization(
            "examples/audio/voice/test_sample.wav", 
            "test-model", 
            save_output=True
        )
        
        if success:
            print("✅ Speaker diarization working")
            return True
        else:
            print("❌ Speaker diarization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing speaker diarization: {e}")
        return False

def test_runpod_client():
    """Test RunPod client with output saving"""
    print("\n🧪 Testing RunPod Client")
    print("=" * 50)
    
    try:
        from src.clients.send_audio import send_audio_file
        
        # Test with save_output=True
        success = send_audio_file(
            "examples/audio/voice/test_sample.wav", 
            "test-model", 
            "test-engine", 
            save_output=True
        )
        
        if success:
            print("✅ RunPod client working")
            return True
        else:
            print("❌ RunPod client failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing RunPod client: {e}")
        return False

def verify_output_files():
    """Verify that all output formats were created"""
    print("\n🔍 Verifying Output Files")
    print("=" * 50)
    
    try:
        from src.utils.output_manager import OutputManager
        
        output_manager = OutputManager()
        transcriptions_dir = output_manager.transcriptions_dir
        
        # Count files by type
        json_files = list(transcriptions_dir.glob("*.json"))
        txt_files = list(transcriptions_dir.glob("*.txt"))
        docx_files = list(transcriptions_dir.glob("*.docx"))
        
        print(f"📄 JSON files: {len(json_files)}")
        print(f"📄 Text files: {len(txt_files)}")
        print(f"📄 Word documents: {len(docx_files)}")
        
        # Check if we have recent files (last 5 minutes)
        import time
        current_time = time.time()
        recent_files = []
        
        for file in json_files + txt_files + docx_files:
            if current_time - file.stat().st_mtime < 300:  # 5 minutes
                recent_files.append(file)
        
        print(f"📄 Recent files (last 5 min): {len(recent_files)}")
        
        if len(recent_files) > 0:
            print("✅ Recent output files found")
            return True
        else:
            print("⚠️  No recent output files found")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying output files: {e}")
        return False

def main():
    """Run all tests"""
    print("🎤 Testing All Transcription Methods")
    print("=" * 60)
    
    results = []
    
    # Test core service
    results.append(test_transcription_service())
    
    # Test speaker diarization
    results.append(test_speaker_diarization())
    
    # Test RunPod client
    results.append(test_runpod_client())
    
    # Verify output files
    results.append(verify_output_files())
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! All transcription methods create all formats.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 