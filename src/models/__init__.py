#!/usr/bin/env python3
"""
Configuration Models Package
Pydantic models for configuration management
"""

from .environment import Environment
from .transcription import TranscriptionConfig, TranscriptionRequest
from .batch import BatchConfig
from .docker import DockerConfig
from .runpod import RunPodConfig
from .output import OutputConfig
from .system import SystemConfig
from .input import InputConfig
from .chunking import ChunkingConfig
from .processing import ProcessingConfig
from .app_config import AppConfig
from .input_validation import (
    InputType,
    TranscriptionEngine,
    AudioFileValidation,
    JobInputValidation,
    InputValidationRequest,
    BatchInputValidation
)
# Merged transcription results (includes speaker models)
from .transcription_results import (
    TranscriptionResult,
    TranscriptionSegment,
    WordTimestamp,
    CTranslate2GenerationResult,
    TranscriptionMetadata,
    BatchTranscriptionResult,
    TranscriptionError,
    SpeakerConfig,
    SpeakerDiarizationRequest
)

__all__ = [
    'Environment',
    'TranscriptionConfig',
    'TranscriptionRequest',
    'TranscriptionResult',
    'TranscriptionSegment',
    'WordTimestamp',
    'CTranslate2GenerationResult',
    'TranscriptionMetadata',
    'BatchTranscriptionResult',
    'TranscriptionError',
    'SpeakerConfig',
    'SpeakerDiarizationRequest',
    'BatchConfig',
    'DockerConfig',
    'RunPodConfig',
    'OutputConfig',
    'SystemConfig',
    'InputConfig',
    'ChunkingConfig',
    'ProcessingConfig',
    'AppConfig',
    'InputType',
    'TranscriptionEngine',
    'AudioFileValidation',
    'JobInputValidation',
    'InputValidationRequest',
    'BatchInputValidation'
] 