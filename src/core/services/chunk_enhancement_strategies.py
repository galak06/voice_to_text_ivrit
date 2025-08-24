#!/usr/bin/env python3
"""
Chunk Enhancement Strategies
Implements different strategies for enhancing individual chunks following Strategy Pattern
"""

import logging
import tempfile
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

from src.models.speaker_models import TranscriptionSegment
from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService

logger = logging.getLogger(__name__)


@dataclass
class ChunkEnhancementContext:
    """Context for chunk enhancement following Single Responsibility Principle"""
    chunk_num: int
    chunk_start: float
    chunk_end: float
    audio_data: Any
    sample_rate: int
    config: Any
    enhancement_level: str = 'basic'


class ChunkEnhancementStrategy(ABC):
    """Abstract base class for chunk enhancement strategies following Open/Closed Principle"""
    
    @abstractmethod
    def can_enhance(self, context: ChunkEnhancementContext) -> bool:
        """Check if this strategy can enhance the given chunk"""
        pass
    
    @abstractmethod
    def enhance(self, segment: TranscriptionSegment, context: ChunkEnhancementContext) -> TranscriptionSegment:
        """Enhance the given segment"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        pass


class NoEnhancementStrategy(ChunkEnhancementStrategy):
    """Strategy for when no enhancement is needed - follows Null Object Pattern"""
    
    def can_enhance(self, context: ChunkEnhancementContext) -> bool:
        """Always returns False - no enhancement needed"""
        return False
    
    def enhance(self, segment: TranscriptionSegment, context: ChunkEnhancementContext) -> TranscriptionSegment:
        """Return segment unchanged"""
        return segment
    
    def get_strategy_name(self) -> str:
        return "no_enhancement"


class BasicSpeakerEnhancementStrategy(ChunkEnhancementStrategy):
    """Basic speaker enhancement strategy for simple cases"""
    
    def __init__(self, config: Any):
        self.config = config
    
    def can_enhance(self, context: ChunkEnhancementContext) -> bool:
        """Check if basic enhancement can be applied"""
        return (hasattr(context, 'config') and 
                context.config is not None and
                context.enhancement_level in ['basic', 'standard'])
    
    def enhance(self, segment: TranscriptionSegment, context: ChunkEnhancementContext) -> TranscriptionSegment:
        """Apply basic speaker enhancement"""
        try:
            logger.debug(f"🎯 Applying basic enhancement to chunk {context.chunk_num + 1}")
            
            # Create enhanced segment with metadata
            enhanced_segment = TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                speaker=segment.speaker,
                words=getattr(segment, 'words', None),
                confidence=getattr(segment, 'confidence', None),
                chunk_file=getattr(segment, 'chunk_file', None),
                chunk_number=context.chunk_num + 1
            )
            
            # Add basic metadata
            enhanced_segment.metadata = {
                'enhancement_strategy': self.get_strategy_name(),
                'enhancement_level': 'basic',
                'original_speaker': segment.speaker,
                'enhancement_applied': True
            }
            
            return enhanced_segment
            
        except Exception as e:
            logger.error(f"❌ Error in basic enhancement: {e}")
            return segment
    
    def get_strategy_name(self) -> str:
        return "basic_enhancement"


class AdvancedSpeakerEnhancementStrategy(ChunkEnhancementStrategy):
    """Advanced speaker enhancement strategy with diarization"""
    
    def __init__(self, config: Any):
        self.config = config
        self._speaker_service: Optional[SpeakerTranscriptionService] = None
    
    def can_enhance(self, context: ChunkEnhancementContext) -> bool:
        """Check if advanced enhancement can be applied"""
        return (hasattr(context, 'config') and 
                context.config is not None and
                context.enhancement_level in ['advanced', 'full'])
    
    def enhance(self, segment: TranscriptionSegment, context: ChunkEnhancementContext) -> TranscriptionSegment:
        """Apply advanced speaker enhancement with diarization"""
        try:
            logger.info(f"🎯 Applying advanced enhancement to chunk {context.chunk_num + 1}")
            
            # Create temporary audio file for this chunk
            chunk_audio_file = self._create_temp_chunk_audio(context)
            
            if not chunk_audio_file:
                logger.warning(f"⚠️ Could not create temp audio for chunk {context.chunk_num + 1}")
                return self._fallback_enhancement(segment, context)
            
            try:
                # Perform speaker diarization
                speaker_segments = self._perform_speaker_diarization(chunk_audio_file, context)
                
                if speaker_segments and len(speaker_segments) > 1:
                    # Multiple speakers detected
                    return self._create_multi_speaker_segment(segment, context, speaker_segments)
                else:
                    # Single speaker detected
                    return self._create_single_speaker_segment(segment, context, speaker_segments)
                    
            finally:
                # Clean up temporary file
                self._cleanup_temp_audio(chunk_audio_file)
                
        except Exception as e:
            logger.error(f"❌ Error in advanced enhancement: {e}")
            return self._fallback_enhancement(segment, context)
    
    def _create_temp_chunk_audio(self, context: ChunkEnhancementContext) -> Optional[str]:
        """Create temporary audio file for chunk analysis"""
        try:
            import soundfile as sf
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Extract audio data for this chunk
            start_sample = int(context.chunk_start * context.sample_rate)
            end_sample = int(context.chunk_end * context.sample_rate)
            chunk_audio = context.audio_data[start_sample:end_sample]
            
            # Save as temporary WAV file
            sf.write(temp_file_path, chunk_audio, context.sample_rate)
            logger.debug(f"💾 Created temp audio for chunk {context.chunk_num + 1}")
            
            return temp_file_path
            
        except Exception as e:
            logger.error(f"❌ Error creating temp audio: {e}")
            return None
    
    def _perform_speaker_diarization(self, chunk_audio_file: str, context: ChunkEnhancementContext) -> List[Tuple[float, float]]:
        """Perform speaker diarization on chunk"""
        try:
            # Get or create speaker service
            if not self._speaker_service:
                from src.core.factories.speaker_config_factory import SpeakerConfigFactory
                speaker_config = SpeakerConfigFactory.get_config('conversation')
                self._speaker_service = SpeakerTranscriptionService(speaker_config, self.config, None)
            
            # Perform diarization
            speaker_segments = self._speaker_service._perform_speaker_diarization(chunk_audio_file)
            
            if speaker_segments:
                # Adjust time ranges to be relative to the chunk
                adjusted_segments = []
                for start_time, end_time in speaker_segments:
                    adjusted_start = context.chunk_start + start_time
                    adjusted_end = context.chunk_start + end_time
                    adjusted_segments.append((adjusted_start, adjusted_end))
                
                logger.info(f"🎯 Speaker diarization: {len(adjusted_segments)} segments detected")
                return adjusted_segments
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error in speaker diarization: {e}")
            return []
    
    def _create_multi_speaker_segment(self, segment: TranscriptionSegment, context: ChunkEnhancementContext, 
                                    speaker_segments: List[Tuple[float, float]]) -> TranscriptionSegment:
        """Create enhanced segment for multiple speakers"""
        enhanced_segment = TranscriptionSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text,
            speaker=f"enhanced_multi_{context.chunk_num + 1}",
            words=getattr(segment, 'words', None),
            confidence=getattr(segment, 'confidence', None),
            chunk_file=getattr(segment, 'chunk_file', None),
            chunk_number=context.chunk_num + 1
        )
        
        # Add comprehensive metadata
        enhanced_segment.metadata = {
            'enhancement_strategy': self.get_strategy_name(),
            'enhancement_level': 'advanced',
            'original_speaker': segment.speaker,
            'detected_speakers': len(speaker_segments),
            'speaker_time_ranges': speaker_segments,
            'enhancement_applied': True,
            'analysis_details': {
                'chunk_duration': context.chunk_end - context.chunk_start,
                'speaker_density': len(speaker_segments) / (context.chunk_end - context.chunk_start),
                'enhancement_timestamp': context.chunk_start
            }
        }
        
        return enhanced_segment
    
    def _create_single_speaker_segment(self, segment: TranscriptionSegment, context: ChunkEnhancementContext,
                                     speaker_segments: List[Tuple[float, float]]) -> TranscriptionSegment:
        """Create enhanced segment for single speaker"""
        enhanced_segment = TranscriptionSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text,
            speaker=f"enhanced_single_{context.chunk_num + 1}",
            words=getattr(segment, 'words', None),
            confidence=getattr(segment, 'confidence', None),
            chunk_file=getattr(segment, 'chunk_file', None),
            chunk_number=context.chunk_num + 1
        )
        
        # Add metadata for single speaker
        enhanced_segment.metadata = {
            'enhancement_strategy': self.get_strategy_name(),
            'enhancement_level': 'advanced',
            'original_speaker': segment.speaker,
            'detected_speakers': 1,
            'speaker_time_ranges': speaker_segments,
            'enhancement_applied': True,
            'analysis_details': {
                'chunk_duration': context.chunk_end - context.chunk_start,
                'speaker_consistency': 'single_speaker',
                'enhancement_timestamp': context.chunk_start
            }
        }
        
        return enhanced_segment
    
    def _fallback_enhancement(self, segment: TranscriptionSegment, context: ChunkEnhancementContext) -> TranscriptionSegment:
        """Fallback enhancement when advanced enhancement fails"""
        logger.warning(f"⚠️ Using fallback enhancement for chunk {context.chunk_num + 1}")
        
        enhanced_segment = TranscriptionSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text,
            speaker=f"fallback_{context.chunk_num + 1}",
            words=getattr(segment, 'words', None),
            confidence=getattr(segment, 'confidence', None),
            chunk_file=getattr(segment, 'chunk_file', None),
            chunk_number=context.chunk_num + 1
        )
        
        enhanced_segment.metadata = {
            'enhancement_strategy': 'fallback',
            'enhancement_level': 'basic',
            'original_speaker': segment.speaker,
            'enhancement_applied': False,
            'fallback_reason': 'advanced_enhancement_failed'
        }
        
        return enhanced_segment
    
    def _cleanup_temp_audio(self, temp_file_path: str):
        """Clean up temporary audio file"""
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.debug(f"🧹 Cleaned up temp audio: {temp_file_path}")
        except Exception as e:
            logger.debug(f"⚠️ Error cleaning up temp audio: {e}")
    
    def get_strategy_name(self) -> str:
        return "advanced_enhancement"


class ChunkEnhancementStrategyFactory:
    """Factory for creating chunk enhancement strategies following Factory Pattern"""
    
    def __init__(self, config: Any):
        self.config = config
        self._strategies = self._create_strategies()
    
    def _create_strategies(self) -> List[ChunkEnhancementStrategy]:
        """Create available enhancement strategies"""
        return [
            NoEnhancementStrategy(),
            BasicSpeakerEnhancementStrategy(self.config),
            AdvancedSpeakerEnhancementStrategy(self.config)
        ]
    
    def get_enhancement_strategy(self, context: ChunkEnhancementContext) -> ChunkEnhancementStrategy:
        """Get the appropriate enhancement strategy for the given context"""
        # Find the best strategy that can enhance the chunk
        for strategy in reversed(self._strategies):  # Start with most advanced
            if strategy.can_enhance(context):
                logger.debug(f"🎯 Selected enhancement strategy: {strategy.get_strategy_name()}")
                return strategy
        
        # Fallback to no enhancement
        logger.debug("🎯 No enhancement strategy available, using no_enhancement")
        return self._strategies[0]  # NoEnhancementStrategy
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names"""
        return [strategy.get_strategy_name() for strategy in self._strategies]
