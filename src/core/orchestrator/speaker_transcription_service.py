#!/usr/bin/env python3
"""
Speaker Transcription Service for ivrit-ai models
Handles speaker diarization with configurable parameters
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, List

from src.models.speaker_models import SpeakerConfig, TranscriptionResult, SpeakerDiarizationRequest, TranscriptionSegment
from src.core.factories.engine_factory import TranscriptionEngineFactory
from src.core.factories.file_validator_factory import FileValidatorFactory
from src.models import AppConfig
from src.core.logic.result_builder import ResultBuilder

logger = logging.getLogger(__name__)

class SpeakerTranscriptionService:
    """
    Service for transcribing audio with speaker diarization
    Uses Strategy Pattern for different transcription engines
    """
    
    def __init__(self, config: Optional[SpeakerConfig] = None, app_config: Optional[AppConfig] = None, output_manager: Optional['OutputManager'] = None):
        """
        Initialize the speaker transcription service
        
        Args:
            config: Speaker configuration (uses defaults if None)
            app_config: Application configuration (uses defaults if None)
            output_manager: Output manager instance (uses default if None)
        """
        from src.models import AppConfig
        
        self.config = config or SpeakerConfig()
        self.app_config = app_config or AppConfig()
        
        # Import OutputManager only when needed to avoid circular imports
        if output_manager is None:
            from src.output_data import OutputManager
            self.output_manager = OutputManager()
        else:
            self.output_manager = output_manager
        
        # Use the unified FileValidator for file validation
        self.file_validator = FileValidatorFactory.create_audio_validator(self.app_config)
    
    def speaker_diarization(
        self, 
        audio_file_path: str, 
        model_name: str = None,
        save_output: bool = True,
        run_session_id: str = None,
        engine_type: str = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file with speaker diarization
        
        Args:
            audio_file_path: Path to the audio file
            model_name: Model to use for transcription
            save_output: Whether to save outputs in all formats
            
        Returns:
            TranscriptionResult with speaker-separated data
        """
        # Create request object for validation
        request = SpeakerDiarizationRequest(
            audio_file_path=audio_file_path,
            model_name=model_name,
            save_output=save_output,
            run_session_id=run_session_id,
            speaker_config=self.config
        )
        
        return self._process_diarization_request(request, engine_type)
    
    def _process_diarization_request(self, request: SpeakerDiarizationRequest, engine_type: str = None) -> TranscriptionResult:
        """Process a speaker diarization request"""
        start_time = time.time()
        logger.info(f"Starting diarization for: {request.audio_file_path}")
        
        # Validate audio file
        if not self._validate_audio_file(request.audio_file_path):
            return self._create_error_result(request, start_time, "Invalid audio file")
        
        # Determine model name
        model_name = self._determine_model_name(request)
        
        try:
            # Use provided engine type or determine based on file size
            if engine_type is None:
                engine_type = self._determine_engine_type(request.audio_file_path)
            else:
                logger.info(f"🎯 Using user-specified engine: {engine_type}")
            
            # Perform transcription
            result = self._transcribe_with_engine(engine_type, request.audio_file_path, model_name)
            
            if result.success:
                logger.info(f"Transcription successful")
                
                # Save outputs if requested
                if request.save_output:
                    self._save_outputs(result, request.audio_file_path, model_name, request.run_session_id)
                
                return result
            
            # Transcription failed
            logger.error(f"Transcription failed")
            return self._create_error_result(request, start_time, "Transcription engine failed")
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return self._create_error_result(request, start_time, str(e))
    
    def _determine_model_name(self, request: SpeakerDiarizationRequest) -> str:
        """Determine the model name to use"""
        if request.model_name is not None:
            return request.model_name
        return self.app_config.transcription.default_model
    
    def _determine_engine_type(self, audio_file_path: str) -> str:
        """Determine engine type based on file size"""
        file_size = Path(audio_file_path).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Get constants from app configuration
        large_file_threshold = 100  # Default threshold
        if hasattr(self.app_config, 'system') and hasattr(self.app_config.system, 'constants'):
            large_file_threshold = getattr(self.app_config.system.constants, 'large_file_threshold_mb', 100)
        
        if file_size_mb > large_file_threshold:
            logger.info(f"📁 Large file detected ({file_size_mb:.1f}MB), using optimized-whisper with chunking")
            return "optimized-whisper"
        else:
            logger.info(f"📁 Small file detected ({file_size_mb:.1f}MB), using optimized-whisper")
            return "optimized-whisper"
    
    def _create_error_result(self, request: SpeakerDiarizationRequest, start_time: float, 
                           error_message: str) -> TranscriptionResult:
        """Create error result with consistent format"""
        return TranscriptionResult(
            success=False,
            speakers={},
            full_text="",
            transcription_time=time.time() - start_time,
            model_name=request.model_name or "unknown",
            audio_file=request.audio_file_path,
            speaker_count=0,
            error_message=error_message
        )
    
    def _transcribe_with_engine(self, engine_type: str, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using a specific engine with speaker diarization"""
        try:
            # First, perform speaker diarization to get speaker segments
            speaker_segments = self._perform_speaker_diarization(audio_file_path)
            
            if not speaker_segments:
                logger.warning("⚠️ No speaker segments detected, using single speaker")
                # Fallback to single speaker transcription
                engine = TranscriptionEngineFactory.create_engine(engine_type, self.config)
                result = engine.transcribe(audio_file_path, model_name)
                
                # Convert to speaker format
                return TranscriptionResult(
                    success=result.success,
                    speakers={"0": [TranscriptionSegment(
                        start=0,
                        end=result.transcription_time if hasattr(result, 'transcription_time') else 120,
                        text=result.full_text if hasattr(result, 'full_text') else "",
                        speaker="0"
                    )]},
                    full_text=result.full_text if hasattr(result, 'full_text') else "",
                    transcription_time=result.transcription_time if hasattr(result, 'transcription_time') else 0,
                    model_name=model_name,
                    audio_file=audio_file_path,
                    speaker_count=1
                )
            
            # Now transcribe each speaker segment
            all_speakers = {}
            total_text = ""
            
            for i, (start_time, end_time) in enumerate(speaker_segments):
                # Extract audio segment
                segment_audio = self._extract_audio_segment(audio_file_path, start_time, end_time)
                
                # Transcribe this segment
                engine = TranscriptionEngineFactory.create_engine(engine_type, self.config)
                segment_result = engine.transcribe(segment_audio, model_name)
                
                # Create transcription segment
                segment = TranscriptionSegment(
                    start=start_time,
                    end=end_time,
                    text=segment_result.full_text if hasattr(segment_result, 'full_text') else "",
                    speaker=f"speaker_{i}"
                )
                
                speaker_id = f"speaker_{i}"
                if speaker_id not in all_speakers:
                    all_speakers[speaker_id] = []
                all_speakers[speaker_id].append(segment)
                total_text += " " + segment.text
            
            return TranscriptionResult(
                success=True,
                speakers=all_speakers,
                full_text=total_text.strip(),
                transcription_time=0,  # Will be calculated by caller
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(all_speakers)
            )
            
        except Exception as e:
            logger.error(f"Error in transcription with speaker diarization: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=f"Failed to transcribe with speaker diarization: {str(e)}"
            )
    
    def _create_fallback_two_speakers(self, audio_file_path: str) -> List[tuple]:
        """Create exactly 2 speakers as a fallback method"""
        try:
            import librosa
            
            # Load audio to get duration
            audio, sr = librosa.load(audio_file_path, sr=16000)
            duration = len(audio) / sr
            
            # Create exactly 2 speakers: first half and second half
            mid_point = duration / 2
            speaker1 = (0, mid_point)
            speaker2 = (mid_point, duration)
            
            logger.info(f"🔧 Created fallback 2 speakers: {speaker1}, {speaker2}")
            return [speaker1, speaker2]
            
        except Exception as e:
            logger.error(f"Fallback 2-speaker creation failed: {e}")
            # Return default 2 segments
            return [(0, 60), (60, 120)]

    def _perform_speaker_diarization(self, audio_file_path: str) -> List[tuple]:
        """Perform speaker diarization using pyannote.audio or fallback method"""
        try:
            # Try to use pyannote.audio for speaker diarization
            return self._pyannote_speaker_diarization(audio_file_path)
        except ImportError:
            logger.warning("⚠️ pyannote.audio not available, using fallback method")
            return self._fallback_speaker_diarization(audio_file_path)
        except Exception as e:
            logger.warning(f"⚠️ pyannote.audio failed: {e}, using fallback method")
            return self._fallback_speaker_diarization(audio_file_path)
    
    def _merge_short_segments(self, segments: List[tuple], min_duration: float = 2.0) -> List[tuple]:
        """Merge very short segments to reduce over-segmentation"""
        if not segments:
            return segments
        
        merged_segments = []
        current_start, current_end = segments[0]
        
        for start, end in segments[1:]:
            # If segments are very close together, merge them
            if start - current_end < 1.0:  # Less than 1 second gap
                current_end = end
            else:
                # Check if current segment is long enough
                if current_end - current_start >= min_duration:
                    merged_segments.append((current_start, current_end))
                current_start, current_end = start, end
        
        # Add the last segment
        if current_end - current_start >= min_duration:
            merged_segments.append((current_start, current_end))
        
        logger.info(f"🔧 Merged segments: {len(segments)} → {len(merged_segments)}")
        return merged_segments

    def _enforce_exactly_two_speakers(self, segments: List[tuple]) -> List[tuple]:
        """Force exactly 2 speakers by merging and redistributing segments"""
        if not segments:
            return segments
        
        logger.info(f"🔧 Enforcing exactly 2 speakers from {len(segments)} segments")
        
        # If we have only 1 segment, duplicate it to create 2 speakers
        if len(segments) == 1:
            start, end = segments[0]
            mid_point = (start + end) / 2
            return [(start, mid_point), (mid_point, end)]
        
        # If we have exactly 2 segments, return as is
        if len(segments) == 2:
            return segments
        
        # If we have more than 2 segments, merge them into exactly 2
        if len(segments) > 2:
            # Sort segments by start time
            sorted_segments = sorted(segments, key=lambda x: x[0])
            
            # Find the middle point to split into 2 groups
            total_duration = sum(end - start for start, end in sorted_segments)
            target_duration = total_duration / 2
            
            # Group segments into 2 speakers
            speaker1_segments = []
            speaker2_segments = []
            current_duration = 0
            
            for start, end in sorted_segments:
                segment_duration = end - start
                if current_duration < target_duration:
                    speaker1_segments.append((start, end))
                    current_duration += segment_duration
                else:
                    speaker2_segments.append((start, end))
            
            # Merge segments for each speaker
            if speaker1_segments:
                speaker1_start = min(start for start, end in speaker1_segments)
                speaker1_end = max(end for start, end in speaker1_segments)
                speaker1_merged = (speaker1_start, speaker1_end)
            else:
                speaker1_merged = (0, 1)
            
            if speaker2_segments:
                speaker2_start = min(start for start, end in speaker2_segments)
                speaker2_end = max(end for start, end in speaker2_segments)
                speaker2_merged = (speaker2_start, speaker2_end)
            else:
                speaker2_merged = (1, 2)
            
            logger.info(f"🔧 Merged {len(segments)} segments into exactly 2 speakers")
            return [speaker1_merged, speaker2_merged]
        
        return segments

    def _pyannote_speaker_diarization(self, audio_file_path: str) -> List[tuple]:
        """Use pyannote.audio for speaker diarization with proper configuration"""
        try:
            import os
            from pyannote.audio import Pipeline
            from pyannote.audio.pipelines.utils.hook import ProgressHook
            
            # Get HuggingFace token from environment variable
            hf_token = os.getenv('HF_TOKEN')
            if not hf_token:
                logger.warning("⚠️ HF_TOKEN environment variable not set, using fallback method")
                raise ImportError("No HuggingFace token available")
            
            # Initialize pipeline with proper configuration
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization@2.1",
                use_auth_token=hf_token
            )
            
            # Configure pipeline for 2 speakers
            min_speakers = getattr(self.config, 'min_speakers', 2)
            max_speakers = getattr(self.config, 'max_speakers', 2)
            
            # Set pipeline parameters for better 2-speaker detection
            pipeline.instantiate({
                "segmentation": {
                    "min_duration_off": 0.5,  # Minimum silence duration
                    "threshold": 0.5,          # Segmentation threshold
                },
                "clustering": {
                    "min_clusters": min_speakers,
                    "max_clusters": max_speakers,
                    "method": "centroid",      # Use centroid clustering for better results
                }
            })
            
            # Perform diarization
            logger.info(f"🎯 Starting pyannote.audio speaker diarization for {min_speakers}-{max_speakers} speakers...")
            diarization = pipeline(audio_file_path)
            
            # Extract and merge speaker segments
            segments = []
            current_speaker = None
            current_start = None
            current_end = None
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # If this is a new speaker, save the previous segment
                if current_speaker is not None and current_speaker != speaker:
                    if current_start is not None and current_end is not None:
                        segments.append((current_start, current_end))
                    current_start = turn.start
                    current_end = turn.end
                    current_speaker = speaker
                else:
                    # Same speaker, extend the segment
                    if current_start is None:
                        current_start = turn.start
                    current_end = turn.end
                    current_speaker = speaker
            
            # Add the last segment
            if current_start is not None and current_end is not None:
                segments.append((current_start, current_end))
            
            # Filter segments by minimum duration
            min_duration = getattr(self.config, 'min_speaker_duration', 0.5)
            filtered_segments = []
            for start, end in segments:
                if end - start >= min_duration:
                    filtered_segments.append((start, end))
            
            # Merge short segments
            min_segment_duration = getattr(self.config, 'min_segment_duration', 2.0)
            filtered_segments = self._merge_short_segments(filtered_segments, min_segment_duration)
            
            # Enforce exactly 2 speakers
            filtered_segments = self._enforce_exactly_two_speakers(filtered_segments)
            
            logger.info(f"✅ Pyannote detected {len(filtered_segments)} speaker segments (filtered from {len(segments)})")
            return filtered_segments
            
        except Exception as e:
            logger.error(f"Pyannote speaker diarization failed: {e}")
            raise
    
    def _fallback_speaker_diarization(self, audio_file_path: str) -> List[tuple]:
        """Fallback speaker diarization using simple silence detection"""
        try:
            import librosa
            import numpy as np
            
            # Load audio
            audio, sr = librosa.load(audio_file_path, sr=16000)
            
            # Simple silence detection
            silence_threshold = self.config.silence_threshold
            min_speaker_duration = self.config.min_speaker_duration
            
            # Detect non-silent regions
            non_silent_intervals = librosa.effects.split(
                audio, 
                top_db=20, 
                frame_length=2048, 
                hop_length=512
            )
            
            # Convert to seconds
            segments = []
            for start_frame, end_frame in non_silent_intervals:
                start_time = start_frame / sr
                end_time = end_frame / sr
                
                # Filter by minimum duration
                if end_time - start_time >= min_speaker_duration:
                    segments.append((start_time, end_time))
            
            # Enforce exactly 2 speakers
            segments = self._enforce_exactly_two_speakers(segments)
            
            logger.info(f"✅ Fallback method detected {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Fallback speaker diarization failed: {e}")
            # Use the fallback 2-speaker method
            return self._create_fallback_two_speakers(audio_file_path)
    
    def _extract_audio_segment(self, audio_file_path: str, start_time: float, end_time: float) -> str:
        """Extract audio segment and return temporary file path"""
        try:
            import librosa
            import soundfile as sf
            import tempfile
            import os
            
            # Load audio
            audio, sr = librosa.load(audio_file_path, sr=16000)
            
            # Calculate frame indices
            start_frame = int(start_time * sr)
            end_frame = int(end_time * sr)
            
            # Extract segment
            segment_audio = audio[start_frame:end_frame]
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(temp_file.name, segment_audio, sr)
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to extract audio segment: {e}")
            return audio_file_path  # Fallback to original file
    
    def _validate_audio_file(self, audio_file_path: str) -> bool:
        """
        Validate audio file exists and is accessible using the unified FileValidator
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            True if file is valid, False otherwise
        """
        # Use the unified FileValidator for comprehensive validation
        validation_result = self.file_validator.validate_audio_file(audio_file_path)
        
        if not validation_result['valid']:
            logger.error(f"Audio file validation failed: {validation_result['error']}")
            return False
        
        # Log file information for debugging
        logger.info(f"Audio file: {audio_file_path} ({validation_result['file_size']:,} bytes)")
        return True
    
    def _save_outputs(
        self, 
        result: TranscriptionResult, 
        audio_file_path: str, 
        model_name: str,
        run_session_id: str = None
    ):
        """Save transcription outputs in all formats"""
        try:
            # Convert TranscriptionResult to the format expected by OutputManager
            # The OutputManager expects a dictionary with 'speakers' key
            transcription_data = {
                'speakers': {speaker: [seg.model_dump() for seg in segments] for speaker, segments in result.speakers.items()},
                'full_text': result.full_text,
                'model_name': result.model_name,
                'audio_file': result.audio_file,
                'transcription_time': result.transcription_time,
                'speaker_count': result.speaker_count
            }
            
            # Use the injected output manager
            saved_files = self.output_manager.save_transcription(
                transcription_data=transcription_data,
                audio_file=audio_file_path,
                model=model_name,
                engine="speaker-diarization",
                session_id=run_session_id
            )
            
            logger.info(f"All formats saved:")
            for format_type, file_path in saved_files.items():
                logger.info(f"  📄 {format_type.upper()}: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to save outputs: {e}")
            # Log more details about the error
            import traceback
            logger.error(f"Error details: {traceback.format_exc()}")
    
    def _format_conversation_text(self, speakers: Dict[str, List]) -> str:
        """Format speaker segments into a readable conversation format"""
        if not speakers:
            return "No transcription data available."
        
        # Collect all segments with timing information
        all_segments = []
        for speaker, segments in speakers.items():
            for segment in segments:
                all_segments.append({
                    'speaker': speaker,
                    'start': float(segment.start),
                    'end': float(segment.end),
                    'text': str(segment.text).strip()
                })
        
        # Sort by start time
        all_segments.sort(key=lambda x: x['start'])
        
        # Format conversation
        conversation_lines = []
        for i, segment in enumerate(all_segments):
            # Format timestamp
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            
            # Format speaker and text
            speaker_name = segment['speaker']
            text = segment['text']
            
            # Add conversation line
            conversation_lines.append(f"[{start_time} - {end_time}] {speaker_name}: {text}")
            
            # Add separator between segments if there's a gap
            if i < len(all_segments) - 1:
                next_segment = all_segments[i + 1]
                gap = next_segment['start'] - segment['end']
                if gap > 2.0:  # Add separator for gaps longer than 2 seconds
                    conversation_lines.append("")
        
        return "\n".join(conversation_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def display_results(self, result: TranscriptionResult):
        """Display transcription results in a formatted way"""
        if not result.success:
            logger.error(f"Transcription failed: {result.error_message}")
            return
        
        logger.info("Speaker-separated transcription completed successfully")
        logger.info(f"Transcription time: {result.transcription_time:.2f} seconds")
        logger.info(f"Detected speakers: {result.speaker_count}")
        logger.info(f"Model used: {result.model_name}")
        
        # Log speaker information
        for speaker, segments in result.speakers.items():
            logger.info(f"Speaker {speaker}: {len(segments)} segments")
        
        logger.info(f"Full transcription length: {len(result.full_text)} characters")
    
    def get_available_engines(self) -> list:
        """Get list of available transcription engines"""
        return TranscriptionEngineFactory.get_available_engines(self.config) 