#!/usr/bin/env python3
"""
Audio transcription client for RunPod endpoint
Backward compatibility module - imports from new modular structure
"""

# Import everything from the new modular structure
from .audio_transcription import (
    AudioTranscriptionClient,
    TranscriptionRequest,
    TranscriptionResult,
    AudioFileValidator,
    TranscriptionPayloadBuilder,
    TranscriptionResultCollector,
    OutputSaver,
    ResultDisplay,
    RunPodEndpoint,
    RunPodEndpointFactory,
    DefaultAudioFileValidator,
    DefaultTranscriptionPayloadBuilder,
    DefaultTranscriptionResultCollector,
    DefaultOutputSaver,
    DefaultResultDisplay,
    TranscriptionParameterProvider,
    QueueWaiter,
    DefaultRunPodEndpointFactory
)

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





 