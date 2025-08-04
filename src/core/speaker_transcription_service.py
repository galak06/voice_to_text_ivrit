#!/usr/bin/env python3
"""
Speaker Transcription Service for ivrit-ai models
Handles speaker diarization with configurable parameters
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
try:
    from faster_whisper import WhisperModel
    import torch
    import torchaudio
    import numpy as np
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

@dataclass
class SpeakerConfig:
    """Configuration for speaker diarization"""
    min_speakers: int = 2
    max_speakers: int = 4
    silence_threshold: float = 2.0  # seconds
    vad_enabled: bool = True
    word_timestamps: bool = True
    language: str = "he"
    beam_size: int = 5
    vad_min_silence_duration_ms: int = 500

@dataclass
class TranscriptionResult:
    """Result of speaker transcription"""
    success: bool
    speakers: Dict[str, List[Dict[str, Any]]]
    full_text: str
    transcription_time: float
    model_name: str
    audio_file: str
    speaker_count: int
    error_message: Optional[str] = None

class SpeakerTranscriptionService:
    """
    Service for transcribing audio with speaker diarization
    Uses Strategy Pattern for different transcription engines
    """
    
    def __init__(self, config: Optional[SpeakerConfig] = None):
        """
        Initialize the speaker transcription service
        
        Args:
            config: Speaker configuration (uses defaults if None)
        """
        from src.utils.config_manager import config as app_config
        
        self.config = config or SpeakerConfig()
        self.app_config = app_config
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the service"""
        import logging
        logger = logging.getLogger('ivrit-ai-speaker')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def speaker_diarization(
        self, 
        audio_file_path: str, 
        model_name: str = None,
        save_output: bool = True,
        run_session_id: str = None
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
        start_time = time.time()
        self.logger.info(f"[PROGRESS] Starting diarization for: {audio_file_path}")
        
        # Validate input
        if not self._validate_audio_file(audio_file_path):
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0,
                model_name=model_name or "unknown",
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="Invalid audio file"
            )
        
        # Use default model if not provided
        if not model_name:
            model_name = self.app_config.transcription.default_model
        
        # Sanitize model name for file paths (replace slashes with underscores)
        model_name_safe = model_name.replace('/', '_').replace('\\', '_')
        
        self.logger.info(f"Starting speaker transcription: {audio_file_path}")
        self.logger.info(f"Model: {model_name}")
        self.logger.info(f"Config: min_speakers={self.config.min_speakers}, max_speakers={self.config.max_speakers}")
        
        try:
            # Try stable-whisper first for better speaker diarization
            result = self._transcribe_with_stable_whisper(audio_file_path, model_name)
            
            if result.success:
                self.logger.info("[PROGRESS] stable-whisper diarization completed successfully.")
            else:
                self.logger.warning("[PROGRESS] stable-whisper failed, falling back to faster-whisper")
                result = self._transcribe_with_faster_whisper(audio_file_path, model_name)
            
            # Save outputs if requested
            if save_output and result.success:
                self._save_outputs(result, audio_file_path, model_name_safe, run_session_id)
            
            # Calculate transcription time
            transcription_time = time.time() - start_time
            result.transcription_time = transcription_time
            
            self.logger.info(f"Transcription completed in {transcription_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )
    
    def _validate_audio_file(self, audio_file_path: str) -> bool:
        """Validate audio file exists and is accessible"""
        if not Path(audio_file_path).exists():
            self.logger.error(f"Audio file not found: {audio_file_path}")
            return False
        
        file_size = Path(audio_file_path).stat().st_size
        self.logger.info(f"Audio file: {audio_file_path} ({file_size:,} bytes)")
        return True
    
    def _transcribe_with_stable_whisper(
        self, 
        audio_file_path: str, 
        model_name: str
    ) -> TranscriptionResult:
        """Transcribe using stable-whisper with speaker diarization"""
        try:
            import stable_whisper
            
            # Check if model name is compatible with stable-whisper
            # stable-whisper only supports standard Whisper model names
            compatible_models = ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 
                               'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 
                               'large-v3-turbo', 'turbo']
            
            # If model name is not compatible, use a fallback
            if model_name not in compatible_models:
                self.logger.warning(f"Model {model_name} not compatible with stable-whisper, using 'large-v3' as fallback")
                model_name = 'large-v3'
            
            # Load stable-whisper model
            model = stable_whisper.load_model(model_name)
            
            # Transcribe with speaker diarization
            result = model.transcribe(
                audio_file_path,
                language=self.config.language,
                vad=self.config.vad_enabled,
                word_timestamps=self.config.word_timestamps,
                min_speakers=self.config.min_speakers,
                max_speakers=self.config.max_speakers
            )
            
            # Process results
            speakers = {}
            full_text = ""
            
            for idx, segment in enumerate(result.segments):
                if idx % 10 == 0:
                    self.logger.info(f"[PROGRESS] stable-whisper processed {idx+1} segments...")
                speaker = segment.speaker if hasattr(segment, 'speaker') else 'Unknown'
                if speaker not in speakers:
                    speakers[speaker] = []
                
                segment_data = {
                    'text': segment.text.strip(),
                    'start': segment.start,
                    'end': segment.end,
                    'words': segment.words if hasattr(segment, 'words') else None
                }
                
                speakers[speaker].append(segment_data)
                full_text += f"\n🎤 {speaker}:\n{segment.text.strip()}\n"
            self.logger.info(f"[PROGRESS] stable-whisper finished all {len(result.segments)} segments.")
            
            return TranscriptionResult(
                success=True,
                speakers=speakers,
                full_text=full_text.strip(),
                transcription_time=0,  # Will be set by caller
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(speakers)
            )
            
        except ImportError:
            self.logger.warning("stable-whisper not available")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="stable-whisper not available"
            )
        except Exception as e:
            self.logger.error(f"stable-whisper error: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )
    
    def _transcribe_with_faster_whisper(
        self, 
        audio_file_path: str, 
        model_name: str
    ) -> TranscriptionResult:
        """Transcribe using faster-whisper with basic speaker detection"""
        try:
            # Import here to ensure it's available
            from faster_whisper import WhisperModel
            
            # Try to load the model, with fallback to a standard model if needed
            try:
                model = WhisperModel(model_name, device="cpu", compute_type="int8")
            except Exception as model_error:
                self.logger.warning(f"Failed to load model {model_name}: {model_error}")
                self.logger.info("Falling back to 'large-v3' model")
                model = WhisperModel("large-v3", device="cpu", compute_type="int8")
                model_name = "large-v3"  # Update model name for output
            
            # Transcribe
            segments, info = model.transcribe(
                audio_file_path,
                beam_size=self.config.beam_size,
                language=self.config.language,
                vad_filter=self.config.vad_enabled,
                vad_parameters=dict(min_silence_duration_ms=self.config.vad_min_silence_duration_ms),
                word_timestamps=self.config.word_timestamps
            )
            self.logger.info(f"[PROGRESS] faster-whisper started segment processing...")
            # Simple speaker detection based on silence gaps
            speakers = {'Speaker 1': []}
            current_speaker = 'Speaker 1'
            speaker_count = 1
            
            for idx, segment in enumerate(segments):
                if idx % 10 == 0:
                    self.logger.info(f"[PROGRESS] faster-whisper processed {idx+1} segments...")
                # Simple heuristic: if gap > silence_threshold seconds, switch speaker
                if (speakers[current_speaker] and 
                    segment.start - speakers[current_speaker][-1]['end'] > self.config.silence_threshold):
                    if speaker_count < self.config.max_speakers:
                        speaker_count += 1
                        current_speaker = f'Speaker {speaker_count}'
                        if current_speaker not in speakers:
                            speakers[current_speaker] = []
                    else:
                        # Recycle speakers in round-robin fashion
                        speaker_keys = list(speakers.keys())
                        idx2 = speaker_keys.index(current_speaker)
                        current_speaker = speaker_keys[(idx2 + 1) % len(speaker_keys)]
                
                segment_data = {
                    'text': segment.text.strip(),
                    'start': segment.start,
                    'end': segment.end,
                    'words': segment.words if hasattr(segment, 'words') else None
                }
                speakers[current_speaker].append(segment_data)
            self.logger.info(f"[PROGRESS] faster-whisper finished all {len(list(segments))} segments.")
            
            # Build full text
            full_text = ""
            for speaker, segments in speakers.items():
                speaker_text = " ".join([seg['text'] for seg in segments])
                full_text += f"\n🎤 {speaker}:\n{speaker_text}\n"
            
            return TranscriptionResult(
                success=True,
                speakers=speakers,
                full_text=full_text.strip(),
                transcription_time=0,  # Will be set by caller
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(speakers)
            )
            
        except Exception as e:
            self.logger.error(f"faster-whisper error: {e}")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message=str(e)
            )
    
    def _save_outputs(
        self, 
        result: TranscriptionResult, 
        audio_file_path: str, 
        model_name: str,
        run_session_id: str = None
    ):
        """Save transcription outputs in all formats"""
        try:
            from src.utils.output_manager import OutputManager
            
            output_manager = OutputManager(run_session_id=run_session_id)
            
            # Prepare data for output manager with proper sanitization
            transcription_data = []
            for speaker, segments in result.speakers.items():
                for segment in segments:
                    # Sanitize words data to ensure JSON serialization
                    words_data = []
                    if segment.get('words'):
                        for word in segment['words']:
                            if isinstance(word, dict):
                                # Convert word dict to serializable format
                                sanitized_word = {}
                                for key, value in word.items():
                                    if isinstance(value, (str, int, float, bool, type(None))):
                                        sanitized_word[key] = value
                                    else:
                                        sanitized_word[key] = str(value)
                                words_data.append(sanitized_word)
                            else:
                                # If word is not a dict, convert to string
                                words_data.append(str(word))
                    
                    transcription_data.append({
                        'id': len(transcription_data),
                        'start': float(segment['start']) if 'start' in segment else 0.0,
                        'end': float(segment['end']) if 'end' in segment else 0.0,
                        'text': str(segment['text']) if 'text' in segment else '',
                        'speaker': str(speaker),
                        'words': words_data
                    })
            
            # Save as JSON
            json_file = output_manager.save_transcription(
                audio_file_path, transcription_data, model_name, "speaker-diarization"
            )
            
            # Format conversation text
            conversation_text = self._format_conversation_text(result.speakers)
            
            # Save as text
            text_file = output_manager.save_transcription_text(
                audio_file_path, conversation_text, model_name, "speaker-diarization"
            )
            
            # Save as Word document
            docx_file = output_manager.save_transcription_docx(
                audio_file_path, transcription_data, model_name, "speaker-diarization"
            )
            
            self.logger.info(f"All formats saved:")
            self.logger.info(f"  📄 JSON: {json_file}")
            self.logger.info(f"  📄 Text: {text_file}")
            if docx_file:
                self.logger.info(f"  📄 Word: {docx_file}")
            else:
                self.logger.info(f"  📄 Word: Skipped (python-docx not available)")
                
        except Exception as e:
            self.logger.error(f"Failed to save outputs: {e}")
            # Log more details about the error
            import traceback
            self.logger.error(f"Error details: {traceback.format_exc()}")
    
    def _format_conversation_text(self, speakers: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format speaker segments into a readable conversation format"""
        if not speakers:
            return "No transcription data available."
        
        # Collect all segments with timing information
        all_segments = []
        for speaker, segments in speakers.items():
            for segment in segments:
                all_segments.append({
                    'speaker': speaker,
                    'start': float(segment.get('start', 0)),
                    'end': float(segment.get('end', 0)),
                    'text': str(segment.get('text', '')).strip()
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
            self.logger.error(f"Transcription failed: {result.error_message}")
            return
        
        self.logger.info("Speaker-separated transcription completed successfully")
        self.logger.info(f"Transcription time: {result.transcription_time:.2f} seconds")
        self.logger.info(f"Detected speakers: {result.speaker_count}")
        self.logger.info(f"Model used: {result.model_name}")
        
        # Log speaker information
        for speaker, segments in result.speakers.items():
            self.logger.info(f"Speaker {speaker}: {len(segments)} segments")
        
        self.logger.info(f"Full transcription length: {len(result.full_text)} characters") 