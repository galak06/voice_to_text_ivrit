#!/usr/bin/env python3
"""
Consolidated Transcription Engine
Combines all transcription capabilities from the original engine and optimized whisper engine
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from .base_interface import TranscriptionEngine
from src.core.engines.utilities.model_manager import ModelManager
from src.core.engines.utilities.text_processor import TextProcessor
from src.core.engines.utilities.cleanup_manager import CleanupManager
from src.core.engines.strategies.transcription_strategy_factory import TranscriptionStrategyFactory

logger = logging.getLogger(__name__)


class ConsolidatedTranscriptionEngine(TranscriptionEngine):
    """Consolidated transcription engine with all capabilities"""
    
    def __init__(self, config, app_config=None):
        """Initialize consolidated engine with all utilities"""
        self.config = config
        self.app_config = app_config
        self._setup_engine()
        self._setup_utilities()
        self._setup_speaker_diarization()
    
    def _setup_engine(self) -> None:
        """Setup engine configuration and directories"""
        self.cleanup_logs_before_run = getattr(self.config, 'cleanup_logs_before_run', True)
        self.max_output_files = getattr(self.config, 'max_output_files', 5)
        self._create_temp_directories()
    
    def _setup_utilities(self) -> None:
        """Setup utility managers"""
        self._model_manager = ModelManager()
        self._text_processor = TextProcessor(self.app_config)
        self._cleanup_manager = CleanupManager(self.config)
        self._strategy_factory = TranscriptionStrategyFactory(self.config, self.app_config)
    
    def _setup_speaker_diarization(self) -> None:
        """Setup speaker diarization capabilities"""
        try:
            # First check environment variable (highest priority)
            import os
            env_enabled = os.getenv('SPEAKER_DIARIZATION_ENABLED', 'true').lower()
            if env_enabled == 'false':
                logger.info("ℹ️ Speaker diarization disabled via environment variable")
                self._speaker_service = None
                self._speaker_diarization_enabled = False
                return
            
            # Then check configuration
            if isinstance(self.config, dict):
                speaker_diarization_config = self.config.get('speaker_diarization', {})
                speaker_preset = self.config.get('speaker_preset', 'conversation')
            else:
                # Check if speaker config object has diarization disabled
                if hasattr(self.config, 'speaker') and hasattr(self.config.speaker, '_diarization_enabled'):
                    if not self.config.speaker._diarization_enabled:
                        logger.info("ℹ️ Speaker diarization disabled in speaker config")
                        self._speaker_service = None
                        self._speaker_diarization_enabled = False
                        return
                
                speaker_diarization_config = getattr(self.config, 'speaker_diarization', {})
                speaker_preset = getattr(self.config, 'speaker_preset', 'conversation')
            
            if speaker_diarization_config and not speaker_diarization_config.get('enabled', True):
                logger.info("ℹ️ Speaker diarization disabled in configuration")
                self._speaker_service = None
                self._speaker_diarization_enabled = False
                return
            
            # Import speaker diarization service
            from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService
            from src.core.factories.speaker_config_factory import SpeakerConfigFactory
            
            # Get speaker configuration from config or use default conversation preset
            speaker_service_config = SpeakerConfigFactory.get_config(speaker_preset)
            
            # Initialize speaker diarization service
            self._speaker_service = SpeakerTranscriptionService(speaker_service_config, self.app_config)
            self._speaker_diarization_enabled = True
            logger.info(f"✅ Speaker diarization enabled with preset: {speaker_preset}")
            
        except Exception as e:
            logger.warning(f"⚠️ Speaker diarization not available: {e}")
            self._speaker_service = None
            self._speaker_diarization_enabled = False
    
    def _create_temp_directories(self) -> None:
        """Create necessary temporary directories"""
        from pathlib import Path
        temp_dirs = ["output/temp_chunks", "examples/audio/voice/audio_chunks"]
        for temp_dir in temp_dirs:
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
    
    def transcribe(self, audio_file_path: str, model_name: str):
        """Main transcription entry point - delegates to appropriate strategy"""
        if not self._validate_audio_file(audio_file_path):
            return self._create_error_result(audio_file_path, model_name, "Audio file not found")
        
        # Perform transcription using existing strategy
        strategy = self._strategy_factory.create_strategy(audio_file_path)
        transcription_result = strategy.execute(audio_file_path, model_name, self)
        
        # Apply speaker diarization if enabled and result is successful
        if (self._speaker_diarization_enabled and 
            transcription_result.success and 
            hasattr(transcription_result, 'speakers')):
            
            try:
                logger.info("🎯 Applying speaker diarization to transcription result")
                enhanced_result = self._apply_speaker_diarization(audio_file_path, transcription_result)
                if enhanced_result:
                    return enhanced_result
                else:
                    logger.warning("⚠️ Speaker diarization failed, returning original result")
                    return transcription_result
                    
            except Exception as e:
                logger.error(f"❌ Error applying speaker diarization: {e}")
                return transcription_result
        
        return transcription_result
    
    def _apply_speaker_diarization(self, audio_file_path: str, transcription_result) -> 'TranscriptionResult':
        """Apply speaker diarization to transcription result"""
        try:
            # Get speaker segments using pyannote.audio
            speaker_segments = self._perform_speaker_diarization(audio_file_path)
            
            if not speaker_segments:
                logger.warning("⚠️ No speaker segments detected, returning original result")
                return transcription_result
            
            # Apply speaker labels to existing segments
            enhanced_result = self._enhance_result_with_speakers(transcription_result, speaker_segments)
            logger.info(f"✅ Speaker diarization applied: {len(speaker_segments)} speaker segments detected")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error in speaker diarization: {e}")
            return transcription_result
    
    def _perform_speaker_diarization(self, audio_file_path: str) -> List[tuple]:
        """Perform speaker diarization using pyannote.audio"""
        try:
            # Use the speaker service's diarization method
            if self._speaker_service:
                return self._speaker_service._perform_speaker_diarization(audio_file_path)
            else:
                return []
        except Exception as e:
            logger.error(f"❌ Speaker diarization failed: {e}")
            return []
    
    def _enhance_result_with_speakers(self, transcription_result, speaker_segments: List[tuple]) -> 'TranscriptionResult':
        """Enhanced speaker diarization with improved chunk preservation following SOLID principles"""
        try:
            from src.models.speaker_models import TranscriptionResult, TranscriptionSegment
            
            # Extract all segments from transcription result
            all_segments = self._extract_all_segments(transcription_result)
            
            if not all_segments:
                logger.warning("⚠️ No segments found in transcription result")
                return transcription_result
            
            # Map segments to speakers using improved overlap detection
            mapped_speakers, mapped_segments = self._map_segments_to_speakers(all_segments, speaker_segments)

            # Second pass: Handle overlapping segments
            overlapping_mappings = self._handle_overlapping_segments(all_segments, speaker_segments, mapped_segments)

            # Third pass: Preserve unmapped segments
            unmapped_speakers = self._handle_unmapped_segments(transcription_result, mapped_segments)
            
            # Merge all speakers
            final_speakers = {**mapped_speakers, **unmapped_speakers}
            
            # Create enhanced result
            enhanced_result = self._create_enhanced_result(transcription_result, final_speakers)
            
            logger.info(f"✅ Enhanced result created with {len(final_speakers)} speakers")
            logger.info(f"   - Total segments: {sum(len(segs) for segs in final_speakers.values())}")
            logger.info(f"   - Mapped segments: {len(mapped_segments)}")
            logger.info(f"   - Unmapped segments preserved: {sum(len(segs) for segs in unmapped_speakers.values())}")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error enhancing result with speakers: {e}")
            return transcription_result
    
    def _extract_all_segments(self, transcription_result) -> List:
        """Extract all segments from transcription result following Single Responsibility Principle"""
        all_segments = []
        
        if hasattr(transcription_result, 'speakers') and transcription_result.speakers:
            for segments in transcription_result.speakers.values():
                all_segments.extend(segments)
        
        return all_segments
    
    def _map_segments_to_speakers(self, all_segments: List, speaker_segments: List[tuple]) -> tuple:
        """Map segments to speakers using improved overlap detection following Single Responsibility Principle"""
        mapped_speakers = {}
        mapped_segments = set()
        
        # First pass: Map segments with exact containment
        for i, (start_time, end_time) in enumerate(speaker_segments):
            # Preserve original speaker IDs from chunks (speaker_1, speaker_2) instead of creating new ones
            speaker_id = f"speaker_{i + 1}"  # Use i+1 to match chunk strategy (speaker_1, speaker_2)
            speaker_segments_list = []
            
            for segment in all_segments:
                if self._is_segment_contained(segment, start_time, end_time):
                    # Preserve the original speaker ID from the segment if it exists
                    original_speaker = getattr(segment, 'speaker', None)
                    if original_speaker and original_speaker.startswith('speaker_'):
                        # Keep the original speaker ID from the chunk
                        mapped_segment = self._create_mapped_segment(segment, original_speaker)
                    else:
                        # Fallback to the calculated speaker ID
                        mapped_segment = self._create_mapped_segment(segment, speaker_id)
                    
                    speaker_segments_list.append(mapped_segment)
                    mapped_segments.add((segment.start, segment.end))
            
            # If no segments mapped, create a placeholder segment
            if not speaker_segments_list:
                placeholder_segment = self._create_placeholder_segment(start_time, end_time, i)
                speaker_segments_list.append(placeholder_segment)
            
            mapped_speakers[speaker_id] = speaker_segments_list
        
        # Second pass: Handle overlapping segments that weren't mapped
        overlapping_mappings = self._handle_overlapping_segments(all_segments, speaker_segments, mapped_segments)
        
        # Merge overlapping mappings
        for speaker_id, segments in overlapping_mappings.items():
            if speaker_id in mapped_speakers:
                mapped_speakers[speaker_id].extend(segments)
            else:
                mapped_speakers[speaker_id] = segments
        
        return mapped_speakers, mapped_segments
    
    def _is_segment_contained(self, segment, start_time: float, end_time: float) -> bool:
        """Check if segment is contained within time range following Single Responsibility Principle"""
        return (hasattr(segment, 'start') and hasattr(segment, 'end') and
                segment.start >= start_time and segment.end <= end_time)
    
    def _create_mapped_segment(self, segment, speaker_id: str):
        """Create a new segment with speaker label following Single Responsibility Principle"""
        from src.models.speaker_models import TranscriptionSegment
        
        return TranscriptionSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text if hasattr(segment, 'text') else "",
            speaker=speaker_id,
            words=getattr(segment, 'words', None),
            confidence=getattr(segment, 'confidence', None),
            chunk_file=getattr(segment, 'chunk_file', None),
            chunk_number=getattr(segment, 'chunk_number', None)
        )
    
    def _create_placeholder_segment(self, start_time: float, end_time: float, speaker_index: int):
        """Create a placeholder segment following Single Responsibility Principle"""
        from src.models.speaker_models import TranscriptionSegment
        
        return TranscriptionSegment(
            start=start_time,
            end=end_time,
            text=f"[Speaker {speaker_index + 1} segment]",
            speaker=f"speaker_{speaker_index + 1}"  # Use consistent format (speaker_1, speaker_2)
        )
    
    def _handle_overlapping_segments(self, all_segments: List, speaker_segments: List[tuple], 
                                   mapped_segments: set) -> Dict[str, List]:
        """Handle segments that overlap with speaker time ranges following Single Responsibility Principle"""
        overlapping_mappings = {}
        
        for segment in all_segments:
            segment_key = (segment.start, segment.end)
            
            # Skip already mapped segments
            if segment_key in mapped_segments:
                continue
            
            # Find which speakers this segment overlaps with
            overlapping_speakers = self._find_overlapping_speakers(segment, speaker_segments)
            
            if overlapping_speakers:
                # Assign to speaker with most overlap
                best_speaker = self._find_best_speaker_match(segment, speaker_segments, overlapping_speakers)
                # Use consistent speaker ID format (speaker_1, speaker_2) to match chunk strategy
                speaker_id = f"speaker_{best_speaker + 1}"
                
                if speaker_id not in overlapping_mappings:
                    overlapping_mappings[speaker_id] = []
                
                # Preserve original speaker ID if it exists, otherwise use calculated one
                original_speaker = getattr(segment, 'speaker', None)
                if original_speaker and original_speaker.startswith('speaker_'):
                    mapped_segment = self._create_mapped_segment(segment, original_speaker)
                else:
                    mapped_segment = self._create_mapped_segment(segment, speaker_id)
                
                overlapping_mappings[speaker_id].append(mapped_segment)
                mapped_segments.add(segment_key)
        
        return overlapping_mappings
    
    def _find_overlapping_speakers(self, segment, speaker_segments: List[tuple]) -> List[int]:
        """Find which speakers a segment overlaps with following Single Responsibility Principle"""
        overlapping_speakers = []
        
        for i, (start_time, end_time) in enumerate(speaker_segments):
            if self._segments_overlap(segment.start, segment.end, start_time, end_time):
                overlapping_speakers.append(i)
        
        return overlapping_speakers
    
    def _segments_overlap(self, seg1_start: float, seg1_end: float, seg2_start: float, seg2_end: float) -> bool:
        """Check if two time segments overlap following Single Responsibility Principle"""
        return seg1_start <= seg2_end and seg1_end >= seg2_start
    
    def _find_best_speaker_match(self, segment, speaker_segments: List[tuple], 
                                candidate_speakers: List[int]) -> int:
        """Find the speaker with the most overlap with the given segment following Single Responsibility Principle"""
        best_speaker = candidate_speakers[0]
        max_overlap = 0
        
        for speaker_idx in candidate_speakers:
            start_time, end_time = speaker_segments[speaker_idx]
            
            # Calculate overlap duration
            overlap_start = max(segment.start, start_time)
            overlap_end = min(segment.end, end_time)
            overlap_duration = max(0, overlap_end - overlap_start)
            
            if overlap_duration > max_overlap:
                max_overlap = overlap_duration
                best_speaker = speaker_idx
        
        return best_speaker
    
    def _handle_unmapped_segments(self, transcription_result, mapped_segments: set) -> Dict[str, List]:
        """Handle segments that weren't mapped to any speaker following Single Responsibility Principle"""
        unmapped_speakers = {}
        
        if hasattr(transcription_result, 'speakers') and transcription_result.speakers:
            for existing_speaker, segments in transcription_result.speakers.items():
                unmapped_segments = []
                
                for segment in segments:
                    segment_key = (segment.start, segment.end)
                    if segment_key not in mapped_segments:
                        unmapped_segments.append(segment)
                
                if unmapped_segments:
                    # Create a new speaker ID for unmapped segments
                    unmapped_speaker_id = f"unmapped_speaker_{len(unmapped_speakers)}"
                    unmapped_speakers[unmapped_speaker_id] = unmapped_segments
        
        return unmapped_speakers
    
    def _create_enhanced_result(self, transcription_result, final_speakers: Dict[str, List]):
        """Create enhanced transcription result following Single Responsibility Principle"""
        from src.models.speaker_models import TranscriptionResult
        
        # Calculate total text from all speakers
        total_text = self._calculate_total_text(final_speakers)
        
        return TranscriptionResult(
            success=True,
            speakers=final_speakers,
            full_text=total_text.strip() if total_text else transcription_result.full_text,
            transcription_time=transcription_result.transcription_time,
            model_name=transcription_result.model_name,
            audio_file=transcription_result.audio_file,
            speaker_count=len(final_speakers)
        )
    
    def _calculate_total_text(self, speakers: Dict[str, List]) -> str:
        """Calculate total text from all speakers following Single Responsibility Principle"""
        text_parts = []
        
        for segments in speakers.values():
            for segment in segments:
                if hasattr(segment, 'text') and segment.text:
                    text_parts.append(segment.text)
        
        return " ".join(text_parts)
    
    def _validate_audio_file(self, audio_file_path: str) -> bool:
        """Validate audio file exists and is accessible"""
        from pathlib import Path
        return Path(audio_file_path).exists()
    
    def _create_error_result(self, audio_file_path: str, model_name: str, error_message: str):
        """Create error result with consistent structure"""
        from src.models.speaker_models import TranscriptionResult
        return TranscriptionResult(
            success=False,
            speakers={},
            full_text="",
            transcription_time=0.0,
            model_name=model_name,
            audio_file=audio_file_path,
            speaker_count=0,
            error_message=error_message
        )
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk using optimized engine"""
        chunk_start_time = time.time()
        logger.info(f"🎯 Starting transcription for chunk {chunk_count}")
        
        try:
            processor, model = self._model_manager.get_or_load_model(model_name)
            language = getattr(self.config, 'language', 'he')
            
            chunk_transcription = self._execute_transcription(audio_chunk, chunk_count, processor, model, language)
            chunk_transcription = self._post_process_transcription(chunk_transcription, language, chunk_count)
            
            total_time = time.time() - chunk_start_time
            logger.info(f"✅ Chunk {chunk_count} completed in {total_time:.2f}s")
            return chunk_transcription
            
        except Exception as e:
            logger.error(f"❌ Error transcribing chunk {chunk_count}: {e}")
            raise
    
    def _execute_transcription(self, audio_chunk, chunk_count: int, processor, model, language: str) -> str:
        """Execute transcription based on model type"""
        # Check if it's a CTranslate2 model by looking for specific CTranslate2 attributes
        if hasattr(model, '_model') and hasattr(model._model, 'device'):  # CTranslate2 model
            return self._transcribe_with_ct2(audio_chunk, chunk_count, processor, model, language)
        elif hasattr(model, 'config') and hasattr(model.config, 'model_type'):  # Transformers model
            return self._transcribe_with_transformers(audio_chunk, chunk_count, processor, model, language)
        else:
            # Fallback: try to determine by model name or other attributes
            model_name = getattr(model, '__class__.__name__', str(type(model)))
            if 'Whisper' in model_name and not hasattr(model, 'config'):
                return self._transcribe_with_ct2(audio_chunk, chunk_count, processor, model, language)
            else:
                return self._transcribe_with_transformers(audio_chunk, chunk_count, processor, model, language)
    
    def _post_process_transcription(self, text: str, language: str, chunk_count: int) -> str:
        """Post-process transcription text"""
        filtered_text = self._text_processor.filter_language_only(text, language)
        quality_info = self._text_processor.validate_transcription_quality(filtered_text)
        
        if not quality_info['is_acceptable']:
            logger.warning(f"⚠️ Chunk {chunk_count}: Low quality transcription (score: {quality_info['quality_score']:.1f})")
        
        return filtered_text
    
    def _transcribe_with_ct2(self, audio_chunk, chunk_count: int, processor, model, language: str) -> str:
        """Transcribe using CTranslate2 model"""
        import ctranslate2
        
        features = self._prepare_ct2_features(processor, audio_chunk)
        prompts = self._get_ct2_prompts(processor, language)
        suppress_tokens = self._text_processor.get_language_suppression_tokens(language)
        
        generation_result = model.generate(
            features, prompts=prompts, suppress_tokens=suppress_tokens,
            beam_size=5, max_length=448, suppress_blank=True
        )
        
        return self._decode_ct2_result(generation_result, processor)
    
    def _prepare_ct2_features(self, processor, audio_chunk):
        """Prepare audio features for CTranslate2"""
        import ctranslate2
        features = processor(audio_chunk, sampling_rate=16000, return_tensors="np").input_features
        features = features.astype("float32")
        return ctranslate2.StorageView.from_array(features)
    
    def _decode_ct2_result(self, generation_result, processor):
        """Decode CTranslate2 generation result"""
        if hasattr(generation_result, 'sequences'):
            sequences = generation_result.sequences
            if isinstance(sequences, list) and len(sequences) > 0:
                return processor.batch_decode(sequences, skip_special_tokens=True)[0]
        raise ValueError("Invalid CTranslate2 generation result")
    
    def _transcribe_with_transformers(self, audio_chunk, chunk_count: int, processor, model, language: str) -> str:
        """Transcribe using transformers model"""
        import torch
        
        features = self._prepare_transformers_features(processor, audio_chunk)
        forced_decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
        suppress_tokens = self._text_processor.get_language_suppression_tokens(language)
        
        with torch.no_grad():
            predicted_ids = model.generate(
                features, forced_decoder_ids=forced_decoder_ids, suppress_tokens=suppress_tokens,
                num_beams=5, temperature=0.0, do_sample=False, max_new_tokens=400
            )
        
        return processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    
    def _prepare_transformers_features(self, processor, audio_chunk):
        """Prepare audio features for transformers"""
        features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
        return features.float()
    
    def _get_ct2_prompts(self, processor, language: str) -> List[List[int]]:
        """Get prompts for CTranslate2 generation"""
        try:
            decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
            if decoder_ids:
                prompt_token_ids = [token_id for _, token_id in decoder_ids]
                start_token = processor.tokenizer.encode("<|startoftranscript|>", add_special_tokens=False)
                if start_token and start_token[0] not in prompt_token_ids:
                    prompt_token_ids = start_token + prompt_token_ids
                return [prompt_token_ids]
        except Exception:
            pass
        return []
    
    def is_available(self) -> bool:
        """Check if the engine is available"""
        try:
            import ctranslate2
            import transformers
            return True
        except ImportError:
            return False
    
    def cleanup_models(self) -> None:
        """Clean up loaded models and free memory"""
        self._model_manager.cleanup_models()
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine"""
        cache_info = self._model_manager.get_cache_info()
        return {
            "engine_type": "ConsolidatedTranscriptionEngine",
            "config": str(self.config),
            "loaded_models_count": cache_info["loaded_models_count"],
            "processor_cache_size": cache_info["processor_cache_size"],
            "cached_models": cache_info["cached_models"]
        }
    

