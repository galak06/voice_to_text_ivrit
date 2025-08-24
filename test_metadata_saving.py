#!/usr/bin/env python3
"""
Test Metadata Saving
Verifies that enhanced metadata is being saved to chunk progress files
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.engines.strategies.chunked_transcription_strategy import ChunkedTranscriptionStrategy
from src.core.factories.speaker_config_factory import SpeakerConfigFactory
from src.models.speaker_models import TranscriptionSegment
from src.utils.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_metadata_saving():
    """Test that enhanced metadata is saved to chunk progress files"""
    try:
        logger.info("🚀 Starting metadata saving test")
        
        # Get configuration
        config_manager = ConfigManager()
        config = config_manager.config
        
        # Create chunked transcription strategy
        strategy = ChunkedTranscriptionStrategy(
            config=config,
            app_config=None
        )
        
        # Set engine type for testing
        strategy.engine_type = "speaker-diarization"
        logger.info(f"✅ Chunked transcription strategy created")
        
        # Create test chunk progress file
        test_chunk_file = "output/temp_chunks/test_chunk_001_0s_120s.json"
        os.makedirs("output/temp_chunks", exist_ok=True)
        
        # Create initial progress data
        initial_data = {
            "chunk_number": 1,
            "start_time": 0,
            "end_time": 120,
            "status": "pending",
            "created_at": 1234567890.0,
            "text": "",
            "processing_started": None,
            "processing_completed": None,
            "audio_chunk_file": "test_audio_chunk_001.wav",
            "error_message": None
        }
        
        # Write initial file
        with open(test_chunk_file, 'w') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Created test chunk file: {test_chunk_file}")
        
        # Create a test enhanced segment with metadata
        test_segment = TranscriptionSegment(
            start=0.0,
            end=120.0,
            text="This is a test transcription with enhanced speaker information.",
            speaker="enhanced_multi_1",
            words=None,
            confidence=0.95,
            chunk_file="test_chunk_001.wav",
            chunk_number=1
        )
        
        # Add metadata to the segment
        test_segment.metadata = {
            "enhancement_strategy": "advanced_enhancement",
            "enhancement_level": "advanced",
            "original_speaker": "speaker_1",
            "detected_speakers": 2,
            "speaker_time_ranges": [
                [0.0, 60.0],
                [60.0, 120.0]
            ],
            "enhancement_applied": True,
            "analysis_details": {
                "chunk_duration": 120.0,
                "speaker_density": 0.017,
                "enhancement_timestamp": 0.0
            }
        }
        
        logger.info("✅ Created test segment with metadata")
        
        # Test the metadata saving
        strategy._update_chunk_progress(
            chunk_num=1,
            status="completed",
            text=test_segment.text,
            error_message=None,
            speaker_id=test_segment.speaker,
            enhanced_segment=test_segment
        )
        
        logger.info("✅ Called _update_chunk_progress with enhanced metadata")
        
        # Read the updated file to verify metadata was saved
        with open(test_chunk_file, 'r') as f:
            updated_data = json.load(f)
        
        logger.info("=" * 80)
        logger.info("🎯 VERIFICATION RESULTS")
        logger.info("=" * 80)
        
        # Check if metadata was saved
        if 'enhanced_metadata' in updated_data:
            logger.info("✅ Enhanced metadata saved successfully!")
            logger.info(f"📊 Enhancement strategy: {updated_data.get('enhancement_strategy', 'N/A')}")
            logger.info(f"📊 Enhancement applied: {updated_data.get('enhancement_applied', 'N/A')}")
            logger.info(f"📊 Detected speakers: {updated_data.get('detected_speakers', 'N/A')}")
            
            if 'speaker_time_ranges' in updated_data:
                ranges = updated_data['speaker_time_ranges']
                logger.info(f"⏰ Speaker time ranges: {len(ranges)} segments")
                for i, (start, end) in enumerate(ranges):
                    logger.info(f"   Speaker {i+1}: {start:.1f}s - {end:.1f}s")
            
            if 'analysis_details' in updated_data:
                details = updated_data['analysis_details']
                logger.info(f"📈 Analysis details:")
                for key, value in details.items():
                    logger.info(f"   {key}: {value}")
        else:
            logger.error("❌ Enhanced metadata was NOT saved!")
            logger.info(f"Available fields: {list(updated_data.keys())}")
        
        # Display the final JSON
        logger.info("\n" + "=" * 80)
        logger.info("🎯 FINAL CHUNK PROGRESS JSON")
        logger.info("=" * 80)
        
        json_str = json.dumps(updated_data, indent=2, ensure_ascii=False)
        print(json_str)
        
        # Clean up test file
        os.remove(test_chunk_file)
        logger.info(f"🧹 Cleaned up test file: {test_chunk_file}")
        
        return updated_data
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    logger.info("🧪 Metadata Saving Test")
    logger.info("=" * 80)
    
    result = test_metadata_saving()
    
    if result and 'enhanced_metadata' in result:
        logger.info("✅ Test completed successfully!")
        logger.info("🎯 Enhanced metadata is now being saved to chunk progress files!")
        sys.exit(0)
    else:
        logger.error("❌ Test failed or metadata not saved!")
        sys.exit(1)
