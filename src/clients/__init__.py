#!/usr/bin/env python3
"""
Client implementations
Contains client code for different services
"""

from .send_audio import send_audio_file
from .infer_client import transcribe

__all__ = ['send_audio_file', 'transcribe'] 