#!/usr/bin/env python3
"""
Enhanced Chunk Processor with Speaker Recognition
Integrates speaker recognition with chunk processing using Pydantic models
Handles overlapping chunks and speaker mapping intelligently
"""

import logging
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from src.models.speaker_recognition import (
    SpeakerSegment,
    ChunkSpeakerMapping,
    ChunkSpeakerAnalysis,
    SpeakerRecognitionResult
)
from src.core.services.speaker_mapper_service import SpeakerMapperService
from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class EnhancedChunkProcessor:
    """
    Enhanced chunk processor that integrates speaker recognition
    
    This class follows SOLID principles:
    - Single Responsibility: Process chunks with speaker information
    - Open/Closed: Extensible for different processing strategies
    - Liskov Substitution: All processing strategies are interchangeable
    - Interface Segregation: Clean, focused interface
    - Dependency Inversion: Depends on service abstractions
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the enhanced chunk processor"""
        self.config_manager = config_manager
        self.speaker_mapper_service = SpeakerMapperService(config_manager)
        
        logger.info("🚀 Initializing EnhancedChunkProcessor")
        logger.info(f"🎤 Speaker mapper service: {type(self.speaker_mapper_service).__name__}")
    
    def process_chunks_with_speakers(self, 
                                   chunks_data: List[Dict[str, Any]],
                                   speaker_segments: Optional[List[SpeakerSegment]] = None) -> List[Dict[str, Any]]:
        """
        Process chunks with integrated speaker recognition
        
        Args:
            chunks_data: List of chunk data dictionaries
            speaker_segments: Optional list of speaker segments from full audio
            
        Returns:
            List of processed chunks with speaker information
        """
        logger.info("🎯 Starting enhanced chunk processing with speaker recognition")
        logger.info(f"📊 Chunks to process: {len(chunks_data)}")
        logger.info(f"🎤 Speaker segments available: {len(speaker_segments) if speaker_segments else 0}")
        
        if not chunks_data:
            logger.warning("⚠️ No chunks provided for processing")
            return []
        
        # Map speakers to chunks if speaker data is available
        chunk_speaker_mappings = []
        if speaker_segments:
            chunk_speaker_mappings = self.speaker_mapper_service.map_speakers_to_chunks(
                speaker_segments, chunks_data
            )
            logger.info(f"✅ Speaker mapping completed: {len(chunk_speaker_mappings)} chunks mapped")
        else:
            logger.info("ℹ️ No speaker segments provided, processing without speaker recognition")
        
        # Process each chunk with speaker information
        processed_chunks = []
        for i, chunk_data in enumerate(chunks_data):
            try:
                processed_chunk = self._process_single_chunk(
                    chunk_data, 
                    chunk_speaker_mappings[i] if chunk_speaker_mappings else None,
                    i + 1,
                    len(chunks_data)
                )
                processed_chunks.append(processed_chunk)
                
            except Exception as e:
                logger.error(f"❌ Error processing chunk {i + 1}: {e}")
                # Create error chunk result
                error_chunk = self._create_error_chunk(chunk_data, str(e), i + 1)
                processed_chunks.append(error_chunk)
        
        logger.info(f"✅ Enhanced chunk processing completed: {len(processed_chunks)} chunks processed")
        return processed_chunks
    
    def _process_single_chunk(self, 
                             chunk_data: Dict[str, Any],
                             speaker_mapping: Optional[ChunkSpeakerMapping],
                             chunk_index: int,
                             total_chunks: int) -> Dict[str, Any]:
        """Process a single chunk with speaker information"""
        chunk_start_time = time.time()
        
        logger.info(f"🎵 Processing chunk {chunk_index}/{total_chunks}: {chunk_data.get('filename', 'unknown')}")
        
        # Extract chunk information
        chunk_info = self._extract_chunk_info(chunk_data)
        
        # Process transcription (placeholder - would integrate with actual transcription engine)
        transcription_result = self._process_chunk_transcription(chunk_data)
        
        # Combine with speaker information
        enhanced_chunk = self._combine_chunk_and_speaker_data(
            chunk_info, transcription_result, speaker_mapping
        )
        
        # Add processing metadata
        processing_time = time.time() - chunk_start_time
        enhanced_chunk['processing_metadata'] = {
            'processing_time': processing_time,
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'processing_method': 'enhanced_with_speakers',
            'speaker_recognition_enabled': speaker_mapping is not None
        }
        
        logger.info(f"✅ Chunk {chunk_index} processed in {processing_time:.2f}s")
        return enhanced_chunk
    
    def _extract_chunk_info(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate chunk information"""
        chunk_info = {
            'chunk_id': chunk_data.get('filename', f"chunk_{chunk_data.get('chunk_number', 'unknown')}"),
            'start_time': chunk_data.get('start', 0.0),
            'end_time': chunk_data.get('end', 0.0),
            'duration': chunk_data.get('duration', 0.0),
            'chunk_number': chunk_data.get('chunk_number', 0),
            'chunking_strategy': chunk_data.get('chunking_strategy', 'unknown'),
            'overlap_info': {
                'overlap_start': chunk_data.get('overlap_start', 0.0),
                'overlap_end': chunk_data.get('overlap_end', 0.0),
                'stride_length': chunk_data.get('stride_length', 0.0)
            }
        }
        
        # Validate timing information
        if chunk_info['end_time'] <= chunk_info['start_time']:
            raise ValueError(f"Invalid chunk timing: end_time ({chunk_info['end_time']}) <= start_time ({chunk_info['start_time']})")
        
        if chunk_info['duration'] <= 0:
            chunk_info['duration'] = chunk_info['end_time'] - chunk_info['start_time']
        
        return chunk_info
    
    def _process_chunk_transcription(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process chunk transcription (placeholder for actual transcription engine integration)"""
        # This would integrate with your existing transcription engine
        # For now, return placeholder data
        return {
            'text': f"Transcription for {chunk_data.get('filename', 'chunk')}",
            'segments': [],
            'language': 'he',
            'confidence': 0.95,
            'processing_status': 'completed'
        }
    
    def _combine_chunk_and_speaker_data(self, 
                                       chunk_info: Dict[str, Any],
                                       transcription_result: Dict[str, Any],
                                       speaker_mapping: Optional[ChunkSpeakerMapping]) -> Dict[str, Any]:
        """Combine chunk information with speaker and transcription data"""
        
        if speaker_mapping:
            # Enhanced chunk with speaker information
            enhanced_chunk = {
                'chunk_info': chunk_info,
                'transcription': transcription_result,
                'speaker_recognition': {
                    'primary_speaker': speaker_mapping.primary_speaker,
                    'primary_confidence': speaker_mapping.primary_confidence,
                    'secondary_speakers': speaker_mapping.secondary_speakers,
                    'overlap_resolution': speaker_mapping.overlap_resolution,
                    'has_multiple_speakers': speaker_mapping.has_multiple_speakers,
                    'speaker_mapping_id': speaker_mapping.chunk_id
                },
                'processing_type': 'enhanced_with_speakers'
            }
        else:
            # Basic chunk without speaker information
            enhanced_chunk = {
                'chunk_info': chunk_info,
                'transcription': transcription_result,
                'speaker_recognition': {
                    'primary_speaker': 'UNKNOWN',
                    'primary_confidence': 0.0,
                    'secondary_speakers': [],
                    'overlap_resolution': 'no_speaker_data',
                    'has_multiple_speakers': False,
                    'speaker_mapping_id': None
                },
                'processing_type': 'basic_without_speakers'
            }
        
        return enhanced_chunk
    
    def _create_error_chunk(self, 
                           chunk_data: Dict[str, Any], 
                           error_message: str, 
                           chunk_index: int) -> Dict[str, Any]:
        """Create an error chunk result when processing fails"""
        return {
            'chunk_info': {
                'chunk_id': chunk_data.get('filename', f"chunk_{chunk_index}"),
                'start_time': chunk_data.get('start', 0.0),
                'end_time': chunk_data.get('end', 0.0),
                'duration': chunk_data.get('duration', 0.0),
                'chunk_number': chunk_index,
                'chunking_strategy': 'error',
                'overlap_info': {}
            },
            'transcription': {
                'text': f"ERROR: {error_message}",
                'segments': [],
                'language': 'unknown',
                'confidence': 0.0,
                'processing_status': 'error'
            },
            'speaker_recognition': {
                'primary_speaker': 'ERROR',
                'primary_confidence': 0.0,
                'secondary_speakers': [],
                'overlap_resolution': 'processing_error',
                'has_multiple_speakers': False,
                'speaker_mapping_id': None
            },
            'processing_type': 'error',
            'processing_metadata': {
                'processing_time': 0.0,
                'chunk_index': chunk_index,
                'total_chunks': 0,
                'processing_method': 'error',
                'speaker_recognition_enabled': False,
                'error_message': error_message
            }
        }
    
    def analyze_chunk_speakers(self, 
                             chunk_speaker_mappings: List[ChunkSpeakerMapping]) -> List[ChunkSpeakerAnalysis]:
        """Analyze speaker patterns in chunks"""
        return self.speaker_mapper_service.analyze_chunk_speakers(chunk_speaker_mappings)
    
    def get_speaker_statistics(self, 
                             chunk_speaker_mappings: List[ChunkSpeakerMapping]) -> Dict[str, Any]:
        """Get statistics about speaker distribution across chunks"""
        if not chunk_speaker_mappings:
            return {
                'total_chunks': 0,
                'total_speakers': 0,
                'speaker_distribution': {},
                'overlap_statistics': {}
            }
        
        # Count speakers
        speaker_counts = {}
        overlap_resolution_counts = {}
        
        for mapping in chunk_speaker_mappings:
            # Count primary speakers
            primary = mapping.primary_speaker
            speaker_counts[primary] = speaker_counts.get(primary, 0) + 1
            
            # Count overlap resolution methods
            resolution = mapping.overlap_resolution
            overlap_resolution_counts[resolution] = overlap_resolution_counts.get(resolution, 0) + 1
        
        # Calculate statistics
        total_chunks = len(chunk_speaker_mappings)
        total_speakers = len(speaker_counts)
        
        # Calculate overlap percentage
        overlapping_chunks = sum(1 for m in chunk_speaker_mappings if 'overlap' in m.overlap_resolution.lower())
        overlap_percentage = (overlapping_chunks / total_chunks) * 100 if total_chunks > 0 else 0
        
        return {
            'total_chunks': total_chunks,
            'total_speakers': total_speakers,
            'speaker_distribution': speaker_counts,
            'overlap_statistics': {
                'overlapping_chunks': overlapping_chunks,
                'overlap_percentage': overlap_percentage,
                'resolution_methods': overlap_resolution_counts
            },
            'average_confidence': sum(m.primary_confidence for m in chunk_speaker_mappings) / total_chunks if total_chunks > 0 else 0
        }
    
    def export_speaker_mappings(self, 
                              chunk_speaker_mappings: List[ChunkSpeakerMapping],
                              output_format: str = 'json') -> str:
        """Export speaker mappings in specified format"""
        if output_format.lower() == 'json':
            import json
            return json.dumps([mapping.model_dump() for mapping in chunk_speaker_mappings], indent=2)
        elif output_format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'chunk_id', 'start_time', 'end_time', 'duration',
                'primary_speaker', 'primary_confidence', 'secondary_speakers',
                'overlap_resolution', 'processing_timestamp'
            ])
            
            # Write data
            for mapping in chunk_speaker_mappings:
                writer.writerow([
                    mapping.chunk_id,
                    mapping.start_time,
                    mapping.end_time,
                    mapping.duration,
                    mapping.primary_speaker,
                    mapping.primary_confidence,
                    ';'.join(mapping.secondary_speakers),
                    mapping.overlap_resolution,
                    mapping.processing_timestamp.isoformat()
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def validate_chunk_speaker_mappings(self, 
                                      chunk_speaker_mappings: List[ChunkSpeakerMapping]) -> List[str]:
        """Validate chunk speaker mappings and return validation errors"""
        validation_errors = []
        
        for i, mapping in enumerate(chunk_speaker_mappings):
            try:
                # Validate the Pydantic model
                mapping.model_validate(mapping.model_dump())
            except Exception as e:
                validation_errors.append(f"Chunk {i + 1} ({mapping.chunk_id}): {e}")
            
            # Additional business logic validation
            if mapping.start_time >= mapping.end_time:
                validation_errors.append(f"Chunk {i + 1} ({mapping.chunk_id}): Invalid timing (start >= end)")
            
            if mapping.primary_confidence < 0 or mapping.primary_confidence > 1:
                validation_errors.append(f"Chunk {i + 1} ({mapping.chunk_id}): Invalid confidence score")
        
        return validation_errors
