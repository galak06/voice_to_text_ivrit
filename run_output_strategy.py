#!/usr/bin/env python3
"""
Run output strategy for all completed chunks to create final transcription output
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
from src.core.factories.output_strategy_factory import OutputStrategyFactory
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

def create_segments_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert chunks to segments format for output strategy processing"""
    segments = []
    
    for chunk in chunks:
        # Create segment from chunk data
        segment = {
            'start': chunk.get('start_time', 0),
            'end': chunk.get('end_time', 0),
            'text': chunk.get('text', ''),
            'speaker': '0',  # Default speaker
            'chunk_number': chunk.get('chunk_number', 0),
            'confidence': chunk.get('transcription_details', {}).get('confidence_score', 0.9),
            'model': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
            'engine': chunk.get('transcription_details', {}).get('engine_used', 'unknown')
        }
        segments.append(segment)
    
    # Sort segments by start time
    segments.sort(key=lambda x: x['start'])
    
    logger.info(f"📝 Created {len(segments)} segments from chunks")
    return segments

def run_output_strategy(chunks: List[Dict[str, Any]], config_manager: ConfigManager):
    """Run the output strategy to create final transcription output"""
    try:
        logger.info("🚀 Initializing output strategy...")
        
        # Create output strategy using factory
        output_strategy = OutputStrategyFactory.create_merged_output_strategy(config_manager)
        logger.info("✅ Output strategy created successfully")
        
        # Create output manager with strategy
        output_manager = OutputManager(
            output_base_path="output/transcriptions",
            data_utils=DataUtils(),
            output_strategy=output_strategy,
            config_manager=config_manager
        )
        logger.info("✅ Output manager created successfully")
        
        # Convert chunks to segments
        segments = create_segments_from_chunks(chunks)
        
        if not segments:
            logger.error("❌ No segments to process")
            return
        
        # Use output strategy to create final output
        logger.info("🎯 Creating final output using output strategy...")
        final_text = output_strategy.create_final_output(segments)
        deduplicated_segments = output_strategy.create_segmented_output(segments)
        
        logger.info(f"✅ Output strategy completed:")
        logger.info(f"   - Original segments: {len(segments)}")
        logger.info(f"   - Deduplicated segments: {len(deduplicated_segments)}")
        logger.info(f"   - Final text length: {len(final_text)} characters")
        
        # Create final transcription result
        final_result = {
            'success': True,
            'full_text': final_text,
            'segments': deduplicated_segments,
            'total_segments': len(deduplicated_segments),
            'total_chunks_processed': len(chunks),
            'total_duration': max([s['end'] for s in segments]) if segments else 0,
            'model_used': chunks[0].get('transcription_details', {}).get('model_used', 'unknown') if chunks else 'unknown',
            'engine_used': chunks[0].get('transcription_details', {}).get('engine_used', 'unknown') if chunks else 'unknown',
            'language': 'he',  # Hebrew
            'processing_timestamp': chunks[0].get('processing_completed', 0) if chunks else 0
        }
        
        # Save final result
        output_file = "output/transcriptions/final_transcription_from_chunks.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Final transcription saved to: {output_file}")
        
        # Also save as text file
        text_file = "output/transcriptions/final_transcription_from_chunks.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(final_text)

        logger.info(f"💾 Final transcription text saved to: {text_file}")

        # Create Word document (DOCX)
        try:
            from src.output_data.formatters.docx_formatter import DocxFormatter
            
            docx_file = "output/transcriptions/final_transcription_from_chunks.docx"
            logger.info("📝 Creating Word document...")
            
            # Create document with full text
            doc = DocxFormatter.create_simple_document(
                full_text=final_text,
                audio_file="combined_chunks",
                model=chunks[0].get('transcription_details', {}).get('model_used', 'unknown') if chunks else 'unknown',
                engine=chunks[0].get('transcription_details', {}).get('engine_used', 'unknown') if chunks else 'unknown'
            )
            
            if doc:
                doc.save(docx_file)
                logger.info(f"💾 Final transcription Word document saved to: {docx_file}")
            else:
                logger.warning("⚠️ Failed to create Word document")
                
        except ImportError:
            logger.warning("⚠️ python-docx not available - skipping Word document generation")
        except Exception as e:
            logger.error(f"❌ Failed to create Word document: {e}")
        
        # Display sample of final text
        logger.info("📝 Sample of final transcription:")
        sample_text = final_text[:500] + "..." if len(final_text) > 500 else final_text
        logger.info(f"   {sample_text}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Error running output strategy: {e}")
        return None

def main():
    """Main function to run output strategy for all completed chunks"""
    try:
        logger.info("🎯 Starting output strategy processing for all completed chunks...")
        
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
        
        # Run output strategy
        result = run_output_strategy(chunks, config_manager)
        
        if result:
            logger.info("🎉 Output strategy processing completed successfully!")
            logger.info(f"📊 Final result: {result['total_segments']} segments, {len(result['full_text'])} characters")
        else:
            logger.error("❌ Output strategy processing failed")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
