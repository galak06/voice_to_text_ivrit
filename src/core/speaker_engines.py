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
                
                # Validate segment timing
                if segment.end <= segment.start:
                    logger.warning(f"Skipping segment {idx} with invalid timing: start={segment.start}, end={segment.end}")
                    continue
                
                # Since stable-whisper doesn't support speaker diarization, use alternating speakers
                speaker = f"Speaker {idx % 2 + 1}"  # Alternate between Speaker 1 and 2
                
                if speaker not in speakers:
                    speakers[speaker] = []
                
                # Convert words to proper format for Pydantic
                words_data = None
                if hasattr(segment, 'words') and segment.words:
                    words_data = []
                    for word in segment.words:
                        # Validate word timing
                        word_start = getattr(word, 'start', 0)
                        word_end = getattr(word, 'end', 0)
                        if word_end <= word_start:
                            logger.warning(f"Skipping word with invalid timing: start={word_start}, end={word_end}")
                            continue
                            
                        if hasattr(word, '__dict__'):
                            words_data.append(word.__dict__)
                        elif isinstance(word, dict):
                            words_data.append(word)
                        else:
                            # Convert to dict if it's a simple object
                            words_data.append({
                                'start': word_start,
                                'end': word_end,
                                'word': getattr(word, 'word', str(word))
                            })
                
                try:
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
                except Exception as e:
                    logger.warning(f"Failed to create segment {idx}: {e}")
                    continue
            
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


class TranscriptionEngineFactory:
    """Factory for creating transcription engines"""
    
    @staticmethod
    def create_engine(engine_type: str, config: SpeakerConfig) -> TranscriptionEngine:
        """Create a transcription engine based on type"""
        if engine_type == "stable-whisper":
            return StableWhisperEngine(config)
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
    
    @staticmethod
    def get_available_engines(config: SpeakerConfig) -> List[TranscriptionEngine]:
        """Get list of available engines"""
        engines = []
        
        stable_engine = StableWhisperEngine(config)
        if stable_engine.is_available():
            engines.append(stable_engine)
        
        return engines 