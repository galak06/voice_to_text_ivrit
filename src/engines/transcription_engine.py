#!/usr/bin/env python3
"""
Transcription engine implementations
Defines concrete implementations for transcription engines
"""

from typing import Any
import torch
from .interfaces import TranscriptionEngineInterface

device = 'cuda' if torch.cuda.is_available() else 'cpu'

class FasterWhisperEngine:
    """Faster Whisper transcription engine implementation"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
    
    def transcribe(self, audio_file: str, language: str = 'he', word_timestamps: bool = True) -> Any:
        """Transcribe using faster-whisper"""
        if self.model is None:
            import faster_whisper
            self.model = faster_whisper.WhisperModel(
                self.model_name, device=device, compute_type='float32', local_files_only=True
            )
        
        return self.model.transcribe(audio_file, language=language, word_timestamps=word_timestamps)

class StableWhisperEngine:
    """Stable Whisper transcription engine implementation"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
    
    def transcribe(self, audio_file: str, language: str = 'he', word_timestamps: bool = True) -> Any:
        """Transcribe using stable-whisper"""
        if self.model is None:
            import stable_whisper
            self.model = stable_whisper.load_faster_whisper(
                self.model_name, device=device, compute_type='float32', local_files_only=True
            )
        
        result = self.model.transcribe(audio_file, language=language, word_timestamps=word_timestamps)
        return result 