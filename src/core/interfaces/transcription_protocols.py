#!/usr/bin/env python3
"""
Transcription service protocols and interfaces
Defines contracts for different behaviors
"""

from typing import Dict, Any, Generator, Protocol
from src.models import TranscriptionResult


class TranscriptionServiceProtocol(Protocol):
    """Protocol for transcription services"""
    def transcribe(self, input_data: Dict[str, Any], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """Process transcription request"""
        ...


class SpeakerServiceProtocol(Protocol):
    """Protocol for speaker diarization services"""
    def speaker_diarization(self, audio_file_path: str, **kwargs) -> TranscriptionResult:
        """Perform speaker diarization"""
        ...


class ProgressMonitorProtocol(Protocol):
    """Protocol for progress monitoring"""
    def start_monitoring(self, file_path: str) -> None:
        """Start monitoring a file"""
        ...
    
    def stop(self) -> None:
        """Stop monitoring"""
        ...
