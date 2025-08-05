#!/usr/bin/env python3
"""
Client implementations
Contains client code for different services
"""

from .audio_transcription_client import send_audio_file
from .infer_client import transcribe

__all__ = ['send_audio_file', 'transcribe'] 