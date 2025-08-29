#!/usr/bin/env python3
"""
Process all chunk JSON files to create unified final transcription
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

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

def load_all_chunk_jsons(chunk_results_dir: str) -> List[Dict[str, Any]]:
    """Load all chunk JSON files from the chunk results directory"""
    all_chunks = []
    
    try:
        # List all chunk result files
        chunk_files = [f for f in os.listdir(chunk_results_dir) if f.startswith('chunk_') and f.endswith('.json')]
        chunk_files.sort(key=lambda x: int(x.split('_')[1]))  # Sort by chunk number
        
        logger.info(f"🔍 Found {len(chunk_files)} chunk JSON files")
        
        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunk_results_dir, chunk_file)
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                # Add file path for reference
                chunk_data['source_file'] = chunk_file
                all_chunks.append(chunk_data)
                
                # Log chunk info
                chunk_num = chunk_data.get('chunk_number', 'unknown')
                status = chunk_data.get('status', 'unknown')
                text_length = len(chunk_data.get('text', ''))
                logger.debug(f"📄 Loaded chunk {chunk_num}: status={status}, text={text_length} chars")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to load chunk file {chunk_file}: {e}")
                continue
        
        logger.info(f"📊 Successfully loaded {len(all_chunks)} chunk JSON files")
        return all_chunks
        
    except Exception as e:
        logger.error(f"❌ Error loading chunks: {e}")
        return []

def analyze_chunk_statuses(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the status of all chunks"""
    status_counts = {}
    text_lengths = []
    completed_chunks = []
    failed_chunks = []
    
    for chunk in chunks:
        status = chunk.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status == 'completed' and chunk.get('text'):
            completed_chunks.append(chunk)
            text_lengths.append(len(chunk.get('text', '')))
        elif status != 'completed':
            failed_chunks.append(chunk)
    
    analysis = {
        'total_chunks': len(chunks),
        'status_counts': status_counts,
        'completed_chunks': len(completed_chunks),
        'failed_chunks': len(failed_chunks),
        'total_text_length': sum(text_lengths),
        'average_text_length': sum(text_lengths) / len(text_lengths) if text_lengths else 0,
        'chunk_numbers': [c.get('chunk_number', 0) for c in chunks],
        'time_range': {
            'start': min([c.get('start_time', 0) for c in chunks]) if chunks else 0,
            'end': max([c.get('end_time', 0) for c in chunks]) if chunks else 0
        }
    }
    
    return analysis

def create_segments_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert chunks to segments format for output strategy processing"""
    segments = []
    
    for chunk in chunks:
        if chunk.get('status') == 'completed' and chunk.get('text'):
            # Create segment from chunk data
            segment = {
                'start': chunk.get('start_time', 0),
                'end': chunk.get('end_time', 0),
                'text': chunk.get('text', ''),
                'speaker': '0',  # Default speaker
                'chunk_number': chunk.get('chunk_number', 0),
                'confidence': chunk.get('transcription_details', {}).get('confidence_score', 0.9),
                'model': chunk.get('transcription_details', {}).get('model_used', 'unknown'),
                'engine': chunk.get('transcription_details', {}).get('engine_used', 'unknown'),
                'source_file': chunk.get('source_file', ''),
                'processing_time': chunk.get('processing_completed', 0)
            }
            segments.append(segment)
    
    # Sort segments by start time
    segments.sort(key=lambda x: x['start'])
    
    logger.info(f"📝 Created {len(segments)} segments from completed chunks")
    return segments

def extract_word_level_data(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract word-level transcription data if available"""
    word_data = []
    
    for chunk in chunks:
        if chunk.get('status') == 'completed' and chunk.get('text'):
            chunk_num = chunk.get('chunk_number', 0)
            start_time = chunk.get('start_time', 0)
            
            # Check if chunk has word-level details
            transcription_details = chunk.get('transcription_details', {})
            words = transcription_details.get('words', [])
            
            if words:
                # Process word-level data
                for word_info in words:
                    word_data.append({
                        'chunk_number': chunk_num,
                        'start_time': start_time + word_info.get('start', 0),
                        'end_time': start_time + word_info.get('end', 0),
                        'word': word_info.get('word', ''),
                        'confidence': word_info.get('confidence', 0.0),
                        'speaker': word_info.get('speaker', '0')
                    })
            else:
                # Fallback: split text into words with estimated timing
                text = chunk.get('text', '')
                chunk_duration = chunk.get('end_time', 0) - chunk.get('start_time', 0)
                words_list = text.split()
                
                if words_list and chunk_duration > 0:
                    word_duration = chunk_duration / len(words_list)
                    for i, word in enumerate(words_list):
                        word_start = start_time + (i * word_duration)
                        word_end = word_start + word_duration
                        word_data.append({
                            'chunk_number': chunk_num,
                            'start_time': word_start,
                            'end_time': word_end,
                            'word': word,
                            'confidence': 0.8,  # Estimated confidence
                            'speaker': '0'
                        })
    
    logger.info(f"🔤 Extracted word-level data for {len(word_data)} words")
    return word_data

