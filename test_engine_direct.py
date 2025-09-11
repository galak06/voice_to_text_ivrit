#!/usr/bin/env python3
"""
Direct test of the consolidated transcription engine with debugging
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from src.utils.config_manager import ConfigManager, Environment
from src.core.engines.consolidated_transcription_engine import ConsolidatedTranscriptionEngine
from src.core.engines.utilities.simple_text_processor import SimpleTextProcessor

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_transcription():
    """Test transcription with debug output"""
    try:
        # Initialize config manager
        config_manager = ConfigManager("config", environment=Environment.PRODUCTION)
        
        # Initialize text processor
        text_processor = SimpleTextProcessor()
        
        # Initialize engine
        engine = ConsolidatedTranscriptionEngine(
            config_manager=config_manager,
            text_processor=text_processor
        )
        
        # Test audio file
        audio_file = "output/audio_chunks/audio_chunk_001_0s_30s.wav"
        model_name = "ivrit-ai/whisper-large-v3-ct2"
        
        logger.info(f"🎯 Testing transcription with {audio_file}")
        logger.info(f"🤖 Using model: {model_name}")
        
        # Transcribe
        result = engine.transcribe(audio_file, model_name)
        
        logger.info(f"🔍 Result success: {result.success}")
        logger.info(f"🔍 Result text: '{result.text}'")
        logger.info(f"🔍 Result text length: {len(result.text) if result.text else 0}")
        
        if hasattr(result, 'segments') and result.segments:
            logger.info(f"🔍 Number of segments: {len(result.segments)}")
            for i, segment in enumerate(result.segments):
                logger.info(f"🔍 Segment {i}: '{segment.text}'")
        
        print("================================================================================")
        print("🎉 DIRECT ENGINE TEST RESULTS")
        print("================================================================================")
        print(f"Success: {result.success}")
        print(f"Text: '{result.text}'")
        print(f"Text Length: {len(result.text) if result.text else 0}")
        print("================================================================================")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transcription()