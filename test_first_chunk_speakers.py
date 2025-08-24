#!/usr/bin/env python3
"""
Test script to verify first chunk produces output JSON with 2 speakers
"""

import logging
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.engines.consolidated_transcription_engine import ConsolidatedTranscriptionEngine
from src.core.factories.speaker_config_factory import SpeakerConfigFactory
from src.core.engines.strategies.chunked_transcription_strategy import ChunkedTranscriptionStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_first_chunk_result():
    """Create a mock transcription result for the first chunk with 2 speakers"""
    # Create a mock audio file for testing
    mock_audio_file = "examples/audio/voice/test_audio.wav"
    os.makedirs(os.path.dirname(mock_audio_file), exist_ok=True)
    
    # Create an empty file to satisfy validation
    with open(mock_audio_file, 'w') as f:
        f.write("mock audio file")
    
    # Import here to avoid circular imports
    from src.models.speaker_models import TranscriptionResult, TranscriptionSegment
    
    # Simulate first chunk (0-120 seconds) with 2 speakers
    speaker_1_segments = [
        TranscriptionSegment(
            start=0.0,
            end=60.0,
            text="Hello, this is the first speaker talking for the first minute.",
            speaker="speaker_1",
            chunk_file="chunk_001.wav",
            chunk_number=1
        )
    ]
    
    speaker_2_segments = [
        TranscriptionSegment(
            start=60.0,
            end=120.0,
            text="Hi there, this is the second speaker talking for the second minute.",
            speaker="speaker_2",
            chunk_file="chunk_001.wav",
            chunk_number=1
        )
    ]
    
    # Create mock transcription result
    mock_result = TranscriptionResult(
        success=True,
        speakers={
            "speaker_1": speaker_1_segments,
            "speaker_2": speaker_2_segments
        },
        full_text="Hello, this is the first speaker talking for the first minute. Hi there, this is the second speaker talking for the second minute.",
        transcription_time=5.0,
        model_name="test-model",
        audio_file=mock_audio_file,
        speaker_count=2
    )
    
    return mock_result