def run_unified_processing(chunks: List[Dict[str, Any]], config_manager: ConfigManager):
    """Run unified processing on all chunks"""
    try:
        logger.info("🚀 Starting unified processing of all chunks...")
        
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
            return None
        
        # Use output strategy to create final output
        logger.info("🎯 Creating final output using output strategy...")
        final_text = output_strategy.create_final_output(segments)
        deduplicated_segments = output_strategy.create_segmented_output(segments)
        
        logger.info(f"✅ Output strategy completed:")
        logger.info(f"   - Original segments: {len(segments)}")
        logger.info(f"   - Deduplicated segments: {len(deduplicated_segments)}")
        logger.info(f"   - Final text length: {len(final_text)} characters")
        
        # Extract word-level data
        word_data = extract_word_level_data(chunks)
        
        # Create comprehensive final result
        final_result = {
            'success': True,
            'full_text': final_text,
            'segments': deduplicated_segments,
            'word_level_data': word_data,
            'total_segments': len(deduplicated_segments),
            'total_chunks_processed': len(chunks),
            'total_words': len(word_data),
            'total_duration': max([s['end'] for s in segments]) if segments else 0,
            'model_used': chunks[0].get('transcription_details', {}).get('model_used', 'unknown') if chunks else 'unknown',
            'engine_used': chunks[0].get('transcription_details', {}).get('engine_used', 'unknown') if chunks else 'unknown',
            'language': 'he',  # Hebrew
            'processing_timestamp': datetime.now().isoformat(),
            'chunk_analysis': analyze_chunk_statuses(chunks)
        }
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Error in unified processing: {e}")
        return None

def save_results(final_result: Dict[str, Any], output_dir: str = "output/transcriptions"):
    """Save all results in multiple formats"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive JSON
        json_file = os.path.join(output_dir, f"unified_transcription_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Comprehensive JSON saved to: {json_file}")
        
        # Save text file
        text_file = os.path.join(output_dir, f"unified_transcription_{timestamp}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(final_result['full_text'])
        logger.info(f"💾 Text file saved to: {text_file}")
        
        # Save word-level data separately
        word_file = os.path.join(output_dir, f"word_level_data_{timestamp}.json")
        word_data = {
            'words': final_result['word_level_data'],
            'total_words': len(final_result['word_level_data']),
            'processing_timestamp': final_result['processing_timestamp']
        }
        with open(word_file, 'w', encoding='utf-8') as f:
            json.dump(word_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Word-level data saved to: {word_file}")
        
        # Save segments separately
        segments_file = os.path.join(output_dir, f"segments_{timestamp}.json")
        segments_data = {
            'segments': final_result['segments'],
            'total_segments': len(final_result['segments']),
            'processing_timestamp': final_result['processing_timestamp']
        }
        with open(segments_file, 'w', encoding='utf-8') as f:
            json.dump(segments_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Segments data saved to: {segments_file}")
        
        return {
            'json': json_file,
            'text': text_file,
            'words': word_file,
            'segments': segments_file
        }
        
    except Exception as e:
        logger.error(f"❌ Error saving results: {e}")
        return None

def main():
    """Main function to process all chunk JSON files"""
    try:
        logger.info("🎯 Starting comprehensive processing of all chunk JSON files...")
        
        # Load configuration
        logger.info("🔧 Loading configuration...")
        config_manager = ConfigManager("config/environments", Environment.PRODUCTION)
        
        # Load all chunk JSON files
        chunk_results_dir = "output/chunk_results"
        if not os.path.exists(chunk_results_dir):
            logger.error(f"❌ Chunk results directory not found: {chunk_results_dir}")
            return
        
        chunks = load_all_chunk_jsons(chunk_results_dir)
        
        if not chunks:
            logger.error("❌ No chunk JSON files found to process")
            return
        
        # Analyze chunk statuses
        analysis = analyze_chunk_statuses(chunks)
        logger.info("📊 Chunk Analysis:")
        logger.info(f"   - Total chunks: {analysis['total_chunks']}")
        logger.info(f"   - Completed: {analysis['completed_chunks']}")
        logger.info(f"   - Failed: {analysis['failed_chunks']}")
        logger.info(f"   - Total text length: {analysis['total_text_length']} characters")
        logger.info(f"   - Time range: {analysis['time_range']['start']:.1f}s - {analysis['time_range']['end']:.1f}s")
        
        # Run unified processing
        final_result = run_unified_processing(chunks, config_manager)
        
        if final_result:
            # Save all results
            saved_files = save_results(final_result)
            
            if saved_files:
                logger.info("🎉 Processing completed successfully!")
                logger.info(f"📊 Final result: {final_result['total_segments']} segments, {final_result['total_words']} words")
                logger.info(f"📁 Files saved:")
                for file_type, file_path in saved_files.items():
                    logger.info(f"   - {file_type.upper()}: {file_path}")
            else:
                logger.error("❌ Failed to save results")
        else:
            logger.error("❌ Unified processing failed")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
