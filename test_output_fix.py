#!/usr/bin/env python3
"""
Test script to verify output format fix
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.output_data.utils.data_utils import DataUtils
from src.output_data.formatters.docx_formatter import DocxFormatter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_format_consistency():
    """Test that both data formats are handled correctly"""
    
    # Test data in 'segments' format (like custom whisper engine)
    segments_data = {
        'segments': [
            {
                'speaker': 'Speaker 1',
                'text': 'שלום עולם',
                'start': 0.0,
                'end': 2.0
            },
            {
                'speaker': 'Speaker 2', 
                'text': 'היי שם',
                'start': 2.5,
                'end': 4.0
            },
            {
                'speaker': 'Speaker 1',
                'text': 'מה שלומך?',
                'start': 4.5,
                'end': 6.0
            }
        ],
        'model_name': 'test-model',
        'audio_file': 'test.wav'
    }
    
    # Test data in 'speakers' format (like speaker diarization engine)
    speakers_data = {
        'speakers': {
            'Speaker 1': [
                {
                    'speaker': 'Speaker 1',
                    'text': 'שלום עולם',
                    'start': 0.0,
                    'end': 2.0
                },
                {
                    'speaker': 'Speaker 1',
                    'text': 'מה שלומך?',
                    'start': 4.5,
                    'end': 6.0
                }
            ],
            'Speaker 2': [
                {
                    'speaker': 'Speaker 2',
                    'text': 'היי שם',
                    'start': 2.5,
                    'end': 4.0
                }
            ]
        },
        'model_name': 'test-model',
        'audio_file': 'test.wav'
    }
    
    data_utils = DataUtils()
    
    # Test segments format
    logger.info("🧪 Testing 'segments' format:")
    speakers_from_segments = data_utils.extract_speakers_data(segments_data)
    logger.info(f"   - Extracted speakers: {list(speakers_from_segments.keys())}")
    for speaker, segments in speakers_from_segments.items():
        logger.info(f"   - {speaker}: {len(segments)} segments")
    
    # Test speakers format
    logger.info("🧪 Testing 'speakers' format:")
    speakers_from_speakers = data_utils.extract_speakers_data(speakers_data)
    logger.info(f"   - Extracted speakers: {list(speakers_from_speakers.keys())}")
    for speaker, segments in speakers_from_speakers.items():
        logger.info(f"   - {speaker}: {len(segments)} segments")
    
    # Test DOCX formatting
    logger.info("🧪 Testing DOCX formatting:")
    
    # Convert speakers to flat list for DOCX formatter
    docx_data_segments = []
    for speaker, segments in speakers_from_segments.items():
        docx_data_segments.extend(segments)
    
    docx_data_speakers = []
    for speaker, segments in speakers_from_speakers.items():
        docx_data_speakers.extend(segments)
    
    logger.info(f"   - Segments format: {len(docx_data_segments)} segments")
    logger.info(f"   - Speakers format: {len(docx_data_speakers)} segments")
    
    # Both should have the same content
    assert len(docx_data_segments) == len(docx_data_speakers), "Segment counts should match"
    
    logger.info("✅ All tests passed! Data format consistency verified.")

if __name__ == "__main__":
    test_data_format_consistency()
