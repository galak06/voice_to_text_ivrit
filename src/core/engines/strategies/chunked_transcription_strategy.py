#!/usr/bin/env python3
"""
Chunked Transcription Strategy
Handles transcription of large files by creating audio chunks
"""

import logging
import time
import json
import os
from typing import TYPE_CHECKING, List, Optional

from src.core.engines.strategies.base_strategy import BaseTranscriptionStrategy
from src.models.speaker_models import TranscriptionResult, TranscriptionSegment

if TYPE_CHECKING:
    from src.core.engines.base_interface import TranscriptionEngine

logger = logging.getLogger(__name__)


class ChunkedTranscriptionStrategy(BaseTranscriptionStrategy):
    """Strategy for chunked transcription of large files"""
    
    def __init__(self, config=None, app_config=None):
        """Initialize the strategy with dependency injection"""
        self.engine = None
        self.config = config or {}
        self.app_config = app_config or {}
        
        # Extract configuration values with defaults
        self.chunk_duration_seconds = self._get_config_value('chunk_duration_seconds', 120)
        self.output_directories = self._get_config_value('output_directories', {
            'temp_chunks': 'output/temp_chunks',
            'audio_chunks': 'output/audio_chunks'
        })
        self.sample_rate = self._get_config_value('sample_rate', 16000)
        
        logger.debug(f"🎯 ChunkedTranscriptionStrategy initialized with config: chunk_duration={self.chunk_duration_seconds}s, sample_rate={self.sample_rate}Hz")
    
    def _get_config_value(self, key: str, default_value):
        """Get configuration value with fallback to default"""
        try:
            # Check if config is a dictionary
            if isinstance(self.config, dict):
                # Check in strategy-specific config
                if 'chunked_strategy' in self.config and key in self.config['chunked_strategy']:
                    return self.config['chunked_strategy'][key]
                
                # Check in transcription config
                if 'transcription' in self.config and key in self.config['transcription']:
                    return self.config['transcription'][key]
                
                # Check in root config
                if key in self.config:
                    return self.config[key]
            
            # Check if config is an object with attributes
            elif hasattr(self.config, '__getattr__') or hasattr(self.config, '__getattribute__'):
                # Check in strategy-specific config
                if hasattr(self.config, 'chunked_strategy') and hasattr(self.config.chunked_strategy, key):
                    return getattr(self.config.chunked_strategy, key)
                
                # Check in transcription config
                if hasattr(self.config, 'transcription') and hasattr(self.config.transcription, key):
                    return getattr(self.config.transcription, key)
                
                # Check in root config
                if hasattr(self.config, key):
                    return getattr(self.config, key)
            
            # Check in app config
            if isinstance(self.app_config, dict) and key in self.app_config:
                return self.app_config[key]
            elif hasattr(self.app_config, '__getattr__') and hasattr(self.app_config, key):
                return getattr(self.app_config, key)
            
            # Return default
            return default_value
            
        except Exception as e:
            logger.debug(f"Error getting config value for {key}: {e}")
            return default_value
    
    def execute(self, audio_file_path: str, model_name: str, engine: 'TranscriptionEngine') -> TranscriptionResult:
        """Execute chunked transcription strategy"""
        logger.info(f"🎯 Using ChunkedTranscriptionStrategy for: {audio_file_path}")
        
        # Store engine reference for later use
        self.engine = engine
        
        # Store engine type information for speaker enhancement decision
        self.engine_type = getattr(engine, 'engine_type', None)
        if not self.engine_type:
            # Try to infer from engine class name or configuration
            engine_class_name = engine.__class__.__name__
            if hasattr(engine, 'config') and hasattr(engine.config, 'engine_type'):
                self.engine_type = engine.config.engine_type
            elif 'Consolidated' in engine_class_name:
                self.engine_type = 'consolidated'
            else:
                self.engine_type = 'unknown'
        
        logger.info(f"🎯 Engine type detected: {self.engine_type}")
        
        # Clean up any leftover temp chunks from previous runs using the engine's cleanup manager
        cleanup_manager = getattr(engine, '_cleanup_manager', None)
        if cleanup_manager:
            cleanup_manager.auto_cleanup_after_transcription()
        
        # Create necessary directories
        self._create_chunk_directories()
        
        audio_data, sample_rate, duration = self._load_audio(audio_file_path)
        # Ensure sample_rate is an integer
        sample_rate = int(sample_rate)
        
        # Store audio data and sample rate for chunk enhancement
        self._audio_data = audio_data
        self._sample_rate = sample_rate
        
        # Update sample rate from config if different
        if self.sample_rate != sample_rate:
            logger.info(f"ℹ️ Updating sample rate from {self.sample_rate}Hz to {sample_rate}Hz (from audio file)")
            self.sample_rate = sample_rate
        
        total_chunks = self._calculate_chunks(duration, sample_rate)
        
        # Create initial progress files for all chunks
        self._create_initial_progress_files(total_chunks, duration)
        
        # Create all audio chunks upfront
        self._create_all_audio_chunks(audio_data, sample_rate, total_chunks, duration)
        
        all_segments = self._process_chunks(audio_data, sample_rate, total_chunks, engine, model_name)
        
        return self._create_result(all_segments, duration, model_name, audio_file_path)
    
    def _load_audio(self, audio_file_path: str):
        """Load and validate audio file"""
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            import librosa
            audio_data, sample_rate = librosa.load(audio_file_path, sr=self.sample_rate, mono=True)
            duration = len(audio_data) / sample_rate
            logger.info(f"✅ Audio loaded: {duration:.1f}s at {sample_rate}Hz")
            return audio_data, sample_rate, duration
        except ImportError:
            logger.error("❌ Librosa not available")
            raise ImportError("Librosa is required for audio processing")
        except Exception as e:
            logger.error(f"❌ Error loading audio: {e}")
            raise
    
    def _calculate_chunks(self, duration: float, sample_rate: int) -> int:
        """Calculate number of chunks needed using injected configuration"""
        samples_per_chunk = self.chunk_duration_seconds * sample_rate
        total_chunks = max(1, int((duration * sample_rate + samples_per_chunk - 1) // samples_per_chunk))
        logger.info(f"📊 Processing {total_chunks} chunks of {self.chunk_duration_seconds}s each")
        return total_chunks
    
    def _process_chunks(self, audio_data, sample_rate: int, total_chunks: int, engine, model_name: str) -> List[TranscriptionSegment]:
        """Process audio chunks and return segments"""
        all_segments: List[TranscriptionSegment] = []
        start_time = time.time()
        chunk_duration_seconds = 120
        
        for chunk_num in range(total_chunks):
            # Update progress status to "processing"
            self._update_chunk_progress(chunk_num + 1, "processing", None, None)
            
            segment = self._process_single_chunk(audio_data, sample_rate, chunk_num, total_chunks, chunk_duration_seconds, engine, model_name)
            if segment:
                all_segments.append(segment)
                
                # Get the actual speaker ID and metadata from the enhanced segment
                speaker_id = segment.speaker
                segment_text: str = segment.text
                
                # Update progress with enhanced speaker information and metadata
                self._update_chunk_progress(chunk_num + 1, "completed", segment_text, None, speaker_id, segment)
                
                # Log enhancement results
                if hasattr(segment, 'metadata') and segment.metadata and segment.metadata.get('enhancement_applied'):
                    logger.info(f"🎯 Chunk {chunk_num + 1}: Enhanced with {segment.metadata.get('detected_speakers', 1)} speakers")
                
            else:
                # Update progress status to "error"
                self._update_chunk_progress(chunk_num + 1, "error", None, "Transcription failed")
        
        logger.info(f"🎯 Chunked transcription completed: {time.time() - start_time:.1f}s, {len(all_segments)} segments")
        return all_segments
    
    def _process_single_chunk(self, audio_data, sample_rate: int, chunk_num: int, total_chunks: int, chunk_duration_seconds: int, engine, model_name: str) -> Optional[TranscriptionSegment]:
        """Process a single audio chunk"""
        chunk_start, chunk_end = self._calculate_chunk_timing(chunk_num, chunk_duration_seconds, sample_rate, audio_data)
        audio_chunk = self._extract_audio_chunk(audio_data, chunk_start, chunk_end, sample_rate)
        
        if len(audio_chunk) == 0:
            return None
        
        logger.info(f"🔧 Processing Chunk {chunk_num + 1}/{total_chunks}: {chunk_start:.1f}s - {chunk_end:.1f}s")
        
        return self._transcribe_and_create_segment(audio_chunk, chunk_num, chunk_start, chunk_end, engine, model_name)
    
    def _calculate_chunk_timing(self, chunk_num: int, chunk_duration_seconds: int, sample_rate: int, audio_data):
        """Calculate chunk start and end times"""
        chunk_start = chunk_num * chunk_duration_seconds
        chunk_end = min((chunk_num + 1) * chunk_duration_seconds, len(audio_data) / sample_rate)
        return chunk_start, chunk_end
    
    def _extract_audio_chunk(self, audio_data, chunk_start: float, chunk_end: float, sample_rate: int):
        """Extract audio chunk from full audio data"""
        start_sample = int(chunk_start * sample_rate)
        end_sample = int(chunk_end * sample_rate)
        return audio_data[start_sample:end_sample]
    
    def _transcribe_and_create_segment(self, audio_chunk, chunk_num: int, chunk_start: float, chunk_end: float, engine, model_name: str):
        """Transcribe chunk and create segment with speaker enhancement"""
        try:
            chunk_text = engine._transcribe_chunk(audio_chunk, chunk_num + 1, chunk_start, chunk_end, model_name)
            
            if chunk_text and chunk_text.strip():
                # Create initial segment with temporary speaker ID (will be enhanced)
                temp_speaker_id = f"temp_speaker_{chunk_num + 1}"
                initial_segment = TranscriptionSegment(start=chunk_start, end=chunk_end, text=chunk_text, speaker=temp_speaker_id)
                
                # Apply speaker enhancement to this individual chunk using pyannote.audio
                enhanced_segment = self._enhance_chunk_with_speakers(initial_segment, chunk_num, chunk_start, chunk_end)
                
                logger.info(f"✅ Chunk {chunk_num + 1} completed with real speaker detection")
                return enhanced_segment
            else:
                logger.warning(f"⚠️ Chunk {chunk_num + 1}: No text produced")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing chunk {chunk_num + 1}: {e}")
            return None
    
    def _update_chunk_progress(self, chunk_num: int, status: str, text: Optional[str] = None, error_message: Optional[str] = None, speaker_id: Optional[str] = None, enhanced_segment: Optional[TranscriptionSegment] = None):
        """Update chunk progress in JSON file"""
        try:
            # Find the correct chunk file by pattern matching using injected configuration
            import glob
            temp_chunks_dir = self.output_directories['temp_chunks']
            pattern = f"{temp_chunks_dir}/chunk_{chunk_num:03d}_*s_*s.json"
            matching_files = glob.glob(pattern)
            
            if matching_files:
                chunk_file = matching_files[0]  # Take the first (should be only one)
                with open(chunk_file, 'r') as f:
                    chunk_data = json.load(f)
                
                # Update progress information
                chunk_data['status'] = status
                chunk_data['processing_completed'] = time.time() if status in ['completed', 'error'] else None
                
                if text:
                    chunk_data['text'] = text
                    chunk_data['transcription_length'] = len(text)
                    chunk_data['words_estimated'] = len(text.split())
                
                if error_message:
                    chunk_data['error_message'] = error_message
                
                # Add speaker information if available
                if speaker_id:
                    chunk_data['speaker_id'] = speaker_id
                    chunk_data['speaker_label'] = f"Speaker {speaker_id.split('_')[-1]}" if '_' in speaker_id else speaker_id
                
                # Add enhanced metadata if available
                if enhanced_segment and hasattr(enhanced_segment, 'metadata') and enhanced_segment.metadata:
                    chunk_data['enhanced_metadata'] = enhanced_segment.metadata
                    chunk_data['enhancement_applied'] = True
                    chunk_data['enhancement_strategy'] = enhanced_segment.metadata.get('enhancement_strategy', 'unknown')
                    chunk_data['detected_speakers'] = enhanced_segment.metadata.get('detected_speakers', 1)
                    
                    # Add speaker time ranges if available
                    if 'speaker_time_ranges' in enhanced_segment.metadata:
                        chunk_data['speaker_time_ranges'] = enhanced_segment.metadata['speaker_time_ranges']
                    
                    # Add analysis details if available
                    if 'analysis_details' in enhanced_segment.metadata:
                        chunk_data['analysis_details'] = enhanced_segment.metadata['analysis_details']
                else:
                    chunk_data['enhancement_applied'] = False
                    chunk_data['enhancement_strategy'] = 'none'
                
                # Write updated progress back to file
                with open(chunk_file, 'w') as f:
                    json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            else:
                logger.debug(f"⚠️ No chunk file found for chunk {chunk_num}")
                    
        except Exception as e:
            logger.debug(f"⚠️ Could not update chunk progress for chunk {chunk_num}: {e}")
    

    
    def _create_chunk_directories(self):
        """Create necessary directories for chunking using injected configuration"""
        try:
            # Create directories from configuration
            for dir_type, dir_path in self.output_directories.items():
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"📁 Created directory: {dir_type} -> {dir_path}")
            
            logger.info(f"📁 Created {len(self.output_directories)} chunk directories")
        except Exception as e:
            logger.warning(f"⚠️ Error creating chunk directories: {e}")
    
    def _create_initial_progress_files(self, total_chunks: int, duration: float):
        """Create initial progress files for all chunks using injected configuration"""
        try:
            temp_chunks_dir = self.output_directories['temp_chunks']
            audio_chunks_dir = self.output_directories['audio_chunks']
            
            for chunk_num in range(total_chunks):
                chunk_start = chunk_num * self.chunk_duration_seconds
                chunk_end = min((chunk_num + 1) * self.chunk_duration_seconds, duration)
                
                # Create progress file using injected configuration
                chunk_file = f"{temp_chunks_dir}/chunk_{chunk_num + 1:03d}_{int(chunk_start)}s_{int(chunk_end)}s.json"
                progress_data = {
                    "chunk_number": chunk_num + 1,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "status": "pending",
                    "created_at": time.time(),
                    "text": "",
                    "processing_started": None,
                    "processing_completed": None,
                    "audio_chunk_file": f"{audio_chunks_dir}/audio_chunk_{chunk_num + 1:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav",
                    "error_message": None
                }
                
                with open(chunk_file, 'w') as f:
                    json.dump(progress_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"📁 Created {total_chunks} initial progress files in {temp_chunks_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Error creating initial progress files: {e}")
    
    def _create_all_audio_chunks(self, audio_data, sample_rate: int, total_chunks: int, duration: float):
        """Create all audio chunks upfront using injected configuration"""
        logger.info(f"🎵 Creating {total_chunks} audio chunks...")
        
        for chunk_num in range(total_chunks):
            chunk_start = chunk_num * self.chunk_duration_seconds
            chunk_end = min((chunk_num + 1) * self.chunk_duration_seconds, duration)
            
            # Extract audio chunk
            audio_chunk = self._extract_audio_chunk(audio_data, chunk_start, chunk_end, sample_rate)
            
            # Save audio chunk as WAV file
            self._save_audio_chunk(audio_chunk, sample_rate, chunk_num, chunk_start, chunk_end)
            
            # Update progress status to "chunk_created"
            self._update_chunk_progress(chunk_num + 1, "chunk_created", None, None)
            
            logger.debug(f"💾 Created audio chunk: audio_chunk_{chunk_num + 1:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav")
        
        logger.info(f"✅ All {total_chunks} audio chunks created successfully")
    
    def _save_audio_chunk(self, audio_chunk, sample_rate: int, chunk_num: int, chunk_start: float, chunk_end: float):
        """Save audio chunk as WAV file using injected configuration"""
        try:
            import soundfile as sf
            
            # Create filename using injected configuration
            filename = f"audio_chunk_{chunk_num + 1:03d}_{int(chunk_start)}s_{int(chunk_end)}s.wav"
            filepath = f"{self.output_directories['audio_chunks']}/{filename}"
            
            # Save as WAV file
            sf.write(filepath, audio_chunk, sample_rate)
            logger.debug(f"💾 Saved audio chunk: {filename}")
            
        except ImportError:
            logger.warning("⚠️ soundfile not available, skipping audio chunk save")
        except Exception as e:
            logger.warning(f"⚠️ Error saving audio chunk {chunk_num + 1}: {e}")
    
    def _create_result(self, all_segments, duration: float, model_name: str, audio_file_path: str):
        """Create final transcription result with optional speaker enhancement"""
        total_text = " ".join([seg.text for seg in all_segments])
        
        # Organize segments by speaker
        speakers_data = {}
        for segment in all_segments:
            speaker_id = segment.speaker
            if speaker_id not in speakers_data:
                speakers_data[speaker_id] = []
            speakers_data[speaker_id].append(segment)
        
        # Create initial result
        initial_result = TranscriptionResult(
            success=True, speakers=speakers_data, full_text=total_text,
            transcription_time=0.0, model_name=model_name, audio_file=audio_file_path, speaker_count=len(speakers_data)
        )
        
        # Apply speaker enhancement if engine supports it and speaker diarization is enabled
        enhanced_result = self._apply_speaker_enhancement(initial_result, audio_file_path)
        
        # Auto-cleanup temp chunks after transcription completion
        if hasattr(self, 'engine'):
            cleanup_manager = getattr(self.engine, '_cleanup_manager', None)
            if cleanup_manager:
                cleanup_manager.auto_cleanup_after_transcription()
        
        return enhanced_result
    
    def _apply_speaker_enhancement(self, transcription_result: TranscriptionResult, audio_file_path: str) -> TranscriptionResult:
        """Apply speaker enhancement if available and enabled"""
        try:
            # Check if speaker enhancement is available and should be applied
            if not self._should_apply_speaker_enhancement():
                logger.info("ℹ️ Speaker enhancement not enabled, returning original result")
                return transcription_result
            
            logger.info("🎯 Applying speaker enhancement to chunked transcription result")
            
            # Import speaker enhancement components
            from src.core.factories.speaker_enhancement_factory import create_speaker_enhancement_orchestrator
            from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService
            
            # Create speaker service with default config
            speaker_config = None
            if hasattr(self, 'config') and self.config:
                from src.core.factories.speaker_config_factory import SpeakerConfigFactory
                speaker_config = SpeakerConfigFactory.get_config('conversation')
            
            speaker_service = SpeakerTranscriptionService(speaker_config, self.config, None)
            
            # Create enhancement orchestrator
            enhancement_orchestrator = create_speaker_enhancement_orchestrator(speaker_service)
            
            # Apply enhancement
            enhanced_result = enhancement_orchestrator.enhance_transcription(
                transcription_result, audio_file_path, strategy='chunked'
            )
            
            if enhanced_result.success:
                logger.info(f"✅ Speaker enhancement successful: {len(enhanced_result.speakers)} speakers detected")
                return enhanced_result
            else:
                logger.warning("⚠️ Speaker enhancement failed, returning original result")
                return transcription_result
                
        except Exception as e:
            logger.error(f"❌ Error applying speaker enhancement: {e}")
            logger.warning("⚠️ Continuing with original transcription result")
            return transcription_result
    
    def _should_apply_speaker_enhancement(self) -> bool:
        """Check if speaker enhancement should be applied"""
        try:
            # Check if we're using speaker-diarization engine
            if hasattr(self, 'engine') and self.engine:
                # Check engine type through app config or other means
                if hasattr(self, 'app_config') and self.app_config:
                    # This is a simplified check - in practice, you might want to pass this information
                    # through the strategy execution context
                    return True
                
                # Check if the engine has speaker enhancement capabilities
                if hasattr(self.engine, '_enhance_result_with_speakers'):
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking speaker enhancement capability: {e}")
            return False
    
    def _enhance_chunk_with_speakers(self, initial_segment: TranscriptionSegment, chunk_num: int, chunk_start: float, chunk_end: float) -> TranscriptionSegment:
        """Apply speaker enhancement to an individual chunk using strategy pattern"""
        try:
            # Import enhancement strategies
            from src.core.services.chunk_enhancement_strategies import (
                ChunkEnhancementStrategyFactory, 
                ChunkEnhancementContext
            )
            
            # Create enhancement context
            context = ChunkEnhancementContext(
                chunk_num=chunk_num,
                chunk_start=chunk_start,
                chunk_end=chunk_end,
                audio_data=getattr(self, '_audio_data', None),
                sample_rate=getattr(self, '_sample_rate', 16000) or 16000,  # Default to 16000 if None
                config=self.config,
                enhancement_level=self._get_enhancement_level()
            )
            
            # Create strategy factory and get appropriate strategy
            strategy_factory = ChunkEnhancementStrategyFactory(self.config)
            enhancement_strategy = strategy_factory.get_enhancement_strategy(context)
            
            logger.info(f"🎯 Using enhancement strategy: {enhancement_strategy.get_strategy_name()} for chunk {chunk_num + 1}")
            
            # Apply enhancement
            enhanced_segment = enhancement_strategy.enhance(initial_segment, context)
            
            # Log enhancement results
            if hasattr(enhanced_segment, 'metadata') and enhanced_segment.metadata:
                metadata = enhanced_segment.metadata
                if metadata.get('enhancement_applied'):
                    logger.info(f"✅ Chunk {chunk_num + 1}: Enhanced with {metadata.get('detected_speakers', 1)} speakers")
                else:
                    logger.info(f"ℹ️ Chunk {chunk_num + 1}: No enhancement applied")
            
            return enhanced_segment
            
        except Exception as e:
            logger.error(f"❌ Error enhancing chunk {chunk_num + 1} with speakers: {e}")
            logger.warning(f"⚠️ Continuing with original segment for chunk {chunk_num + 1}")
            return initial_segment
    
    def _get_enhancement_level(self) -> str:
        """Determine the enhancement level based on configuration and engine type"""
        try:
            # FIRST: Check if speaker diarization is disabled in config
            if hasattr(self, 'config') and self.config:
                speaker_config = getattr(self.config, 'speaker_diarization', {})
                if speaker_config and not speaker_config.get('enabled', True):
                    logger.info("ℹ️ Speaker diarization disabled in config, using no enhancement")
                    return 'none'
            
            # SECOND: Check if we're using speaker-diarization engine
            if hasattr(self, 'engine_type') and self.engine_type == 'speaker-diarization':
                logger.info("🎯 Speaker-diarization engine detected, using advanced enhancement")
                return 'advanced'
            
            # Check if the engine has speaker enhancement capabilities AND it's enabled
            if hasattr(self, 'engine') and self.engine:
                if hasattr(self.engine, '_enhance_result_with_speakers'):
                    # Also check if speaker diarization is actually enabled in the engine
                    if hasattr(self.engine, '_speaker_diarization_enabled'):
                        if not self.engine._speaker_diarization_enabled:
                            logger.info("ℹ️ Engine has speaker enhancement but diarization is disabled, using no enhancement")
                            return 'none'
                    return 'standard'
            
            # Check configuration for enhancement preferences
            if hasattr(self, 'config') and self.config:
                if hasattr(self.config, 'speaker') and self.config.speaker:
                    if getattr(self.config.speaker, 'enhancement_level', None):
                        return self.config.speaker.enhancement_level
            
            # Check if we're in the main transcription orchestrator with speaker-diarization
            if hasattr(self, 'engine') and hasattr(self.engine, 'config'):
                engine_config = getattr(self.engine, 'config', None)
                if engine_config and hasattr(engine_config, 'engine_type'):
                    if engine_config.engine_type == 'speaker-diarization':
                        logger.info("🎯 Speaker-diarization engine detected via config, using advanced enhancement")
                        return 'advanced'
            
            return 'basic'
            
        except Exception as e:
            logger.debug(f"Error determining enhancement level: {e}")
            return 'basic'
    
    def _create_temp_chunk_audio(self, chunk_num: int, chunk_start: float, chunk_end: float) -> Optional[str]:
        """Create temporary audio file for chunk speaker diarization"""
        try:
            import tempfile
            import soundfile as sf
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Extract audio data for this chunk
            if hasattr(self, '_audio_data') and hasattr(self, '_sample_rate'):
                start_sample = int(chunk_start * self._sample_rate)
                end_sample = int(chunk_end * self._sample_rate)
                chunk_audio = self._audio_data[start_sample:end_sample]
                
                # Save as temporary WAV file
                sf.write(temp_file_path, chunk_audio, self._sample_rate)
                logger.debug(f"💾 Created temp audio for chunk {chunk_num + 1}: {temp_file_path}")
                return temp_file_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating temp audio for chunk {chunk_num + 1}: {e}")
            return None
    
    def _perform_chunk_speaker_diarization(self, chunk_audio_file: str, chunk_start: float, chunk_end: float) -> List[tuple]:
        """Perform speaker diarization on a single chunk"""
        try:
            # Import speaker service
            from src.core.orchestrator.speaker_transcription_service import SpeakerTranscriptionService
            from src.core.factories.speaker_config_factory import SpeakerConfigFactory
            
            # Create speaker service with conversation preset
            speaker_config = SpeakerConfigFactory.get_config('conversation')
            speaker_service = SpeakerTranscriptionService(speaker_config, self.config, None)
            
            # Perform speaker diarization
            speaker_segments = speaker_service._perform_speaker_diarization(chunk_audio_file)
            
            if speaker_segments:
                # Adjust time ranges to be relative to the chunk
                adjusted_segments = []
                for start_time, end_time in speaker_segments:
                    adjusted_start = chunk_start + start_time
                    adjusted_end = chunk_start + end_time
                    adjusted_segments.append((adjusted_start, adjusted_end))
                
                logger.info(f"🎯 Speaker diarization successful: {len(adjusted_segments)} segments detected")
                return adjusted_segments
            else:
                logger.info("ℹ️ No speaker segments detected")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error in chunk speaker diarization: {e}")
            return []
    
    def _cleanup_temp_chunk_audio(self, temp_file_path: str):
        """Clean up temporary chunk audio file"""
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.debug(f"🧹 Cleaned up temp audio: {temp_file_path}")
        except Exception as e:
            logger.debug(f"⚠️ Error cleaning up temp audio: {e}")
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return "ChunkedTranscriptionStrategy"
