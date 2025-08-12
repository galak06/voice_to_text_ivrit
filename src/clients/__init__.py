#!/usr/bin/env python3
"""
Clients package
"""

from .audio_transcription_client import AudioTranscriptionClient
from .infer_client import transcribe

__all__ = [
    'AudioTranscriptionClient',
    'transcribe'
] 