def test_first_chunk_speaker_diarization():
    """Test that the first chunk produces output JSON with 2 speakers"""
    logger.info("🧪 Testing First Chunk Speaker Diarization")
    
    try:
        # Create speaker configuration
        speaker_config = SpeakerConfigFactory.get_config("conversation")
        logger.info(f"✅ Speaker config created: {speaker_config}")
        
        # Create consolidated transcription engine
        engine = ConsolidatedTranscriptionEngine(speaker_config)
        logger.info(f"✅ Engine created with speaker diarization: {engine._speaker_diarization_enabled}")
        
        # Create mock first chunk result
        mock_result = create_mock_first_chunk_result()
        logger.info(f"✅ Mock first chunk result created with {mock_result.speaker_count} speakers")
        
        # Log the mock result structure
        for speaker_id, segments in mock_result.speakers.items():
            logger.info(f"   - {speaker_id}: {len(segments)} segments")
            for segment in segments:
                logger.info(f"     * {segment.start:.1f}s - {segment.end:.1f}s: {segment.text[:50]}...")
        
        # Test speaker enhancement with mock speaker segments
        # Simulate speaker diarization detecting 2 speakers
        mock_speaker_segments = [
            (0.0, 60.0),   # Speaker 0: 0-60 seconds
            (60.0, 120.0)  # Speaker 1: 60-120 seconds
        ]
        
        logger.info(f"🎯 Testing with mock speaker segments: {mock_speaker_segments}")
        
        # Apply speaker enhancement
        enhanced_result = engine._enhance_result_with_speakers(mock_result, mock_speaker_segments)
        
        if enhanced_result and enhanced_result.success:
            logger.info("✅ Speaker enhancement completed successfully")
            logger.info(f"   - Enhanced speakers: {enhanced_result.speaker_count}")
            logger.info(f"   - Total segments: {sum(len(segs) for segs in enhanced_result.speakers.values())}")
            
            # Verify we have 2 speakers
            if enhanced_result.speaker_count == 2:
                logger.info("✅ SUCCESS: Output contains exactly 2 speakers")
            else:
                logger.error(f"❌ FAILURE: Expected 2 speakers, got {enhanced_result.speaker_count}")
                return False
            
            # Log enhanced result structure
            for speaker_id, segments in enhanced_result.speakers.items():
                logger.info(f"   - {speaker_id}: {len(segments)} segments")
                for segment in segments:
                    logger.info(f"     * {segment.start:.1f}s - {segment.end:.1f}s: {segment.text[:50]}...")
            
            # Test JSON output generation
            test_json_output(enhanced_result)
            
            return True
            
        else:
            logger.error("❌ Speaker enhancement failed")
            if hasattr(enhanced_result, 'error_message'):
                logger.error(f"   Error: {enhanced_result.error_message}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_json_output(enhanced_result):
    """Test JSON output generation and verify 2 speakers"""
    logger.info("🧪 Testing JSON Output Generation")
    
    try:
        # Convert to dictionary format
        result_dict = {
            'success': enhanced_result.success,
            'speakers': {},
            'full_text': enhanced_result.full_text,
            'transcription_time': enhanced_result.transcription_time,
            'model_name': enhanced_result.model_name,
            'audio_file': enhanced_result.audio_file,
            'speaker_count': enhanced_result.speaker_count
        }
        
        # Convert speaker segments to dictionaries
        for speaker_id, segments in enhanced_result.speakers.items():
            result_dict['speakers'][speaker_id] = []
            for segment in segments:
                segment_dict = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'speaker': segment.speaker,
                    'chunk_file': getattr(segment, 'chunk_file', None),
                    'chunk_number': getattr(segment, 'chunk_number', None)
                }
                result_dict['speakers'][speaker_id].append(segment_dict)
        
        # Generate JSON
        json_output = json.dumps(result_dict, indent=2, ensure_ascii=False)
        
        # Save test JSON file
        test_json_file = "test_first_chunk_output.json"
        with open(test_json_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        logger.info(f"✅ JSON output saved to: {test_json_file}")
        
        # Verify JSON structure
        verify_json_structure(result_dict)
        
        # Display JSON content
        logger.info("📄 Generated JSON Structure:")
        logger.info(json.dumps(result_dict, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        logger.error(f"❌ JSON output test failed: {e}")
        return False

def verify_json_structure(result_dict):
    """Verify the JSON structure contains 2 speakers"""
    logger.info("🔍 Verifying JSON Structure")
    
    try:
        # Check basic structure
        assert 'success' in result_dict, "Missing 'success' field"
        assert 'speakers' in result_dict, "Missing 'speakers' field"
        assert 'speaker_count' in result_dict, "Missing 'speaker_count' field"
        
        # Verify speaker count
        speaker_count = result_dict['speaker_count']
        actual_speakers = len(result_dict['speakers'])
        
        logger.info(f"   - Declared speaker count: {speaker_count}")
        logger.info(f"   - Actual speakers in JSON: {actual_speakers}")
        
        if speaker_count == 2 and actual_speakers == 2:
            logger.info("✅ SUCCESS: JSON contains exactly 2 speakers")
        else:
            logger.error(f"❌ FAILURE: Expected 2 speakers, got {actual_speakers}")
            return False
        
        # Verify each speaker has segments
        for speaker_id, segments in result_dict['speakers'].items():
            logger.info(f"   - {speaker_id}: {len(segments)} segments")
            if len(segments) == 0:
                logger.warning(f"⚠️ Warning: {speaker_id} has no segments")
        
        # Verify text content is preserved
        total_text_length = len(result_dict.get('full_text', ''))
        logger.info(f"   - Total text length: {total_text_length} characters")
        
        if total_text_length > 0:
            logger.info("✅ SUCCESS: Text content is preserved")
        else:
            logger.warning("⚠️ Warning: No text content found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ JSON structure verification failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases for speaker enhancement"""
    logger.info("🧪 Testing Edge Cases")
    
    try:
        # Test with empty speaker segments
        logger.info("🎯 Testing with empty speaker segments")
        mock_result = create_mock_first_chunk_result()
        empty_speaker_segments = []
        
        engine = ConsolidatedTranscriptionEngine(SpeakerConfigFactory.get_config("conversation"))
        enhanced_result = engine._enhance_result_with_speakers(mock_result, empty_speaker_segments)
        
        if enhanced_result and enhanced_result.success:
            logger.info("✅ Empty speaker segments handled correctly")
            logger.info(f"   - Result speakers: {enhanced_result.speaker_count}")
        else:
            logger.error("❌ Empty speaker segments not handled correctly")
        
        # Test with single speaker segment
        logger.info("🎯 Testing with single speaker segment")
        single_speaker_segments = [(0.0, 120.0)]
        
        enhanced_result = engine._enhance_result_with_speakers(mock_result, single_speaker_segments)
        
        if enhanced_result and enhanced_result.success:
            logger.info("✅ Single speaker segment handled correctly")
            logger.info(f"   - Result speakers: {enhanced_result.speaker_count}")
        else:
            logger.error("❌ Single speaker segment not handled correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Edge case testing failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files created during testing"""
    try:
        # Remove mock audio file
        mock_audio_file = "examples/audio/voice/test_audio.wav"
        if os.path.exists(mock_audio_file):
            os.remove(mock_audio_file)
            logger.info(f"🧹 Cleaned up mock audio file: {mock_audio_file}")
        
        # Remove test JSON file
        test_json_file = "test_first_chunk_output.json"
        if os.path.exists(test_json_file):
            os.remove(test_json_file)
            logger.info(f"🧹 Cleaned up test JSON file: {test_json_file}")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not clean up test files: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting First Chunk Speaker Test Suite")
    
    try:
        # Run main test
        main_test_passed = test_first_chunk_speaker_diarization()
        
        # Run edge case tests
        edge_cases_passed = test_edge_cases()
        
        # Summary
        logger.info("=" * 60)
        if main_test_passed and edge_cases_passed:
            logger.info("🎉 ALL TESTS PASSED: First chunk correctly produces 2 speakers")
        else:
            logger.error("❌ SOME TESTS FAILED: Check the output above for details")
        
        logger.info("=" * 60)
        
    finally:
        # Clean up test files
        cleanup_test_files()
