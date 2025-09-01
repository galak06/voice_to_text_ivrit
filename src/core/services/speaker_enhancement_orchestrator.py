#!/usr/bin/env python3
"""
Speaker Enhancement Orchestrator
Orchestrates the speaker diarization enhancement workflow following SOLID principles
"""

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.models.transcription_results import TranscriptionResult, TranscriptionSegment
from src.core.orchestrator.transcription_service import TranscriptionService as SpeakerTranscriptionService

logger = logging.getLogger(__name__)


class SpeakerEnhancementInterface(ABC):
    """Interface for speaker enhancement strategies following Interface Segregation Principle"""
    
    @abstractmethod
    def enhance_transcription(self, transcription_result: TranscriptionResult, audio_file_path: str) -> TranscriptionResult:
        """Enhance transcription with speaker diarization"""
        pass


@dataclass
class EnhancementContext:
    """Context for speaker enhancement following Single Responsibility Principle"""
    audio_file_path: str
    speaker_config: Any
    enhancement_strategy: str
    preserve_original_chunks: bool = True


class ChunkedSpeakerEnhancementStrategy(SpeakerEnhancementInterface):
    """Strategy for enhancing chunked transcriptions with speaker diarization"""
    
    def __init__(self, speaker_service: SpeakerTranscriptionService):
        self.speaker_service = speaker_service
    
    def enhance_transcription(self, transcription_result: TranscriptionResult, audio_file_path: str) -> TranscriptionResult:
        """Enhance chunked transcription with speaker diarization"""
        try:
            logger.info("🎯 Applying chunked speaker enhancement strategy")
            
            # Extract all segments from the transcription result
            all_segments = self._extract_all_segments(transcription_result)
            
            if not all_segments:
                logger.warning("⚠️ No segments found for enhancement")
                return transcription_result
            
            # Perform speaker diarization on the full audio
            speaker_segments = self.speaker_service._perform_speaker_diarization(audio_file_path)
            
            if not speaker_segments:
                logger.warning("⚠️ No speaker segments detected, returning original result")
                return transcription_result
            
            # Enhance the result with speaker information
            enhanced_result = self._enhance_with_speaker_segments(transcription_result, speaker_segments, all_segments)
            
            logger.info(f"✅ Speaker enhancement completed: {len(enhanced_result.speakers)} speakers detected")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error in chunked speaker enhancement: {e}")
            return transcription_result
    
    def _extract_all_segments(self, transcription_result: TranscriptionResult) -> List[TranscriptionSegment]:
        """Extract all segments from transcription result following Single Responsibility Principle"""
        all_segments = []
        
        if hasattr(transcription_result, 'speakers') and transcription_result.speakers:
            for segments in transcription_result.speakers.values():
                all_segments.extend(segments)
        
        return all_segments
    
    def _enhance_with_speaker_segments(self, transcription_result: TranscriptionResult, 
                                     speaker_segments: List[tuple], 
                                     all_segments: List[TranscriptionSegment]) -> TranscriptionResult:
        """Enhance transcription with speaker segments following Single Responsibility Principle"""
        from src.core.engines.consolidated_transcription_engine import ConsolidatedTranscriptionEngine
        
        # Create a temporary engine instance for enhancement
        temp_config = getattr(transcription_result, 'config', None)
        temp_engine = ConsolidatedTranscriptionEngine(temp_config) if temp_config else None
        
        if temp_engine and hasattr(temp_engine, '_enhance_result_with_speakers'):
            # Use the enhanced method we implemented
            return temp_engine._enhance_result_with_speakers(transcription_result, speaker_segments)
        else:
            # Fallback enhancement
            return self._fallback_enhancement(transcription_result, speaker_segments, all_segments)
    
    def _fallback_enhancement(self, transcription_result: TranscriptionResult, 
                             speaker_segments: List[tuple], 
                             all_segments: List[TranscriptionSegment]) -> TranscriptionResult:
        """Fallback enhancement when the main method is not available"""
        logger.info("🔄 Using fallback speaker enhancement")
        
        # Create enhanced speakers dictionary
        enhanced_speakers = {}
        
        # Map segments to speakers based on time overlap
        for i, (start_time, end_time) in enumerate(speaker_segments):
            speaker_id = f"speaker_{i + 1}"
            speaker_segments_list = []
            
            for segment in all_segments:
                if self._is_segment_overlapping(segment, start_time, end_time):
                    # Create enhanced segment with speaker information
                    enhanced_segment = TranscriptionSegment(
                        start=segment.start,
                        end=segment.end,
                        text=segment.text,
                        speaker=speaker_id,
                        words=getattr(segment, 'words', None),
                        confidence=getattr(segment, 'confidence', None),
                        chunk_file=getattr(segment, 'chunk_file', None),
                        chunk_number=getattr(segment, 'chunk_number', None)
                    )
                    speaker_segments_list.append(enhanced_segment)
            
            if speaker_segments_list:
                enhanced_speakers[speaker_id] = speaker_segments_list
        
        # If no segments were mapped, preserve original structure
        if not enhanced_speakers and transcription_result.speakers:
            enhanced_speakers = transcription_result.speakers
        
        # Create enhanced result
        return TranscriptionResult(
            success=transcription_result.success,
            speakers=enhanced_speakers,
            full_text=transcription_result.full_text,
            transcription_time=transcription_result.transcription_time,
            model_name=transcription_result.model_name,
            audio_file=transcription_result.audio_file,
            speaker_count=len(enhanced_speakers)
        )
    
    def _is_segment_overlapping(self, segment: TranscriptionSegment, start_time: float, end_time: float) -> bool:
        """Check if segment overlaps with time range following Single Responsibility Principle"""
        return (hasattr(segment, 'start') and hasattr(segment, 'end') and
                segment.start <= end_time and segment.end >= start_time)


