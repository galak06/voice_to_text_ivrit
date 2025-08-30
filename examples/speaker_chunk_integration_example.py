#!/usr/bin/env python3
"""
Example: Speaker Recognition with Overlapping Chunks
Demonstrates the Pydantic-based solution for handling overlapping chunks and speaker recognition
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models.speaker_recognition import (
    SpeakerSegment,
    ChunkSpeakerMapping,
    SpeakerOverlapStrategy,
    SpeakerOverlapResolution
)
from src.core.services.speaker_mapper_service import SpeakerMapperService
from src.core.processors.enhanced_chunk_processor import EnhancedChunkProcessor
from src.utils.config_manager import ConfigManager


def create_sample_speaker_segments() -> List[SpeakerSegment]:
    """Create sample speaker segments for demonstration"""
    return [
        SpeakerSegment(
            speaker_id="SPEAKER_00",
            start_time=0.0,
            end_time=15.0,
            confidence=0.95,
            duration=15.0
        ),
        SpeakerSegment(
            speaker_id="SPEAKER_01",
            start_time=15.0,
            end_time=45.0,
            confidence=0.92,
            duration=30.0
        ),
        SpeakerSegment(
            speaker_id="SPEAKER_00",
            start_time=45.0,
            end_time=75.0,
            confidence=0.88,
            duration=30.0
        ),
        SpeakerSegment(
            speaker_id="SPEAKER_01",
            start_time=75.0,
            end_time=90.0,
            confidence=0.94,
            duration=15.0
        )
    ]


def create_sample_chunks() -> List[Dict[str, Any]]:
    """Create sample chunk data for demonstration"""
    return [
        {
            'filename': 'chunk_001_0s_30s',
            'start': 0.0,
            'end': 30.0,
            'duration': 30.0,
            'chunk_number': 1,
            'chunking_strategy': 'overlapping',
            'overlap_start': 0.0,
            'overlap_end': 35.0,
            'stride_length': 5.0
        },
        {
            'filename': 'chunk_002_25s_55s',
            'start': 25.0,
            'end': 55.0,
            'duration': 30.0,
            'chunk_number': 2,
            'chunking_strategy': 'overlapping',
            'overlap_start': 20.0,
            'overlap_end': 60.0,
            'stride_length': 5.0
        },
        {
            'filename': 'chunk_003_50s_80s',
            'start': 50.0,
            'end': 80.0,
            'duration': 30.0,
            'chunk_number': 3,
            'chunking_strategy': 'overlapping',
            'overlap_start': 45.0,
            'overlap_end': 85.0,
            'stride_length': 5.0
        },
        {
            'filename': 'chunk_004_75s_105s',
            'start': 75.0,
            'end': 105.0,
            'duration': 30.0,
            'chunk_number': 4,
            'chunking_strategy': 'overlapping',
            'overlap_start': 70.0,
            'overlap_end': 110.0,
            'stride_length': 5.0
        }
    ]


def demonstrate_speaker_mapping():
    """Demonstrate speaker mapping with overlapping chunks"""
    print("🎯 DEMONSTRATING SPEAKER MAPPING WITH OVERLAPPING CHUNKS")
    print("=" * 60)
    
    # Create sample data
    speaker_segments = create_sample_speaker_segments()
    chunks_data = create_sample_chunks()
    
    print(f"📊 Sample Data:")
    print(f"   🎤 Speaker segments: {len(speaker_segments)}")
    print(f"   🎵 Audio chunks: {len(chunks_data)}")
    print(f"   🔄 Overlap between chunks: 5 seconds")
    print()
    
    # Show speaker timeline
    print("🎤 SPEAKER TIMELINE:")
    for segment in speaker_segments:
        print(f"   {segment.start_time:5.1f}s - {segment.end_time:5.1f}s: {segment.speaker_id} (confidence: {segment.confidence:.2f})")
    print()
    
    # Show chunk timeline
    print("🎵 CHUNK TIMELINE:")
    for chunk in chunks_data:
        print(f"   {chunk['start']:5.1f}s - {chunk['end']:5.1f}s: {chunk['filename']}")
    print()
    
    # Initialize services
    config_manager = ConfigManager()
    speaker_mapper = SpeakerMapperService(config_manager)
    
    # Map speakers to chunks
    print("🔄 MAPPING SPEAKERS TO CHUNKS...")
    start_time = time.time()
    
    chunk_mappings = speaker_mapper.map_speakers_to_chunks(speaker_segments, chunks_data)
    
    mapping_time = time.time() - start_time
    print(f"✅ Speaker mapping completed in {mapping_time:.2f}s")
    print()
    
    # Display results
    print("📊 SPEAKER MAPPING RESULTS:")
    print("-" * 60)
    
    for mapping in chunk_mappings:
        print(f"🎵 {mapping.chunk_id}:")
        print(f"   ⏰ Time: {mapping.start_time:5.1f}s - {mapping.end_time:5.1f}s")
        print(f"   🎤 Primary: {mapping.primary_speaker} (confidence: {mapping.primary_confidence:.2f})")
        if mapping.secondary_speakers:
            print(f"   🎤 Secondary: {', '.join(mapping.secondary_speakers)}")
        print(f"   🔄 Overlap resolution: {mapping.overlap_resolution}")
        print()
    
    return chunk_mappings


def demonstrate_enhanced_processing(chunk_mappings: List[ChunkSpeakerMapping]):
    """Demonstrate enhanced chunk processing with speaker recognition"""
    print("🚀 DEMONSTRATING ENHANCED CHUNK PROCESSING")
    print("=" * 60)
    
    # Create sample chunks data
    chunks_data = create_sample_chunks()
    
    # Initialize enhanced processor
    config_manager = ConfigManager()
    enhanced_processor = EnhancedChunkProcessor(config_manager)
    
    # Process chunks with speaker information
    print("🔄 Processing chunks with speaker recognition...")
    start_time = time.time()
    
    processed_chunks = enhanced_processor.process_chunks_with_speakers(
        chunks_data, 
        create_sample_speaker_segments()
    )
    
    processing_time = time.time() - start_time
    print(f"✅ Enhanced processing completed in {processing_time:.2f}s")
    print()
    
    # Display results
    print("📊 ENHANCED PROCESSING RESULTS:")
    print("-" * 60)
    
    for chunk in processed_chunks:
        chunk_info = chunk['chunk_info']
        speaker_info = chunk['speaker_recognition']
        
        print(f"🎵 {chunk_info['chunk_id']}:")
        print(f"   ⏰ Time: {chunk_info['start_time']:5.1f}s - {chunk_info['end_time']:5.1f}s")
        print(f"   🎤 Speaker: {speaker_info['primary_speaker']} (confidence: {speaker_info['primary_confidence']:.2f})")
        print(f"   🔄 Resolution: {speaker_info['overlap_resolution']}")
        print(f"   📝 Processing: {chunk['processing_type']}")
        print()
    
    return processed_chunks


def demonstrate_overlap_resolution_strategies():
    """Demonstrate different overlap resolution strategies"""
    print("🔄 DEMONSTRATING OVERLAP RESOLUTION STRATEGIES")
    print("=" * 60)
    
    # Create sample data
    speaker_segments = create_sample_speaker_segments()
    chunks_data = create_sample_chunks()
    
    # Initialize services
    config_manager = ConfigManager()
    speaker_mapper = SpeakerMapperService(config_manager)
    
    # Test different strategies
    strategies = [
        SpeakerOverlapStrategy.DOMINANT_SPEAKER,
        SpeakerOverlapStrategy.WEIGHTED_AVERAGE,
        SpeakerOverlapStrategy.CONFIDENCE_BASED,
        SpeakerOverlapStrategy.TIME_BASED
    ]
    
    for strategy in strategies:
        print(f"🎯 Testing strategy: {strategy.value}")
        print("-" * 40)
        
        # Create custom overlap resolution config
        overlap_config = SpeakerOverlapResolution(
            strategy=strategy,
            confidence_threshold=0.6,
            min_overlap_duration=0.5,
            smooth_transitions=True,
            overlap_weight_factor=0.7
        )
        
        # Override the default config for testing
        speaker_mapper.overlap_config = overlap_config
        
        # Map speakers
        start_time = time.time()
        chunk_mappings = speaker_mapper.map_speakers_to_chunks(speaker_segments, chunks_data)
        mapping_time = time.time() - start_time
        
        # Count overlap resolution methods
        resolution_counts = {}
        for mapping in chunk_mappings:
            resolution = mapping.overlap_resolution
            resolution_counts[resolution] = resolution_counts.get(resolution, 0) + 1
        
        print(f"   ⏱️  Processing time: {mapping_time:.2f}s")
        print(f"   📊 Resolution methods:")
        for resolution, count in resolution_counts.items():
            print(f"      {resolution}: {count}")
        print()
    
    # Reset to default config
    speaker_mapper.overlap_config = SpeakerOverlapResolution()


def demonstrate_statistics_and_analysis(chunk_mappings: List[ChunkSpeakerMapping]):
    """Demonstrate statistics and analysis capabilities"""
    print("📊 DEMONSTRATING STATISTICS AND ANALYSIS")
    print("=" * 60)
    
    # Initialize enhanced processor
    config_manager = ConfigManager()
    enhanced_processor = EnhancedChunkProcessor(config_manager)
    
    # Get speaker statistics
    stats = enhanced_processor.get_speaker_statistics(chunk_mappings)
    
    print("📈 SPEAKER STATISTICS:")
    print(f"   📊 Total chunks: {stats['total_chunks']}")
    print(f"   🎤 Total speakers: {stats['total_speakers']}")
    print(f"   🔄 Overlapping chunks: {stats['overlap_statistics']['overlapping_chunks']}")
    print(f"   📊 Overlap percentage: {stats['overlap_statistics']['overlap_percentage']:.1f}%")
    print(f"   🎯 Average confidence: {stats['average_confidence']:.2f}")
    print()
    
    print("🎤 SPEAKER DISTRIBUTION:")
    for speaker, count in stats['speaker_distribution'].items():
        percentage = (count / stats['total_chunks']) * 100
        print(f"   {speaker}: {count} chunks ({percentage:.1f}%)")
    print()
    
    print("🔄 OVERLAP RESOLUTION METHODS:")
    for method, count in stats['overlap_statistics']['resolution_methods'].items():
        percentage = (count / stats['total_chunks']) * 100
        print(f"   {method}: {count} chunks ({percentage:.1f}%)")
    print()
    
    # Analyze chunk speakers
    analyses = enhanced_processor.analyze_chunk_speakers(chunk_mappings)
    
    print("🔍 CHUNK ANALYSIS:")
    for analysis in analyses:
        print(f"   🎵 {analysis.chunk_id}:")
        print(f"      🎤 Speakers detected: {analysis.total_speakers_detected}")
        print(f"      🎯 Primary: {analysis.primary_speaker}")
        print(f"      🔄 Has overlap: {analysis.has_overlap}")
        print(f"      📊 Overlap confidence: {analysis.overlap_confidence:.2f}")
        print()


def demonstrate_export_and_validation(chunk_mappings: List[ChunkSpeakerMapping]):
    """Demonstrate export and validation capabilities"""
    print("📤 DEMONSTRATING EXPORT AND VALIDATION")
    print("=" * 60)
    
    # Initialize enhanced processor
    config_manager = ConfigManager()
    enhanced_processor = EnhancedChunkProcessor(config_manager)
    
    # Export to different formats
    print("📤 EXPORTING SPEAKER MAPPINGS:")
    
    # JSON export
    json_export = enhanced_processor.export_speaker_mappings(chunk_mappings, 'json')
    print(f"   📄 JSON export length: {len(json_export)} characters")
    
    # CSV export
    csv_export = enhanced_processor.export_speaker_mappings(chunk_mappings, 'csv')
    print(f"   📊 CSV export length: {len(csv_export)} characters")
    
    # Save exports to files
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)
    
    json_file = output_dir / "speaker_mappings.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json_export)
    
    csv_file = output_dir / "speaker_mappings.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(csv_export)
    
    print(f"   💾 Exports saved to:")
    print(f"      📄 JSON: {json_file}")
    print(f"      📊 CSV: {csv_file}")
    print()
    
    # Validate mappings
    print("✅ VALIDATING SPEAKER MAPPINGS:")
    validation_errors = enhanced_processor.validate_chunk_speaker_mappings(chunk_mappings)
    
    if validation_errors:
        print("   ❌ Validation errors found:")
        for error in validation_errors:
            print(f"      {error}")
    else:
        print("   ✅ All speaker mappings are valid!")
    print()


def main():
    """Main demonstration function"""
    print("🎯 SPEAKER RECOGNITION WITH OVERLAPPING CHUNKS DEMONSTRATION")
    print("=" * 80)
    print("This example demonstrates the Pydantic-based solution for handling")
    print("overlapping chunks and speaker recognition intelligently.")
    print()
    
    try:
        # Step 1: Basic speaker mapping
        chunk_mappings = demonstrate_speaker_mapping()
        
        # Step 2: Enhanced processing
        processed_chunks = demonstrate_enhanced_processing(chunk_mappings)
        
        # Step 3: Overlap resolution strategies
        demonstrate_overlap_resolution_strategies()
        
        # Step 4: Statistics and analysis
        demonstrate_statistics_and_analysis(chunk_mappings)
        
        # Step 5: Export and validation
        demonstrate_export_and_validation(chunk_mappings)
        
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("Key benefits of this Pydantic-based solution:")
        print("✅ Handles overlapping chunks intelligently")
        print("✅ Multiple overlap resolution strategies")
        print("✅ Comprehensive validation and error handling")
        print("✅ Rich analytics and statistics")
        print("✅ Multiple export formats")
        print("✅ Follows SOLID principles")
        print("✅ Type-safe with Pydantic models")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
