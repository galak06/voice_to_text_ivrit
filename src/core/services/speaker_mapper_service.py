#!/usr/bin/env python3
"""
Speaker Mapper Service for Chunked Audio Processing
Maps speakers from full audio diarization to individual chunks
Handles overlapping regions intelligently using Pydantic models
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.models.speaker_recognition import (
    SpeakerSegment,
    ChunkSpeakerMapping,
    SpeakerOverlapStrategy,
    SpeakerOverlapResolution,
    ChunkSpeakerAnalysis
)
from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SpeakerMapperService:
    """
    Service for mapping speakers from full audio diarization to individual chunks
    
    This service follows SOLID principles:
    - Single Responsibility: Maps speakers to chunks
    - Open/Closed: Extensible for different overlap resolution strategies
    - Liskov Substitution: All overlap resolution strategies are interchangeable
    - Interface Segregation: Clean, focused interface
    - Dependency Inversion: Depends on ConfigManager abstraction
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the speaker mapper service"""
        self.config_manager = config_manager
        self.overlap_config = self._get_overlap_resolution_config()
        
        logger.info("🎯 Initializing SpeakerMapperService")
        logger.info(f"🔄 Overlap resolution strategy: {self.overlap_config.strategy}")
        logger.info(f"📊 Confidence threshold: {self.overlap_config.confidence_threshold}")
    
    def map_speakers_to_chunks(self, 
                              full_diarization: List[SpeakerSegment],
                              chunk_timestamps: List[Dict[str, Any]]) -> List[ChunkSpeakerMapping]:
        """
        Map speakers from full audio diarization to individual chunks
        
        Args:
            full_diarization: List of speaker segments from full audio
            chunk_timestamps: List of chunk metadata with timing information
            
        Returns:
            List of ChunkSpeakerMapping objects for each chunk
        """
        logger.info("🎯 Starting speaker-to-chunk mapping")
        logger.info(f"📊 Full diarization segments: {len(full_diarization)}")
        logger.info(f"🎵 Chunks to process: {len(chunk_timestamps)}")
        
        if not full_diarization:
            logger.warning("⚠️ No speaker segments provided for mapping")
            return self._create_empty_mappings(chunk_timestamps)
        
        if not chunk_timestamps:
            logger.warning("⚠️ No chunks provided for mapping")
            return []
        
        # Create initial mappings
        chunk_mappings = []
        for chunk_info in chunk_timestamps:
            chunk_mapping = self._map_speakers_for_chunk(
                full_diarization, chunk_info
            )
            chunk_mappings.append(chunk_mapping)
        
        # Resolve overlapping speaker conflicts
        resolved_mappings = self._resolve_overlapping_speakers(chunk_mappings)
        
        logger.info(f"✅ Speaker mapping completed: {len(resolved_mappings)} chunks mapped")
        return resolved_mappings
    
    def _map_speakers_for_chunk(self, 
                               full_diarization: List[SpeakerSegment],
                               chunk_info: Dict[str, Any]) -> ChunkSpeakerMapping:
        """Map speakers for a specific chunk"""
        chunk_id = chunk_info.get('filename', f"chunk_{chunk_info.get('chunk_number', 'unknown')}")
        chunk_start = chunk_info.get('start', 0.0)
        chunk_end = chunk_info.get('end', 0.0)
        
        # Find all speaker segments that overlap with this chunk
        overlapping_segments = self._find_overlapping_segments(
            full_diarization, chunk_start, chunk_end
        )
        
        if not overlapping_segments:
            # No speakers detected in this chunk
            return ChunkSpeakerMapping(
                chunk_id=chunk_id,
                start_time=chunk_start,
                end_time=chunk_end,
                primary_speaker="UNKNOWN",
                primary_confidence=0.0,
                overlap_resolution="no_speakers"
            )
        
        # Sort by overlap duration (most overlap first)
        overlapping_segments.sort(key=lambda x: x['overlap_duration'], reverse=True)
        
        # Primary speaker is the one with most overlap
        primary_segment = overlapping_segments[0]
        primary_speaker = primary_segment['segment'].speaker_id
        primary_confidence = primary_segment['segment'].confidence
        
        # Secondary speakers (if any)
        secondary_speakers = [
            seg['segment'].speaker_id 
            for seg in overlapping_segments[1:] 
            if seg['overlap_percentage'] > 0.3  # Only include if >30% overlap
        ]
        
        return ChunkSpeakerMapping(
            chunk_id=chunk_id,
            start_time=chunk_start,
            end_time=chunk_end,
            primary_speaker=primary_speaker,
            primary_confidence=primary_confidence,
            secondary_speakers=secondary_speakers,
            overlap_resolution="dominant_speaker"
        )
    
    def _find_overlapping_segments(self, 
                                 full_diarization: List[SpeakerSegment],
                                 chunk_start: float, 
                                 chunk_end: float) -> List[Dict[str, Any]]:
        """Find speaker segments that overlap with a chunk"""
        overlapping_segments = []
        
        for segment in full_diarization:
            # Check if segment overlaps with chunk
            if self._segments_overlap(segment, chunk_start, chunk_end):
                overlap_duration = self._calculate_overlap_duration(
                    segment, chunk_start, chunk_end
                )
                chunk_duration = chunk_end - chunk_start
                overlap_percentage = overlap_duration / chunk_duration if chunk_duration > 0 else 0
                
                overlapping_segments.append({
                    'segment': segment,
                    'overlap_duration': overlap_duration,
                    'overlap_percentage': overlap_percentage
                })
        
        return overlapping_segments
    
    def _resolve_overlapping_speakers(self, 
                                   chunk_mappings: List[ChunkSpeakerMapping]) -> List[ChunkSpeakerMapping]:
        """Resolve conflicts in overlapping regions between chunks"""
        logger.info("🔄 Resolving overlapping speaker conflicts")
        
        if len(chunk_mappings) <= 1:
            return chunk_mappings
        
        resolved_mappings = []
        
        for i, current_mapping in enumerate(chunk_mappings):
            if i > 0:
                # Check for overlap with previous chunk
                previous_mapping = resolved_mappings[i-1]
                
                if self._chunks_overlap(current_mapping, previous_mapping):
                    # Resolve overlap conflict
                    resolved_mapping = self._resolve_chunk_overlap(
                        current_mapping, previous_mapping
                    )
                    resolved_mappings.append(resolved_mapping)
                else:
                    resolved_mappings.append(current_mapping)
            else:
                resolved_mappings.append(current_mapping)
        
        return resolved_mappings
    
    def _resolve_chunk_overlap(self, 
                             current: ChunkSpeakerMapping, 
                             previous: ChunkSpeakerMapping) -> ChunkSpeakerMapping:
        """Resolve overlap between two chunks using configured strategy"""
        
        if self.overlap_config.strategy == SpeakerOverlapStrategy.DOMINANT_SPEAKER:
            return self._resolve_dominant_speaker(current, previous)
        elif self.overlap_config.strategy == SpeakerOverlapStrategy.WEIGHTED_AVERAGE:
            return self._resolve_weighted_average(current, previous)
        elif self.overlap_config.strategy == SpeakerOverlapStrategy.CONFIDENCE_BASED:
            return self._resolve_confidence_based(current, previous)
        elif self.overlap_config.strategy == SpeakerOverlapStrategy.TIME_BASED:
            return self._resolve_time_based(current, previous)
        else:
            # Default to dominant speaker
            return self._resolve_dominant_speaker(current, previous)
    
    def _resolve_dominant_speaker(self, 
                                current: ChunkSpeakerMapping, 
                                previous: ChunkSpeakerMapping) -> ChunkSpeakerMapping:
        """Resolve overlap using dominant speaker strategy"""
        overlap_start = max(current.start_time, previous.start_time)
        overlap_end = min(current.end_time, previous.end_time)
        overlap_duration = overlap_end - overlap_start
        
        # If overlap is significant, use weighted confidence
        if overlap_duration > self.overlap_config.min_overlap_duration:
            # Use the speaker with higher confidence in the overlap region
            if current.primary_confidence > previous.primary_confidence:
                resolved_speaker = current.primary_speaker
                resolved_confidence = current.primary_confidence
                overlap_resolution = "dominant_speaker_current"
            else:
                resolved_speaker = previous.primary_speaker
                resolved_confidence = previous.primary_confidence
                overlap_resolution = "dominant_speaker_previous"
            
            return ChunkSpeakerMapping(
                chunk_id=current.chunk_id,
                start_time=current.start_time,
                end_time=current.end_time,
                primary_speaker=resolved_speaker,
                primary_confidence=resolved_confidence,
                secondary_speakers=current.secondary_speakers,
                overlap_resolution=overlap_resolution
            )
        else:
            # Minimal overlap, keep current speaker
            return current
    
    def _resolve_weighted_average(self, 
                                current: ChunkSpeakerMapping, 
                                previous: ChunkSpeakerMapping) -> ChunkSpeakerMapping:
        """Resolve overlap using weighted average strategy"""
        overlap_start = max(current.start_time, previous.start_time)
        overlap_end = min(current.end_time, previous.end_time)
        overlap_duration = overlap_end - overlap_start
        
        if overlap_duration > self.overlap_config.min_overlap_duration:
            # Calculate weighted confidence based on overlap
            current_weight = overlap_duration / current.duration
            previous_weight = overlap_duration / previous.duration
            
            # Use weighted average for confidence
            weighted_confidence = (
                current.primary_confidence * current_weight +
                previous.primary_confidence * previous_weight
            ) / (current_weight + previous_weight)
            
            # Choose speaker based on weighted confidence
            if weighted_confidence > self.overlap_config.confidence_threshold:
                resolved_speaker = current.primary_speaker
            else:
                resolved_speaker = previous.primary_speaker
            
            return ChunkSpeakerMapping(
                chunk_id=current.chunk_id,
                start_time=current.start_time,
                end_time=current.end_time,
                primary_speaker=resolved_speaker,
                primary_confidence=weighted_confidence,
                secondary_speakers=current.secondary_speakers,
                overlap_resolution="weighted_average"
            )
        else:
            return current
    
    def _resolve_confidence_based(self, 
                                current: ChunkSpeakerMapping, 
                                previous: ChunkSpeakerMapping) -> ChunkSpeakerMapping:
        """Resolve overlap using confidence-based strategy"""
        overlap_start = max(current.start_time, previous.start_time)
        overlap_end = min(current.end_time, previous.end_time)
        overlap_duration = overlap_end - overlap_start
        
        if overlap_duration > self.overlap_config.min_overlap_duration:
            # Use confidence threshold to determine speaker
            if current.primary_confidence >= self.overlap_config.confidence_threshold:
                resolved_speaker = current.primary_speaker
                resolved_confidence = current.primary_confidence
                overlap_resolution = "confidence_based_current"
            elif previous.primary_confidence >= self.overlap_config.confidence_threshold:
                resolved_speaker = previous.primary_speaker
                resolved_confidence = previous.primary_confidence
                overlap_resolution = "confidence_based_previous"
            else:
                # Both below threshold, use the higher one
                if current.primary_confidence > previous.primary_confidence:
                    resolved_speaker = current.primary_speaker
                    resolved_confidence = current.primary_confidence
                    overlap_resolution = "confidence_based_higher"
                else:
                    resolved_speaker = previous.primary_speaker
                    resolved_confidence = previous.primary_confidence
                    overlap_resolution = "confidence_based_higher"
            
            return ChunkSpeakerMapping(
                chunk_id=current.chunk_id,
                start_time=current.start_time,
                end_time=current.end_time,
                primary_speaker=resolved_speaker,
                primary_confidence=resolved_confidence,
                secondary_speakers=current.secondary_speakers,
                overlap_resolution=overlap_resolution
            )
        else:
            return current
    
    def _resolve_time_based(self, 
                           current: ChunkSpeakerMapping, 
                           previous: ChunkSpeakerMapping) -> ChunkSpeakerMapping:
        """Resolve overlap using time-based strategy"""
        overlap_start = max(current.start_time, previous.start_time)
        overlap_end = min(current.end_time, previous.end_time)
        overlap_duration = overlap_end - overlap_start
        
        if overlap_duration > self.overlap_config.min_overlap_duration:
            # Use time-based resolution (prefer current chunk for recent time)
            time_weight = self.overlap_config.overlap_weight_factor
            
            if time_weight > 0.5:
                # Prefer current chunk
                resolved_speaker = current.primary_speaker
                resolved_confidence = current.primary_confidence
                overlap_resolution = "time_based_current"
            else:
                # Prefer previous chunk
                resolved_speaker = previous.primary_speaker
                resolved_confidence = previous.primary_confidence
                overlap_resolution = "time_based_previous"
            
            return ChunkSpeakerMapping(
                chunk_id=current.chunk_id,
                start_time=current.start_time,
                end_time=current.end_time,
                primary_speaker=resolved_speaker,
                primary_confidence=resolved_confidence,
                secondary_speakers=current.secondary_speakers,
                overlap_resolution=overlap_resolution
            )
        else:
            return current
    
    def _create_empty_mappings(self, chunk_timestamps: List[Dict[str, Any]]) -> List[ChunkSpeakerMapping]:
        """Create empty speaker mappings when no diarization data is available"""
        empty_mappings = []
        
        for chunk_info in chunk_timestamps:
            chunk_id = chunk_info.get('filename', f"chunk_{chunk_info.get('chunk_number', 'unknown')}")
            chunk_start = chunk_info.get('start', 0.0)
            chunk_end = chunk_info.get('end', 0.0)
            
            empty_mapping = ChunkSpeakerMapping(
                chunk_id=chunk_id,
                start_time=chunk_start,
                end_time=chunk_end,
                primary_speaker="UNKNOWN",
                primary_confidence=0.0,
                overlap_resolution="no_diarization_data"
            )
            empty_mappings.append(empty_mapping)
        
        return empty_mappings
    
    def _chunks_overlap(self, chunk1: ChunkSpeakerMapping, chunk2: ChunkSpeakerMapping) -> bool:
        """Check if two chunks overlap"""
        return (chunk1.start_time < chunk2.end_time and 
                chunk2.start_time < chunk1.end_time)
    
    def _segments_overlap(self, segment: SpeakerSegment, start: float, end: float) -> bool:
        """Check if a speaker segment overlaps with a time range"""
        return segment.start_time < end and segment.end_time > start
    
    def _calculate_overlap_duration(self, segment: SpeakerSegment, start: float, end: float) -> float:
        """Calculate overlap duration between segment and time range"""
        overlap_start = max(segment.start_time, start)
        overlap_end = min(segment.end_time, end)
        return max(0, overlap_end - overlap_start)
    
    def _get_overlap_resolution_config(self) -> SpeakerOverlapResolution:
        """Get overlap resolution configuration from ConfigManager"""
        try:
            # Try to get from speaker diarization config
            if (hasattr(self.config_manager.config, 'speaker') and 
                hasattr(self.config_manager.config.speaker, 'overlap_resolution')):
                return self.config_manager.config.speaker.overlap_resolution
            
            # Try to get from chunking config
            if (hasattr(self.config_manager.config, 'chunking') and 
                hasattr(self.config_manager.config.chunking, 'overlap_resolution')):
                return self.config_manager.config.chunking.overlap_resolution
            
            # Return default configuration
            return SpeakerOverlapResolution()
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load overlap resolution config: {e}")
            return SpeakerOverlapResolution()
    
    def analyze_chunk_speakers(self, 
                             chunk_mappings: List[ChunkSpeakerMapping]) -> List[ChunkSpeakerAnalysis]:
        """Analyze speaker patterns in chunks"""
        analyses = []
        
        for mapping in chunk_mappings:
            # Create analysis for each chunk
            analysis = ChunkSpeakerAnalysis(
                chunk_id=mapping.chunk_id,
                total_speakers_detected=1 + len(mapping.secondary_speakers),
                primary_speaker=mapping.primary_speaker,
                speaker_segments=[],  # Would need actual segment data
                overlap_confidence=mapping.primary_confidence,
                processing_metadata={
                    'overlap_resolution': mapping.overlap_resolution,
                    'has_multiple_speakers': mapping.has_multiple_speakers
                }
            )
            analyses.append(analysis)
        
        return analyses
