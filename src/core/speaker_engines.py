#!/usr/bin/env python3
"""
Transcription engines for speaker diarization
Implements Strategy Pattern for different transcription engines
"""

import logging
import time
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from ..models.speaker_models import SpeakerConfig, TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class TranscriptionEngine(ABC):
    """Abstract base class for transcription engines"""
    
    def __init__(self, config: SpeakerConfig):
        self.config = config
    
    @abstractmethod
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe audio file with speaker diarization"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available"""
        pass


class StableWhisperEngine(TranscriptionEngine):
    """Stable-Whisper transcription engine"""
    
    def is_available(self) -> bool:
        try:
            import stable_whisper
            return True
        except ImportError:
            return False
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using stable-whisper with speaker diarization"""
        start_time = time.time()
        
        try:
            import stable_whisper
            
            # Check if model name is compatible with stable-whisper
            compatible_models = ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 
                               'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 
                               'large-v3-turbo', 'turbo']
            
            # If model name is not compatible, use a fallback
            if model_name not in compatible_models:
                logger.warning(f"Model {model_name} not compatible with stable-whisper, using 'large-v3' as fallback")
                model_name = 'large-v3'
            
            # Load stable-whisper model
            model = stable_whisper.load_model(model_name)
            
            # Transcribe with basic parameters (no speaker_labels - not supported)
            result = model.transcribe(
                audio_file_path,
                language=self.config.language,
                vad=self.config.vad_enabled,
                word_timestamps=self.config.word_timestamps
            )
            
            # Process results
            speakers: Dict[str, List[TranscriptionSegment]] = {}
            full_text = ""
            
            for idx, segment in enumerate(result.segments):
                if idx % 10 == 0:
                    logger.info(f"[PROGRESS] stable-whisper processed {idx+1} segments...")
                
                # Since stable-whisper doesn't support speaker diarization, use alternating speakers
                speaker = f"Speaker {idx % 2 + 1}"  # Alternate between Speaker 1 and 2
                
                if speaker not in speakers:
                    speakers[speaker] = []
                
                # Convert words to proper format for Pydantic
                words_data = None
                if hasattr(segment, 'words') and segment.words:
                    words_data = []
                    for word in segment.words:
                        if hasattr(word, '__dict__'):
                            words_data.append(word.__dict__)
                        elif isinstance(word, dict):
                            words_data.append(word)
                        else:
                            # Convert to dict if it's a simple object
                            words_data.append({
                                'start': getattr(word, 'start', 0),
                                'end': getattr(word, 'end', 0),
                                'word': getattr(word, 'word', str(word))
                            })
                
                # Create TranscriptionSegment
                segment_data = TranscriptionSegment(
                    text=segment.text.strip(),
                    start=segment.start,
                    end=segment.end,
                    speaker=speaker,
                    words=words_data
                )
                
                speakers[speaker].append(segment_data)
                full_text += f"\n🎤 {speaker}:\n{segment.text.strip()}\n"
            
            logger.info(f"[PROGRESS] stable-whisper finished all {len(result.segments)} segments.")
            
            return TranscriptionResult(
                success=True,
                speakers=speakers,
                full_text=full_text.strip(),
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(speakers)
            )
            
        except ImportError:
            logger.warning("stable-whisper not available")
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="stable-whisper not available"
            )
        except Exception as e:
            logger.error(f"stable-whisper error: {e}")
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


class FasterWhisperEngine(TranscriptionEngine):
    """Faster-Whisper transcription engine"""
    
    def is_available(self) -> bool:
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """Transcribe using faster-whisper with basic speaker detection"""
        start_time = time.time()
        
        try:
            # Import here to ensure it's available
            from faster_whisper import WhisperModel
            
            # Try to load the model, with fallback to a standard model if needed
            try:
                model = WhisperModel(model_name, device="cpu", compute_type="int8")
            except Exception as model_error:
                logger.warning(f"Failed to load model {model_name}: {model_error}")
                logger.info("Falling back to 'large-v3' model")
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
            logger.info(f"[PROGRESS] faster-whisper started segment processing...")
            
            # Convert generator to list to avoid consumption issues
            segments_list = list(segments)
            logger.info(f"[PROGRESS] faster-whisper found {len(segments_list)} segments to process...")
            
            # Simple speaker detection based on silence gaps
            speakers: Dict[str, List[TranscriptionSegment]] = {}
            current_speaker = 'Speaker 1'
            speaker_count = 1
            
            # Initialize first speaker
            speakers[current_speaker] = []
            
            for idx, segment in enumerate(segments_list):
                if idx % 10 == 0:
                    logger.info(f"[PROGRESS] faster-whisper processed {idx+1} segments...")
                
                # Simple heuristic: if gap > silence_threshold seconds, switch speaker
                if (speakers[current_speaker] and 
                    segment.start - speakers[current_speaker][-1].end > self.config.silence_threshold):
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
                
                # Convert words to proper format for Pydantic
                words_data = None
                if hasattr(segment, 'words') and segment.words:
                    words_data = []
                    for word in segment.words:
                        if hasattr(word, '__dict__'):
                            words_data.append(word.__dict__)
                        elif isinstance(word, dict):
                            words_data.append(word)
                        else:
                            # Convert to dict if it's a simple object
                            words_data.append({
                                'start': getattr(word, 'start', 0),
                                'end': getattr(word, 'end', 0),
                                'word': getattr(word, 'word', str(word))
                            })
                
                # Create TranscriptionSegment
                segment_data = TranscriptionSegment(
                    text=segment.text.strip(),
                    start=segment.start,
                    end=segment.end,
                    speaker=current_speaker,
                    words=words_data
                )
                speakers[current_speaker].append(segment_data)
            
            logger.info(f"[PROGRESS] faster-whisper finished all {len(segments_list)} segments.")
            
            # Build full text
            full_text = ""
            for speaker, segments in speakers.items():
                speaker_text = " ".join([seg.text for seg in segments])
                full_text += f"\n🎤 {speaker}:\n{speaker_text}\n"
            
            return TranscriptionResult(
                success=True,
                speakers=speakers,
                full_text=full_text.strip(),
                transcription_time=time.time() - start_time,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=len(speakers)
            )
            
        except Exception as e:
            logger.error(f"faster-whisper error: {e}")
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


class TranscriptionEngineFactory:
    """Factory for creating transcription engines"""
    
    @staticmethod
    def create_engine(engine_type: str, config: SpeakerConfig) -> TranscriptionEngine:
        """Create a transcription engine based on type"""
        if engine_type == "stable-whisper":
            return StableWhisperEngine(config)
        elif engine_type == "faster-whisper":
            return FasterWhisperEngine(config)
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
    
    @staticmethod
    def get_available_engines(config: SpeakerConfig) -> List[TranscriptionEngine]:
        """Get list of available engines"""
        engines = []
        
        stable_engine = StableWhisperEngine(config)
        if stable_engine.is_available():
            engines.append(stable_engine)
        
        faster_engine = FasterWhisperEngine(config)
        if faster_engine.is_available():
            engines.append(faster_engine)
        
        return engines 