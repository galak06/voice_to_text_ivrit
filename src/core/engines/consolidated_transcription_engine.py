#!/usr/bin/env python3
"""
Consolidated transcription engine with all capabilities
Follows SOLID principles with dependency injection
"""

import logging
import os
import tempfile
import time
from typing import List, Dict, Any, Optional
from src.core.engines.utilities.model_manager import ModelManager
from src.core.engines.utilities.cleanup_manager import CleanupManager
from src.core.interfaces.transcription_engine_interface import ITranscriptionEngine
from src.core.engines.strategies.transcription_strategy_factory import TranscriptionStrategyFactory
from src.models.speaker_models import TranscriptionResult

logger = logging.getLogger(__name__)


class ConsolidatedTranscriptionEngine(ITranscriptionEngine):
    """Consolidated transcription engine with all capabilities"""
    
    def _create_text_processor(self):
        """Create a text processor with required methods"""
        class SimpleTextProcessor:
            def get_language_suppression_tokens(self, *args, **kwargs):
                """Return empty list for language suppression tokens"""
                return []
            
            def filter_language_only(self, text, *args, **kwargs):
                """Simple text filter - return text as is"""
                return text
            
            def validate_transcription_quality(self, text):
                """Simple quality validation - return True if text exists"""
                return bool(text and text.strip())
        
        return SimpleTextProcessor()
    
    def __init__(self, config_manager, model_manager=None):
        """Initialize the consolidated transcription engine"""
        # ONLY use ConfigManager - no duplicate config storage
        if not config_manager:
            raise ValueError("ConfigManager is required - no fallback to direct config")
        
        self.config_manager = config_manager
        
        # Extract models path from ConfigManager
        self.model_manager = model_manager or ModelManager(config_manager=config_manager)
        
        # Initialize internal attributes
        self._model_manager = self.model_manager
        self._text_processor = self._create_text_processor()  # Initialize with proper implementation

        # Initialize speaker labeling service with dependency injection (DIP)
        from src.core.models.speaker_labeling_service import SpeakerLabelingService, DefaultSpeakerLabelingConfig
        
        config_dict = self.config_manager.config.dict() if hasattr(self.config_manager.config, 'dict') else self.config_manager.config
        config_provider = DefaultSpeakerLabelingConfig(config_dict)
        self.speaker_labeling_service = SpeakerLabelingService(config_provider)
        
        # Setup capabilities
        self._setup_speaker_diarization()
        self._create_temp_directories()
        
        # Initialize transcription strategies
        self._init_transcription_strategies()
        
        # Initialize cleanup manager with ConfigManager
        self._cleanup_manager = CleanupManager(config_manager=config_manager)
        
        logger.info("🚀 Consolidated Transcription Engine initialized successfully")
    
    def _setup_speaker_diarization(self) -> None:
        """Setup speaker diarization capabilities using injected service (SRP)"""
        try:
            # Use the injected speaker labeling service to determine state
            config_dict = self.config_manager.config.dict() if hasattr(self.config_manager.config, 'dict') else self.config_manager.config
            self._speaker_diarization_enabled = self.speaker_labeling_service.should_label_speakers(config_dict)
            
            if self._speaker_diarization_enabled:
                logger.info("ℹ️ Speaker diarization enabled")
                self._speaker_service = None  # Will be injected by orchestrator if needed
            else:
                logger.info("ℹ️ Speaker diarization disabled")
                self._speaker_service = None
                
        except Exception as e:
            logger.warning(f"⚠️ Error setting up speaker diarization: {e}")
            self._speaker_service = None
            self._speaker_diarization_enabled = False
    
    def _create_temp_directories(self) -> None:
        """Create temporary directories for processing (SRP)"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="transcription_")
            self.chunks_dir = os.path.join(self.temp_dir, "chunks")
            os.makedirs(self.chunks_dir, exist_ok=True)
            logger.info(f"📁 Temporary directories created: {self.temp_dir}")
        except Exception as e:
            logger.error(f"❌ Error creating temp directories: {e}")
            raise
    
    def _init_transcription_strategies(self) -> None:
        """Initialize transcription strategies using factory (SRP)"""
        try:
            # Pass the config_manager to ensure proper dependency injection
            if hasattr(self, 'config_manager'):
                self._strategy_factory = TranscriptionStrategyFactory(self.config_manager)
            else:
                # NO FALLBACK - ConfigManager is required
                raise ValueError("ConfigManager is required - no fallback allowed")
            logger.info("🔧 Transcription strategies initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing transcription strategies: {e}")
            raise
    
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
        
        # Validate that the audio_file_path is a valid file path
        if not audio_file_path or audio_file_path == "":
            # Use a default path if none provided
            audio_file_path = "unknown_audio_file"
        
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
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> 'TranscriptionResult':
        """Transcribe a single audio chunk using optimized engine and return TranscriptionResult"""
        chunk_start_time = time.time()
        
        # Debug logging to see exact values received
        logger.info(f"🔍 DEBUG: _transcribe_chunk received - chunk_count: {chunk_count}, chunk_start: {chunk_start}, chunk_end: {chunk_end}")
        
        logger.info(f"🎯 Starting transcription for chunk {chunk_count}")
        
        try:
            processor, model = self._model_manager.get_or_load_model(model_name)
            language = getattr(self.config_manager.config.transcription, 'language', 'he')
            
            # Get the raw transcription text
            chunk_transcription = self._execute_transcription(audio_chunk, chunk_count, processor, model, language)
            chunk_transcription = self._post_process_transcription(chunk_transcription, language, chunk_count)
            
            total_time = time.time() - chunk_start_time
            logger.info(f"✅ Chunk {chunk_count} completed in {total_time:.2f}s")
            
            # Create a proper TranscriptionResult object
            from src.models.speaker_models import TranscriptionResult, TranscriptionSegment
            
            # Create a single segment for this chunk
            segment = TranscriptionSegment(
                text=chunk_transcription,
                start=chunk_start,
                end=chunk_end,
                speaker="0",  # Default speaker for single chunk
                chunk_file=f"chunk_{chunk_count:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav",
                chunk_number=chunk_count,
                confidence=1.0
            )
            
            # Create the TranscriptionResult with correct audio file path
            # Get the audio chunks directory from ConfigManager
            audio_chunks_dir = self.config_manager.get_directory_paths().get('audio_chunks_dir', 'output/audio_chunks')
            # Use the actual chunk number from the chunk info, not the chunk_count parameter
            # The chunk_count parameter is the 1-based chunk number, so use it directly
            audio_file_path = f"{audio_chunks_dir}/audio_chunk_{chunk_count:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav"
            
            result = TranscriptionResult(
                success=True,
                speakers={"0": [segment]},
                full_text=chunk_transcription,
                transcription_time=total_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=1
            )
            
            logger.info(f"✅ Chunk {chunk_count}: Created TranscriptionResult with {len(segment.text)} characters")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error transcribing chunk {chunk_count}: {e}")
            # Return error result instead of raising
            from src.models.speaker_models import TranscriptionResult
            
            # Get the audio chunks directory from ConfigManager for error case too
            audio_chunks_dir = self.config_manager.get_directory_paths().get('audio_chunks_dir', 'output/audio_chunks')
            # Use the actual chunk number from the chunk info, not the chunk_count parameter
            # The chunk_count parameter is the 1-based chunk number, so use it directly
            audio_file_path = f"{audio_chunks_dir}/audio_chunk_{chunk_count:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav"
            
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - chunk_start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )
    
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
        
        # quality_info is a boolean, not a dictionary
        if not quality_info:
            logger.warning(f"⚠️ Chunk {chunk_count}: Low quality transcription detected")
        
        return filtered_text
    
    def _transcribe_with_ct2(self, audio_chunk, chunk_count: int, processor, model, language: str) -> str:
        """Transcribe using CTranslate2 model"""
        import ctranslate2
        import time
        
        start_time = time.time()
        logger.info(f"🎯 Chunk {chunk_count}: Starting CTranslate2 transcription")
        
        # Prepare features
        feature_start = time.time()
        logger.info(f"🔧 Chunk {chunk_count}: Preparing audio features...")
        features = self._prepare_ct2_features(processor, audio_chunk)
        feature_time = time.time() - feature_start
        logger.info(f"✅ Chunk {chunk_count}: Features prepared in {feature_time:.2f}s")
        
        # Get prompts
        prompt_start = time.time()
        logger.info(f"📝 Chunk {chunk_count}: Generating prompts for language: {language}")
        prompts = self._get_ct2_prompts(processor, language)
        prompt_time = time.time() - prompt_start
        logger.info(f"✅ Chunk {chunk_count}: Prompts generated in {prompt_time:.2f}s")
        
        # Get suppression tokens
        suppress_tokens = self._text_processor.get_language_suppression_tokens(language)
        logger.info(f"🚫 Chunk {chunk_count}: Using {len(suppress_tokens)} suppression tokens")
        
        # Generate transcription
        generation_start = time.time()
        # Get configuration values for generation parameters
        # Use ONLY the injected ConfigManager - NO FALLBACKS
        logger.info(f"🔍 Debug: self.config_manager exists: {hasattr(self, 'config_manager')}")
        logger.info(f"🔍 Debug: self.config_manager value: {self.config_manager}")
        
        if not hasattr(self, 'config_manager') or not self.config_manager:
            raise ValueError("❌ ConfigManager is required but not available")
        
        config_dict = self.config_manager.config.dict() if hasattr(self.config_manager.config, 'dict') else self.config_manager.config
        logger.info(f"🔍 Using ConfigManager config")
        
        # Debug: Log the configuration structure
        logger.info(f"🔍 Config dict keys: {list(config_dict.keys()) if isinstance(config_dict, dict) else 'Not a dict'}")
        if isinstance(config_dict, dict) and 'transcription' in config_dict:
            transcription_config = config_dict['transcription']
            logger.info(f"🔍 Transcription config keys: {list(transcription_config.keys())}")
            logger.info(f"🔍 Full transcription config: {transcription_config}")
            if 'ctranslate2_optimization' in transcription_config:
                ct2_config = transcription_config['ctranslate2_optimization']
                logger.info(f"🔍 CTranslate2 config: {ct2_config}")
            else:
                logger.warning(f"⚠️ ctranslate2_optimization section missing from transcription config!")
                logger.warning(f"⚠️ Available sections: {list(transcription_config.keys())}")
        
        # Use configuration values from ConfigManager - NO FALLBACKS
        ctranslate2_config = config_dict.get('transcription', {}).get('ctranslate2_optimization')
        if not ctranslate2_config or not isinstance(ctranslate2_config, dict):
            raise ValueError(f"❌ ctranslate2_optimization configuration is required but not found or invalid: {ctranslate2_config}")
        
        # Extract all required parameters from config
        max_new_tokens = ctranslate2_config.get('max_new_tokens')
        beam_size = ctranslate2_config.get('beam_size')
        temperature = ctranslate2_config.get('temperature')
        return_scores = ctranslate2_config.get('return_scores')
        cpu_threads = ctranslate2_config.get('cpu_threads')
        compute_type = ctranslate2_config.get('compute_type')
        
        # Validate all required parameters are present
        if max_new_tokens is None:
            raise ValueError("❌ max_new_tokens is required in ctranslate2_optimization config")
        if beam_size is None:
            raise ValueError("❌ beam_size is required in ctranslate2_optimization config")
        if temperature is None:
            raise ValueError("❌ temperature is required in ctranslate2_optimization config")
        if return_scores is None:
            raise ValueError("❌ return_scores is required in ctranslate2_optimization config")
        if cpu_threads is None:
            raise ValueError("❌ cpu_threads is required in ctranslate2_optimization config")
        if compute_type is None:
            raise ValueError("❌ compute_type is required in ctranslate2_optimization config")
        
        logger.info(f"🚀 Chunk {chunk_count}: Starting generation with beam_size={beam_size}, max_new_tokens={max_new_tokens}")
        logger.info(f"🔍 Chunk {chunk_count}: Using temperature={temperature}, return_scores={return_scores}, cpu_threads={cpu_threads}, compute_type={compute_type}")
        
        # For CTranslate2, max_length should be much larger to account for input prompt + new tokens
        # The input prompt is typically around 448 tokens, but let's be more generous to ensure full transcription
        # Adding extra buffer to account for any additional prompt overhead
        prompt_buffer = 1000  # Increased buffer for prompt tokens
        total_max_length = max_new_tokens + prompt_buffer
        
        # Get suppress_blank, early_stopping, without_timestamps, and max_initial_timestamp from hebrew_optimization config - NO FALLBACKS
        hebrew_config = config_dict.get('transcription', {}).get('hebrew_optimization')
        if not hebrew_config or not isinstance(hebrew_config, dict):
            raise ValueError(f"❌ hebrew_optimization configuration is required but not found or invalid: {hebrew_config}")
        
        suppress_blank = hebrew_config.get('suppress_blank')
        early_stopping = hebrew_config.get('early_stopping')
        without_timestamps = hebrew_config.get('without_timestamps')
        max_initial_timestamp = hebrew_config.get('max_initial_timestamp')
        
        # Validate all required parameters are present
        if suppress_blank is None:
            raise ValueError("❌ suppress_blank is required in hebrew_optimization config")
        if early_stopping is None:
            raise ValueError("❌ early_stopping is required in hebrew_optimization config")
        if without_timestamps is None:
            raise ValueError("❌ without_timestamps is required in hebrew_optimization config")
        if max_initial_timestamp is None:
            raise ValueError("❌ max_initial_timestamp is required in hebrew_optimization config")
        
        logger.info(f"🔍 Chunk {chunk_count}: Using total_max_length={total_max_length} (prompt buffer: {prompt_buffer} + new_tokens: {max_new_tokens})")
        logger.info(f"🔍 Chunk {chunk_count}: Using suppress_blank={suppress_blank}")
        logger.info(f"🔍 Chunk {chunk_count}: Using early_stopping={early_stopping}")
        logger.info(f"🔍 Chunk {chunk_count}: Using without_timestamps={without_timestamps}")
        logger.info(f"🔍 Chunk {chunk_count}: Using max_initial_timestamp={max_initial_timestamp}")
        
        # VERIFY PROCESSOR CONFIGURATION BEFORE MODEL GENERATION
        logger.info(f"🔍 Chunk {chunk_count}: VERIFYING PROCESSOR CONFIGURATION BEFORE GENERATION")
        processor_config = config_dict.get('transcription', {}).get('processor_config', {})
        if processor_config:
            logger.info(f"🔍 Chunk {chunk_count}: Processor config found: {list(processor_config.keys())}")
            logger.info(f"🔍 Chunk {chunk_count}: Full processor config: {processor_config}")
            
            # Check for critical processor parameters that might limit transcription length
            chunk_length = processor_config.get('chunk_length')
            nb_max_frames = processor_config.get('nb_max_frames')
            n_samples = processor_config.get('n_samples')
            
            if chunk_length:
                logger.info(f"🔍 Chunk {chunk_count}: Processor chunk_length: {chunk_length} seconds")
            if nb_max_frames:
                logger.info(f"🔍 Chunk {chunk_count}: Processor nb_max_frames: {nb_max_frames}")
            if n_samples:
                logger.info(f"🔍 Chunk {chunk_count}: Processor n_samples: {n_samples}")
                
            # Check if processor config might be limiting transcription
            if chunk_length and chunk_length < 30:
                logger.warning(f"⚠️ Chunk {chunk_count}: Processor chunk_length ({chunk_length}s) is less than expected chunk duration (30s)!")
            if nb_max_frames and nb_max_frames < 3000:
                logger.warning(f"⚠️ Chunk {chunk_count}: Processor nb_max_frames ({nb_max_frames}) might be limiting transcription length!")
        else:
            logger.warning(f"⚠️ Chunk {chunk_count}: No processor_config found - using default processor settings")
        
        # FINAL CONFIG VERIFICATION SUMMARY
        logger.info(f"🔍 Chunk {chunk_count}: FINAL CONFIG VERIFICATION SUMMARY:")
        logger.info(f"🔍 Chunk {chunk_count}: max_new_tokens: {max_new_tokens} (should be 10000)")
        logger.info(f"🔍 Chunk {chunk_count}: total_max_length: {total_max_length} (should be 11000)")
        logger.info(f"🔍 Chunk {chunk_count}: beam_size: {beam_size} (should be 10)")
        logger.info(f"🔍 Chunk {chunk_count}: prompt_buffer: {prompt_buffer}")
        
        # Only use parameters that are definitely supported by CTranslate2 generate method
        generation_result = model.generate(
            features, prompts=prompts, suppress_tokens=suppress_tokens,
            beam_size=beam_size, max_length=total_max_length
        )
        generation_time = time.time() - generation_start
        logger.info(f"✅ Chunk {chunk_count}: Generation completed in {generation_time:.2f}s")
        
        # Decode result
        decode_start = time.time()
        logger.info(f"🔍 Chunk {chunk_count}: Decoding generation result...")
        result = self._decode_ct2_result(generation_result, processor)
        decode_time = time.time() - decode_start
        
        total_time = time.time() - start_time
        logger.info(f"🎯 Chunk {chunk_count}: CTranslate2 transcription completed in {total_time:.2f}s")
        logger.info(f"📊 Chunk {chunk_count}: Breakdown - Features: {feature_time:.2f}s, Prompts: {prompt_time:.2f}s, Generation: {generation_time:.2f}s, Decode: {decode_time:.2f}s")
        
        return result
    
    def _prepare_ct2_features(self, processor, audio_chunk):
        """Prepare audio features for CTranslate2"""
        import ctranslate2
        features = processor(audio_chunk, sampling_rate=16000, return_tensors="np").input_features
        features = features.astype("float32")
        return ctranslate2.StorageView.from_array(features)
    
    def _decode_ct2_result(self, generation_result, processor):
        """Decode CTranslate2 generation result"""
        try:
            logger.info(f"🔍 CTranslate2 generation result type: {type(generation_result)}")
            logger.info(f"🔍 CTranslate2 generation result class: {generation_result.__class__.__name__}")
            
            # Handle case where result is a list directly
            if isinstance(generation_result, list):
                logger.info(f"🔍 Result is a list with {len(generation_result)} items")
                if len(generation_result) > 0:
                    # Try to decode the first item
                    first_item = generation_result[0]
                    logger.info(f"🔍 First item type: {type(first_item)}")
                    
                    # Check if first item is a WhisperGenerationResult object
                    if hasattr(first_item, '__class__') and ('WhisperGenerationResult' in str(first_item.__class__) or 'GenerationResult' in str(first_item.__class__)):
                        logger.info(f"🔍 First item is WhisperGenerationResult, processing it directly")
                        
                        # Process the WhisperGenerationResult object directly
                        if hasattr(first_item, 'sequences') and first_item.sequences:
                            sequences = first_item.sequences
                            logger.info(f"🔍 Sequences type: {type(sequences)}")
                            
                            # Get the first sequence without using [0]
                            first_sequence = None
                            if hasattr(sequences, '__iter__'):
                                for seq in sequences:
                                    first_sequence = seq
                                    break
                            
                            if first_sequence is not None:
                                logger.info(f"🔍 First sequence type: {type(first_sequence)}, value: {first_sequence}")
                                
                                # Ensure we have a list of integers for batch_decode
                                if isinstance(first_sequence, (list, tuple)):
                                    try:
                                        # Convert to list of integers, filtering out None values
                                        token_ids = [int(token) for token in first_sequence if token is not None]
                                        if token_ids:
                                            logger.info(f"🔍 Converted token IDs: {token_ids[:10]}...")  # Show first 10
                                            decoded = processor.batch_decode([token_ids], skip_special_tokens=True)
                                            logger.info(f"🔍 Decoded from first sequence: {decoded}")
                                            return decoded[0] if decoded else ""
                                        else:
                                            logger.warning(f"⚠️ No valid token IDs found in sequence: {first_sequence}")
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"⚠️ Failed to convert sequence to token IDs: {e}")
                                        logger.warning(f"⚠️ Sequence: {first_sequence}")
                                else:
                                    logger.warning(f"⚠️ Unexpected sequence format: {type(first_sequence)}")
                        
                        # Try sequences_ids attribute
                        if hasattr(first_item, 'sequences_ids') and first_item.sequences_ids:
                            sequences_ids = first_item.sequences_ids
                            logger.info(f"🔍 Sequences IDs type: {type(sequences_ids)}")
                            
                            # Get the first sequence ID without using [0]
                            first_sequence_id = None
                            if hasattr(sequences_ids, '__iter__'):
                                for seq_id in sequences_ids:
                                    first_sequence_id = seq_id
                                    break
                            
                            if first_sequence_id is not None:
                                logger.info(f"🔍 First sequence ID type: {type(first_sequence_id)}, value: {first_sequence_id}")
                                
                                # Ensure we have a list of integers for batch_decode
                                if isinstance(first_sequence_id, (list, tuple)):
                                    # Convert to list of integers
                                    try:
                                        token_ids = [int(token) for token in first_sequence_id if token is not None]
                                        if token_ids:
                                            logger.info(f"🔍 Converted sequence ID token IDs: {token_ids[:10]}...")  # Show first 10
                                            decoded = processor.batch_decode([token_ids], skip_special_tokens=True)
                                            logger.info(f"🔍 Decoded from token IDs: {decoded}")
                                            return decoded[0] if decoded else ""
                                        else:
                                            logger.warning(f"⚠️ No valid token IDs found in sequence ID: {first_sequence_id}")
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"⚠️ Failed to convert sequence ID token IDs to integers: {e}")
                                        logger.warning(f"⚠️ Sequence ID: {first_sequence_id}")
                                else:
                                    logger.warning(f"⚠️ Unexpected sequence ID format: {type(first_sequence_id)}")
                    
                    # Handle regular list items
                    elif hasattr(first_item, '__len__') and len(first_item) > 0:
                        decoded = processor.batch_decode([first_item], skip_special_tokens=True)
                        logger.info(f"🔍 Decoded from list item: {decoded}")
                        return decoded[0] if decoded else ""
                    else:
                        # Try to decode the list directly
                        decoded = processor.batch_decode(generation_result, skip_special_tokens=True)
                        logger.info(f"🔍 Decoded from list directly: {decoded}")
                        return decoded[0] if decoded else ""
            
            # Handle WhisperGenerationResult objects specifically
            elif hasattr(generation_result, '__class__') and ('GenerationResult' in str(generation_result.__class__) or 'WhisperGenerationResult' in str(generation_result.__class__)):
                logger.info(f"🔍 Handling WhisperGenerationResult/GenerationResult object")
                
                # Try to access the sequences attribute without subscripting
                if hasattr(generation_result, 'sequences') and generation_result.sequences:
                    sequences = generation_result.sequences
                    logger.info(f"🔍 Sequences type: {type(sequences)}")
                    
                    # Get the first sequence without using [0]
                    first_sequence = None
                    if hasattr(sequences, '__iter__'):
                        for seq in sequences:
                            first_sequence = seq
                            break
                    
                    if first_sequence is not None:
                        logger.info(f"🔍 First sequence type: {type(first_sequence)}, value: {first_sequence}")
                        
                        # Ensure we have a list of integers for batch_decode
                        if isinstance(first_sequence, (list, tuple)):
                            try:
                                # Convert to list of integers, filtering out None values
                                token_ids = [int(token) for token in first_sequence if token is not None]
                                if token_ids:
                                    logger.info(f"🔍 Converted main sequence token IDs: {token_ids[:10]}...")  # Show first 10
                                    decoded = processor.batch_decode([token_ids], skip_special_tokens=True)
                                    logger.info(f"🔍 Decoded from first sequence: {decoded}")
                                    return decoded[0] if decoded else ""
                                else:
                                    logger.warning(f"⚠️ No valid token IDs found in main sequence: {first_sequence}")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"⚠️ Failed to convert main sequence to token IDs: {e}")
                                logger.warning(f"⚠️ Main sequence: {first_sequence}")
                        else:
                            logger.warning(f"⚠️ Unexpected main sequence format: {type(first_sequence)}")
                
                # Try sequences_ids attribute without subscripting
                if hasattr(generation_result, 'sequences_ids') and generation_result.sequences_ids:
                    sequences_ids = generation_result.sequences_ids
                    logger.info(f"🔍 Sequences IDs type: {type(sequences_ids)}")
                    
                    # Get the first sequence ID without using [0]
                    first_sequence_id = None
                    if hasattr(sequences_ids, '__iter__'):
                        for seq_id in sequences_ids:
                            first_sequence_id = seq_id
                            break
                    
                    if first_sequence_id is not None:
                        logger.info(f"🔍 First sequence ID type: {type(first_sequence_id)}, value: {first_sequence_id}")
                        
                        # Ensure we have a list of integers for batch_decode
                        if isinstance(first_sequence_id, (list, tuple)):
                            # Convert to list of integers
                            try:
                                token_ids = [int(token) for token in first_sequence_id if token is not None]
                                if token_ids:
                                    logger.info(f"🔍 Converted main sequence ID token IDs: {token_ids[:10]}...")  # Show first 10
                                    decoded = processor.batch_decode([token_ids], skip_special_tokens=True)
                                    logger.info(f"🔍 Decoded from token IDs: {decoded}")
                                    return decoded[0] if decoded else ""
                                else:
                                    logger.warning(f"⚠️ No valid token IDs found in main sequence ID: {first_sequence_id}")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"⚠️ Failed to convert main sequence ID token IDs to integers: {e}")
                                logger.warning(f"⚠️ Main sequence ID: {first_sequence_id}")
                        else:
                            logger.warning(f"⚠️ Unexpected main sequence ID format: {type(first_sequence_id)}")
                
                # Try alternative attributes
                if hasattr(generation_result, 'hypotheses') and generation_result.hypotheses:
                    hypotheses = generation_result.hypotheses
                    if hasattr(hypotheses, '__iter__'):
                        for hyp in hypotheses:
                            if hyp:
                                logger.info(f"🔍 Using first hypothesis: {hyp}")
                                return str(hyp)
                            break
                
                if hasattr(generation_result, 'tokens') and generation_result.tokens:
                    tokens = generation_result.tokens
                    if hasattr(tokens, '__iter__'):
                        for token in tokens:
                            if token:
                                logger.info(f"🔍 Using first token: {token}")
                                return processor.decode([token], skip_special_tokens=True)
                            break
                
                # Try to get the result directly if it has a method
                if hasattr(generation_result, 'get_result'):
                    try:
                        result = generation_result.get_result()
                        logger.info(f"🔍 Got result from get_result(): {result}")
                        if result:
                            return str(result)
                    except Exception as e:
                        logger.warning(f"⚠️ get_result() failed: {e}")
            
            # Handle other object types with attributes
            else:
                logger.info(f"🔍 CTranslate2 generation result attributes: {dir(generation_result)}")
                
                # Handle different CTranslate2 result formats
                if hasattr(generation_result, 'sequences'):
                    sequences = generation_result.sequences
                    logger.info(f"🔍 Sequences type: {type(sequences)}")
                    
                    if hasattr(sequences, '__iter__'):
                        for seq in sequences:
                            if seq is not None:
                                decoded = processor.batch_decode([seq], skip_special_tokens=True)
                                logger.info(f"🔍 Decoded result: {decoded}")
                                return decoded[0] if decoded else ""
                            break
                
                # Try alternative result formats
                if hasattr(generation_result, 'hypotheses'):
                    hypotheses = generation_result.hypotheses
                    if hasattr(hypotheses, '__iter__'):
                        for hyp in hypotheses:
                            if hyp:
                                logger.info(f"🔍 Using hypothesis: {hyp}")
                                return str(hyp)
                            break
                
                if hasattr(generation_result, 'tokens'):
                    tokens = generation_result.tokens
                    if hasattr(tokens, '__iter__'):
                        for token in tokens:
                            if token:
                                logger.info(f"🔍 Using token: {token}")
                                return processor.decode([token], skip_special_tokens=True)
                            break
            
            # Log the actual result for debugging
            logger.error(f"❌ Unexpected CTranslate2 result format: {generation_result}")
            logger.error(f"❌ Result repr: {repr(generation_result)}")
            
            # Try to convert to string as last resort
            try:
                if hasattr(generation_result, '__str__'):
                    result_str = str(generation_result)
                    if result_str and result_str != repr(generation_result):
                        logger.warning(f"⚠️ Using string representation: {result_str}")
                        return result_str
            except Exception as e:
                logger.error(f"❌ Error converting result to string: {e}")
            
            raise ValueError(f"Invalid CTranslate2 generation result format: {type(generation_result)}")
            
        except Exception as e:
            logger.error(f"❌ Error decoding CTranslate2 result: {e}")
            logger.error(f"❌ Generation result: {generation_result}")
            raise ValueError(f"Invalid CTranslate2 generation result: {str(e)}")
    
    def _transcribe_with_transformers(self, audio_chunk, chunk_count: int, processor, model, language: str) -> str:
        """Transcribe using transformers model"""
        import torch
        
        features = self._prepare_transformers_features(processor, audio_chunk)
        forced_decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
        suppress_tokens = self._text_processor.get_language_suppression_tokens(language)
        
        # Get configuration values for generation parameters - ONLY use ConfigManager
        if not hasattr(self, 'config_manager') or not self.config_manager:
            raise ValueError("❌ ConfigManager is required but not available")
        
        config_dict = self.config_manager.config.dict() if hasattr(self.config_manager.config, 'dict') else self.config_manager.config
        
        # Get max_new_tokens, temperature, beam_size, and do_sample from config - NO FALLBACKS
        ctranslate2_config = config_dict.get('transcription', {}).get('ctranslate2_optimization')
        if not ctranslate2_config or not isinstance(ctranslate2_config, dict):
            raise ValueError(f"❌ ctranslate2_optimization configuration is required but not found or invalid: {ctranslate2_config}")
        
        max_new_tokens = ctranslate2_config.get('max_new_tokens')
        temperature = ctranslate2_config.get('temperature')
        beam_size = ctranslate2_config.get('beam_size')
        do_sample = ctranslate2_config.get('do_sample')
        
        # Validate all required parameters are present
        if max_new_tokens is None:
            raise ValueError("❌ max_new_tokens is required in ctranslate2_optimization config")
        if temperature is None:
            raise ValueError("❌ temperature is required in ctranslate2_optimization config")
        if beam_size is None:
            raise ValueError("❌ beam_size is required in ctranslate2_optimization config")
        if do_sample is None:
            raise ValueError("❌ do_sample is required in ctranslate2_optimization config")
        
        with torch.no_grad():
            predicted_ids = model.generate(
                features, forced_decoder_ids=forced_decoder_ids, suppress_tokens=suppress_tokens,
                num_beams=beam_size, temperature=temperature, do_sample=do_sample, max_new_tokens=max_new_tokens
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
            "config": str(self.config_manager.config),
            "loaded_models_count": cache_info["loaded_models_count"],
            "processor_cache_size": cache_info["processor_cache_size"],
            "cached_models": cache_info["cached_models"]
        }
    

