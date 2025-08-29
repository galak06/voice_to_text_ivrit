#!/usr/bin/env python3
"""
Run OutputProcessor on all completed chunks to generate properly formatted output files
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config_manager import ConfigManager
from src.models.environment import Environment
from src.core.processors.output_processor import OutputProcessor
from src.output_data.managers.output_manager import OutputManager
from src.output_data.utils.data_utils import DataUtils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_completed_chunks(chunk_results_dir: str) -> List[Dict[str, Any]]:
    """Load all completed chunks from the chunk results directory"""
    completed_chunks = []

    try:
        # List all chunk result files
        chunk_files = [f for f in os.listdir(chunk_results_dir) if f.startswith('chunk_') and f.endswith('.json')]
        logger.info(f"🔍 Found {len(chunk_files)} chunk result files")

        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunk_results_dir, chunk_file)
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)

                # Only process completed chunks
                if chunk_data.get('status') == 'completed' and chunk_data.get('text'):
                    completed_chunks.append(chunk_data)
                    logger.debug(f"✅ Loaded completed chunk {chunk_data.get('chunk_number')}: {len(chunk_data.get('text', ''))} chars")
                else:
                    logger.debug(f"⏳ Skipping chunk {chunk_data.get('chunk_number')}: status={chunk_data.get('status')}")

            except Exception as e:
                logger.warning(f"⚠️ Failed to load chunk file {chunk_file}: {e}")
                continue

        logger.info(f"📊 Loaded {len(completed_chunks)} completed chunks with text content")
        return completed_chunks

    except Exception as e:
        logger.error(f"❌ Error loading chunks: {e}")
        return []

def create_transcription_result_for_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Convert chunk data to transcription result format expected by OutputProcessor"""
    # Create segments from chunk
    segments = [{
        'start': chunk.get('start_time', 0),
        'end': chunk.get('end_time', 0),
        'text': chunk.get('text', ''),
        'speaker': '0',  # Default speaker
        'confidence': chunk.get('transcription_details', {}).get('confidence_score', 0.9)
    }]
    
    # Create transcription data structure
    transcription_data = {
        'segments': segments,
        'text': chunk.get('text', ''),
        'language': 'he',
        'duration': chunk.get('end_time', 0) - chunk.get('start_time', 0),
        'metadata': {
            'chunk_number': chunk.get('chunk_number', 0),
            'start_time': chunk.get('start_time', 0),
            'end_time': chunk.get('end_time', 0),
            'model_used': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
            'engine_used': chunk.get('transcription_details', {}).get('engine_used', 'unknown'),
            'confidence_score': chunk.get('transcription_details', {}).get('confidence_score', 0.9)
        }
    }
    
    # Create transcription result structure
    transcription_result = {
        'success': True,
        'transcription': transcription_data,
        'model': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
        'engine': chunk.get('transcription_details', {}).get('engine_used', 'unknown'),
        'chunk_number': chunk.get('chunk_number', 0)
    }
    
    return transcription_result

def create_input_metadata_for_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Create input metadata for the chunk"""
    return {
        'file_name': f"chunk_{chunk.get('chunk_number', 0)}_{chunk.get('start_time', 0)}s_{chunk.get('end_time', 0)}s",
        'chunk_number': chunk.get('chunk_number', 0),
        'start_time': chunk.get('start_time', 0),
        'end_time': chunk.get('end_time', 0),
        'duration': chunk.get('end_time', 0) - chunk.get('start_time', 0)
    }

def run_output_processor_on_chunks(chunks: List[Dict[str, Any]], config_manager: ConfigManager):
    """Run OutputProcessor on all chunks to generate properly formatted output"""
    try:
        logger.info("🚀 Initializing OutputProcessor...")

        # Create output manager
        output_manager = OutputManager(
            output_base_path="output/transcriptions",
            data_utils=DataUtils(),
            output_strategy=None,  # Not needed for basic output processing
            config_manager=config_manager
        )
        logger.info("✅ Output manager created successfully")

        # Create output processor
        output_processor = OutputProcessor(config_manager, output_manager)
        logger.info("✅ Output processor created successfully")

        # Process each chunk
        successful_chunks = 0
        failed_chunks = 0
        
        for chunk in chunks:
            try:
                chunk_number = chunk.get('chunk_number', 0)
                logger.info(f"🔄 Processing chunk {chunk_number}...")
                
                # Create transcription result format
                transcription_result = create_transcription_result_for_chunk(chunk)
                
                # Create input metadata
                input_metadata = create_input_metadata_for_chunk(chunk)
                
                # Process output using OutputProcessor
                result = output_processor.process_output(transcription_result, input_metadata)
                
                if result.get('success', False):
                    successful_chunks += 1
                    logger.info(f"✅ Chunk {chunk_number} processed successfully")
                    
                    # Log output formats generated
                    output_results = result.get('output_results', {})
                    formats_generated = list(output_results.keys())
                    logger.info(f"   📁 Generated formats: {formats_generated}")
                    
                else:
                    failed_chunks += 1
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"❌ Chunk {chunk_number} failed: {error_msg}")
                
            except Exception as e:
                failed_chunks += 1
                logger.error(f"❌ Error processing chunk {chunk.get('chunk_number', 0)}: {e}")
                continue
        
        logger.info(f"📊 Output processing completed:")
        logger.info(f"   - Successful chunks: {successful_chunks}")
        logger.info(f"   - Failed chunks: {failed_chunks}")
        logger.info(f"   - Total chunks: {len(chunks)}")
        
        return successful_chunks, failed_chunks

    except Exception as e:
        logger.error(f"❌ Error running output processor: {e}")
        return 0, 0

def main():
    """Main function to run OutputProcessor on all completed chunks"""
    try:
        logger.info("🎯 Starting OutputProcessor processing for all completed chunks...")

        # Load configuration
        logger.info("🔧 Loading configuration...")
        config_manager = ConfigManager("config/environments", Environment.PRODUCTION)

        # Load all completed chunks
        chunk_results_dir = "output/chunk_results"
        if not os.path.exists(chunk_results_dir):
            logger.error(f"❌ Chunk results directory not found: {chunk_results_dir}")
            return

        chunks = load_completed_chunks(chunk_results_dir)

        if not chunks:
            logger.error("❌ No completed chunks found to process")
            return

        # Run output processor
        successful, failed = run_output_processor_on_chunks(chunks, config_manager)

        if successful > 0:
            logger.info("🎉 OutputProcessor processing completed successfully!")
            logger.info(f"📊 Results: {successful} successful, {failed} failed")
        else:
            logger.error("❌ OutputProcessor processing failed for all chunks")

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
