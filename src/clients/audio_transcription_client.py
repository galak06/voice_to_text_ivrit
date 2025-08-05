#!/usr/bin/env python3
"""
Audio transcription client for RunPod endpoint
Backward compatibility module - imports from new modular structure
"""

# Import everything from the new modular structure
from .audio_transcription.models import TranscriptionRequest, TranscriptionResult
from .audio_transcription.protocols import (
    AudioFileValidator,
    TranscriptionPayloadBuilder,
    TranscriptionResultCollector,
    OutputSaver,
    ResultDisplay,
    RunPodEndpoint,
    RunPodEndpointFactory
)
from .audio_transcription.audio_file_validator import DefaultAudioFileValidator
from .audio_transcription.transcription_payload_builder import DefaultTranscriptionPayloadBuilder
from .audio_transcription.transcription_result_collector import DefaultTranscriptionResultCollector
from .audio_transcription.output_saver import DefaultOutputSaver
from .audio_transcription.result_display import DefaultResultDisplay
from .audio_transcription.transcription_parameter_provider import TranscriptionParameterProvider
from .audio_transcription.queue_waiter import QueueWaiter
from .audio_transcription.runpod_endpoint_factory import DefaultRunPodEndpointFactory
from .audio_transcription.audio_transcription_client import AudioTranscriptionClient

# Re-export for backward compatibility
__all__ = [
    'AudioTranscriptionClient',
    'TranscriptionRequest',
    'TranscriptionResult',
    'AudioFileValidator',
    'TranscriptionPayloadBuilder',
    'TranscriptionResultCollector',
    'OutputSaver',
    'ResultDisplay',
    'RunPodEndpoint',
    'RunPodEndpointFactory',
    'DefaultAudioFileValidator',
    'DefaultTranscriptionPayloadBuilder',
    'DefaultTranscriptionResultCollector',
    'DefaultOutputSaver',
    'DefaultResultDisplay',
    'TranscriptionParameterProvider',
    'QueueWaiter',
    'DefaultRunPodEndpointFactory'
]





 