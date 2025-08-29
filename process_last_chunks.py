#!/usr/bin/env python3
"""
Process only the last two chunks (246 and 247) that have errors
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config_manager import ConfigManager
from src.models.environment import Environment
from src.core.engines.consolidated_transcription_engine import ConsolidatedTranscriptionEngine
from src.core.engines.strategies.direct_transcription_strategy import DirectTranscriptionStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_chunk(chunk_number: int, start_time: float, end_time: float, config_manager: ConfigManager):
    """Process a single chunk"""
    try:
        logger.info(f"🎯 Processing chunk {chunk_number}: {start_time:.1f}s - {end_time:.1f}s")
        
        # Initialize engine
        engine = ConsolidatedTranscriptionEngine(config_manager)
        
        # Initialize DirectTranscriptionStrategy
        direct_strategy = DirectTranscriptionStrategy(config_manager)
        
        # Audio chunk file path
        audio_chunk_filename = f"audio_chunk_{chunk_number:03d}_{int(start_time)}s_{int(end_time)}s.wav"
        audio_chunk_path = f"output/audio_chunks/{audio_chunk_filename}"
        
        if not os.path.exists(audio_chunk_path):
            logger.error(f"❌ Audio chunk file not found: {audio_chunk_path}")
            return False
        
        # Create chunk info
        chunk_info = {
            'chunk_number': chunk_number,
            'start': start_time,
            'end': end_time,
            'filename': f"chunk_{chunk_number:03d}_{int(start_time)}s_{int(end_time)}s"
        }
        
        # Process chunk
        start_processing = time.time()
        result = direct_strategy.execute(audio_chunk_path, "ivrit-ai/whisper-large-v3-ct2", engine, chunk_info)
        processing_time = time.time() - start_processing
        
        if result and result.success:
            logger.info(f"✅ Chunk {chunk_number} completed successfully in {processing_time:.1f}s")
            logger.info(f"📝 Text: {result.full_text[:100]}...")
            return True
        else:
            logger.error(f"❌ Chunk {chunk_number} failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error processing chunk {chunk_number}: {e}")
        return False

def main():
    """Main function to process the last two chunks"""
    try:
        # Load configuration with production environment
        logger.info("🔧 Loading configuration...")
        config_manager = ConfigManager("config/environments", Environment.PRODUCTION)
        
        # Define the last two chunks
        chunks_to_process = [
            (246, 6125.0, 6153.680430839002),  # Chunk 246
            (247, 6150.0, 6153.680430839002)   # Chunk 247
        ]
        
        logger.info(f"🎯 Processing {len(chunks_to_process)} chunks...")
        
        success_count = 0
        for chunk_num, start_time, end_time in chunks_to_process:
            logger.info("=" * 60)
            success = process_chunk(chunk_num, start_time, end_time, config_manager)
            if success:
                success_count += 1
        
        logger.info("=" * 60)
        logger.info(f"🎯 Processing completed: {success_count}/{len(chunks_to_process)} chunks successful")
        
        if success_count == len(chunks_to_process):
            logger.info("✅ All chunks processed successfully!")
        else:
            logger.warning(f"⚠️ {len(chunks_to_process) - success_count} chunks failed")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
