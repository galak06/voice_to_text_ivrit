#!/usr/bin/env python3
"""
Application configuration model
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .environment import Environment
from .transcription import TranscriptionConfig
from .speaker import SpeakerConfig
from .batch import BatchConfig
from .docker import DockerConfig
from .runpod import RunPodConfig
from .output import OutputConfig
from .system import SystemConfig
from .input import InputConfig
from .chunking import ChunkingConfig
from .processing import ProcessingConfig
from .ctranslate2 import CTranslate2Config


class AppConfig(BaseModel):
    """Complete application configuration"""
    
    environment: Environment = Field(default=Environment.BASE, description="Application environment")
    transcription: Optional[TranscriptionConfig] = Field(default_factory=TranscriptionConfig, description="Transcription configuration")
    speaker: Optional[SpeakerConfig] = Field(default_factory=SpeakerConfig, description="Speaker diarization configuration")
    batch: Optional[BatchConfig] = Field(default_factory=BatchConfig, description="Batch processing configuration")
    docker: Optional[DockerConfig] = Field(default_factory=DockerConfig, description="Docker configuration")
    runpod: Optional[RunPodConfig] = Field(default_factory=RunPodConfig, description="RunPod configuration")
    output: Optional[OutputConfig] = Field(default_factory=OutputConfig, description="Output configuration")
    system: Optional[SystemConfig] = Field(default_factory=SystemConfig, description="System configuration")
    input: Optional[InputConfig] = Field(default_factory=InputConfig, description="Input configuration")
    chunking: Optional[ChunkingConfig] = Field(default_factory=ChunkingConfig, description="Chunking configuration")
    processing: Optional[ProcessingConfig] = Field(default_factory=ProcessingConfig, description="Processing configuration")
    ctranslate2_specific: Optional[CTranslate2Config] = Field(default_factory=CTranslate2Config, description="CTranslate2 specific configuration")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 