class SpeakerEnhancementOrchestrator:
    """Orchestrates speaker enhancement workflow following Single Responsibility Principle"""
    
    def __init__(self, speaker_service: SpeakerTranscriptionService):
        """
        Initialize the orchestrator with dependency injection
        
        Args:
            speaker_service: Injected speaker transcription service
        """
        self.speaker_service = speaker_service
        self.enhancement_strategies = self._create_enhancement_strategies()
    
    def _create_enhancement_strategies(self) -> Dict[str, SpeakerEnhancementInterface]:
        """Create enhancement strategies following Factory Pattern"""
        return {
            'chunked': ChunkedSpeakerEnhancementStrategy(self.speaker_service),
            'default': ChunkedSpeakerEnhancementStrategy(self.speaker_service)
        }
    
    def enhance_transcription(self, transcription_result: TranscriptionResult, 
                            audio_file_path: str, 
                            strategy: str = 'chunked') -> TranscriptionResult:
        """
        Enhance transcription with speaker diarization
        
        Args:
            transcription_result: Original transcription result
            audio_file_path: Path to audio file for speaker diarization
            strategy: Enhancement strategy to use
            
        Returns:
            Enhanced transcription result with speaker information
        """
        try:
            # Get the appropriate enhancement strategy
            enhancement_strategy = self.enhancement_strategies.get(
                strategy, 
                self.enhancement_strategies['default']
            )
            
            # Create enhancement context
            context = EnhancementContext(
                audio_file_path=audio_file_path,
                speaker_config=getattr(transcription_result, 'config', None),
                enhancement_strategy=strategy
            )
            
            # Apply enhancement
            enhanced_result = enhancement_strategy.enhance_transcription(transcription_result, audio_file_path)
            
            logger.info(f"✅ Speaker enhancement orchestration completed successfully")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error in speaker enhancement orchestration: {e}")
            return transcription_result
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available enhancement strategies"""
        return list(self.enhancement_strategies.keys())
