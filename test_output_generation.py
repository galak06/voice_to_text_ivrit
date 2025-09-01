#!/usr/bin/env python3
"""
Test script for output generation only
Uses existing chunk results to test the output processing logic
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_chunk_results():
    """Load all existing chunk results from the output directory"""
    chunk_dir = "output/chunk_results"
    chunk_results = []
    
    if not os.path.exists(chunk_dir):
        logger.error(f"Chunk results directory not found: {chunk_dir}")
        return []
    
    # Load all chunk JSON files
    for filename in os.listdir(chunk_dir):
        if filename.endswith('.json') and filename.startswith('chunk_'):
            file_path = os.path.join(chunk_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                    chunk_results.append(chunk_data)
                    logger.info(f"✅ Loaded chunk: {filename}")
            except Exception as e:
                logger.error(f"❌ Error loading {filename}: {e}")
    
    logger.info(f"📊 Loaded {len(chunk_results)} chunk results")
    return chunk_results

def test_output_strategy():
    """Test the output strategy with existing chunk results"""
    try:
        from src.core.engines.strategies.output_strategy import MergedOutputStrategy, OverlappingTextDeduplicator
        from src.utils.config_manager import ConfigManager
        
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Create output strategy
        deduplicator = OverlappingTextDeduplicator(config_manager)
        output_strategy = MergedOutputStrategy(config_manager, deduplicator)
        
        logger.info("✅ Output strategy created successfully")
        return output_strategy
        
    except Exception as e:
        logger.error(f"❌ Error creating output strategy: {e}")
        return None

def test_output_manager():
    """Test the output manager with existing chunk results"""
    try:
        from src.output_data.managers.output_manager import OutputManager
        from src.output_data.utils.data_utils import DataUtils
        from src.core.engines.strategies.output_strategy import MergedOutputStrategy, OverlappingTextDeduplicator
        from src.utils.config_manager import ConfigManager
        
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Create output strategy
        deduplicator = OverlappingTextDeduplicator(config_manager)
        output_strategy = MergedOutputStrategy(config_manager, deduplicator)
        
        # Create data utils
        data_utils = DataUtils()
        
        # Create output manager
        output_manager = OutputManager('output', data_utils, output_strategy)
        output_manager.config_manager = config_manager  # Inject config manager
        
        logger.info("✅ Output manager created successfully")
        return output_manager
        
    except Exception as e:
        logger.error(f"❌ Error creating output manager: {e}")
        return None

def create_test_transcription_result(chunk_results):
    """Create a test transcription result from chunk data"""
    try:
        from src.models.transcription_results import TranscriptionResult, TranscriptionSegment, TranscriptionMetadata
        
        # Collect all segments from chunks
        all_segments = []
        all_speakers = {}
        total_text = ""
        
        for chunk in chunk_results:
            if 'speaker_recognition' in chunk and 'speaker_details' in chunk['speaker_recognition']:
                speaker_details = chunk['speaker_recognition']['speaker_details']
                
                for speaker_id, speaker_info in speaker_details.items():
                    if speaker_id not in all_speakers:
                        all_speakers[speaker_id] = []
                    
                    for segment_data in speaker_info.get('segments', []):
                        # Create TranscriptionSegment
                        segment = TranscriptionSegment(
                            start=segment_data.get('start', 0.0),
                            end=segment_data.get('end', 0.0),
                            text=segment_data.get('text', ''),
                            speaker=speaker_id
                        )
                        all_segments.append(segment)
                        all_speakers[speaker_id].append(segment)
                        
                        # Add to total text
                        if segment_data.get('text'):
                            total_text += " " + segment_data['text']
        
        # Create metadata
        metadata = TranscriptionMetadata(
            model_name="test-model",
            engine="test-engine",
            language="he",
            processing_time=0.0
        )
        
        # Create final result
        result = TranscriptionResult(
            success=True,
            text=total_text.strip(),
            segments=all_segments,
            speakers=all_speakers,
            speaker_count=len(all_speakers),
            metadata=metadata
        )
        
        logger.info(f"✅ Created test transcription result: {len(all_segments)} segments, {len(all_speakers)} speakers")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating test transcription result: {e}")
        return None

def test_output_generation():
    """Test the complete output generation process"""
    logger.info("🚀 Starting output generation test...")
    
    # 1. Load existing chunk results
    chunk_results = load_chunk_results()
    if not chunk_results:
        logger.error("❌ No chunk results to process")
        return
    
    # 2. Test output strategy
    output_strategy = test_output_strategy()
    if not output_strategy:
        logger.error("❌ Output strategy test failed")
        return
    
    # 3. Test output manager
    output_manager = test_output_manager()
    if not output_manager:
        logger.error("❌ Output manager test failed")
        return
    
    # 4. Create test transcription result
    test_result = create_test_transcription_result(chunk_results)
    if not test_result:
        logger.error("❌ Test transcription result creation failed")
        return
    
    # 5. Test saving output files
    try:
        logger.info("📝 Testing output file generation...")
        
        # Save using output manager
        results = output_manager.save_transcription(
            transcription_data=test_result,
            audio_file="test_audio.wav",
            model="test-model",
            engine="test-engine"
        )
        
        logger.info(f"✅ Output files generated: {results}")
        
        # Check what files were created
        output_dir = "output"
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith(('.json', '.txt', '.docx')):
                    file_path = os.path.join(output_dir, filename)
                    file_size = os.path.getsize(file_path)
                    logger.info(f"📁 Output file: {filename} ({file_size} bytes)")
        
    except Exception as e:
        logger.error(f"❌ Error testing output generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_output_generation()
