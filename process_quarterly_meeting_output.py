#!/usr/bin/env python3
"""
Process the quarterly meeting transcription output from existing chunks
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config_manager import ConfigManager
from src.output_data.utils.data_utils import DataUtils
from src.core.engines.strategies.output_strategy import OverlappingTextDeduplicator, MergedOutputStrategy
from src.output_data.managers.output_manager import OutputManager
from src.core.processors.output_processor import OutputProcessor

def load_all_chunk_data() -> List[Dict[str, Any]]:
    """Load all chunk JSON files and extract transcription data"""
    chunk_files = glob.glob("output/chunk_results/chunk_*.json")
    chunk_files.sort()  # Sort to maintain chronological order
    
    print(f"📁 Found {len(chunk_files)} chunk files")
    
    all_segments = []
    combined_text = ""
    
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            if chunk_data.get('status') == 'completed' and chunk_data.get('text'):
                # Create segment from chunk data
                segment = {
                    'start': chunk_data.get('start_time', 0.0),
                    'end': chunk_data.get('end_time', 30.0),
                    'text': chunk_data.get('text', ''),
                    'words': chunk_data.get('words_estimated', 0)
                }
                all_segments.append(segment)
                combined_text += chunk_data.get('text', '') + ' '
                
        except Exception as e:
            print(f"⚠️ Error loading {chunk_file}: {e}")
    
    print(f"✅ Loaded {len(all_segments)} segments with {len(combined_text)} characters")
    return all_segments, combined_text.strip()

def main():
    """Main processing function"""
    print("🎤 Processing Quarterly Meeting Transcription Output")
    print("=" * 60)
    
    # Set environment and config path
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['CONFIG_DIR'] = 'config/environments'
    
    # Load chunk data
    segments, combined_text = load_all_chunk_data()
    
    if not segments:
        print("❌ No segments found!")
        return
    
    # Initialize components
    print("\n🔧 Initializing components...")
    config_manager = ConfigManager()
    data_utils = DataUtils()
    deduplicator = OverlappingTextDeduplicator(config_manager)
    output_strategy = MergedOutputStrategy(deduplicator, data_utils)
    output_manager = OutputManager(config_manager, output_strategy)
    output_processor = OutputProcessor(config_manager, output_manager)
    
    # Create mock transcription result
    transcription_result = {
        'success': True,
        'data': {
            'text': combined_text,
            'segments': segments,
            'metadata': {
                'total_segments': len(segments),
                'total_characters': len(combined_text),
                'audio_duration': segments[-1]['end'] if segments else 0,
                'model': 'ivrit-ai/whisper-large-v3-ct2',
                'engine': 'ctranslate2-whisper'
            }
        },
        'processing_info': {
            'mode': 'chunked',
            'chunks_processed': len(segments)
        },
        'processing_time': 9429.2,
        'timestamp': '2025-09-01T23:49:46'
    }
    
    # Create mock input metadata
    input_metadata = {
        'success': True,
        'data': {
            'audio_file': 'examples/audio/voice/פגישה רביעית.wav',
            'model': 'ivrit-ai/whisper-large-v3-ct2',
            'engine': 'ctranslate2-whisper'
        },
        'metadata': {
            'file_size': 0,
            'duration': segments[-1]['end'] if segments else 0
        },
        'validation': {'valid': True},
        'timestamp': '2025-09-01T23:49:46'
    }
    
    print(f"\n📝 Processing {len(segments)} segments with {len(combined_text)} characters...")
    
    # Process output
    try:
        result = output_processor.process_output(transcription_result, input_metadata)
        print(f"✅ Output processing completed: {result}")
        
        # Check output files
        output_dir = "output/transcriptions"
        latest_run = max(glob.glob(f"{output_dir}/run_*"), key=os.path.getctime)
        print(f"\n📁 Output saved to: {latest_run}")
        
        # List generated files
        for root, dirs, files in os.walk(latest_run):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f"   📄 {file} ({file_size:,} bytes)")
        
    except Exception as e:
        print(f"❌ Error processing output: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
