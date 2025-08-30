#!/usr/bin/env python3
"""
Simple Speaker Recognition Test
Tests basic functionality without heavy processing
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic functionality without heavy processing"""
    logger.info("🧪 Testing basic functionality...")
    
    # Test 1: Environment
    hf_token = os.getenv('HF_TOKEN')
    if hf_token:
        logger.info(f"✅ HF_TOKEN found (length: {len(hf_token)})")
    else:
        logger.warning("⚠️ HF_TOKEN not found")
    
    # Test 2: File access
    test_file = "examples/audio/test/test_1min.wav"
    if os.path.exists(test_file):
        size_mb = os.path.getsize(test_file) / (1024 * 1024)
        logger.info(f"✅ Test file found: {test_file} ({size_mb:.1f} MB)")
    else:
        logger.error(f"❌ Test file not found: {test_file}")
        return False
    
    # Test 3: Import pyannote.audio (without processing)
    try:
        logger.info("🔄 Testing pyannote.audio import...")
        from pyannote.audio import Pipeline
        logger.info("✅ Pyannote.audio imported successfully")
        
        # Test 4: Create pipeline (without processing)
        logger.info("🔄 Testing pipeline creation...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization@2.1",
            use_auth_token=hf_token
        )
        logger.info("✅ Pipeline created successfully")
        
        # Test 5: Configure pipeline
        logger.info("🔄 Testing pipeline configuration...")
        pipeline.instantiate({
            'segmentation': {
                'threshold': 0.5,
                'min_duration_off': 0.5
            },
            'clustering': {
                'threshold': 0.7,
                'method': 'centroid',
                'min_cluster_size': 15
            }
        })
        logger.info("✅ Pipeline configured successfully")
        
        # Test 6: Mock processing (skip actual audio processing)
        logger.info("🧪 Testing mock processing...")
        time.sleep(1)  # Simulate processing
        
        # Create mock results
        class MockTurn:
            def __init__(self, start, end):
                self.start = start
                self.end = end
        
        class MockDiarization:
            def itertracks(self, yield_label=True):
                mock_turns = [
                    (MockTurn(0, 30), None, "SPEAKER_00"),
                    (MockTurn(30, 60), None, "SPEAKER_01"),
                ]
                for turn in mock_turns:
                    yield turn
        
        diarization = MockDiarization()
        
        # Process mock results
        speakers = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker not in speakers:
                speakers[speaker] = []
            speakers[speaker].append({
                'start': turn.start,
                'end': turn.end,
                'duration': turn.end - turn.start
            })
        
        logger.info(f"✅ Mock processing completed: {len(speakers)} speakers detected")
        for speaker_id, segments in speakers.items():
            total_duration = sum(seg['duration'] for seg in segments)
            logger.info(f"   🎤 {speaker_id}: {len(segments)} segments, {total_duration}s total")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Simple Speaker Recognition Test Starting")
    logger.info("=" * 50)
    
    success = test_basic_functionality()
    
    logger.info("=" * 50)
    if success:
        logger.info("✅ All basic tests passed!")
        logger.info("💡 The script structure is working correctly")
        logger.info("🔧 The hanging issue is likely in the audio processing step")
    else:
        logger.info("❌ Some tests failed")
        logger.info("🔧 Check the error messages above")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
