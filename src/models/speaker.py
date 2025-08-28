#!/usr/bin/env python3
"""
Speaker diarization configuration model
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SpeakerConfig(BaseModel):
    """Speaker diarization configuration"""
    
    enabled: bool = Field(default=True, description="Enable speaker diarization")
    min_speakers: int = Field(default=1, ge=1, le=10, description="Minimum number of speakers")
    max_speakers: int = Field(default=4, ge=1, le=20, description="Maximum number of speakers")
    silence_threshold: float = Field(default=2.0, ge=0.1, le=10.0, description="Silence threshold in seconds")
    vad_enabled: bool = Field(default=True, description="Enable Voice Activity Detection")
    word_timestamps: bool = Field(default=True, description="Enable word-level timestamps")
    language: str = Field(default="he", description="Language code for diarization")
    beam_size: int = Field(default=5, ge=1, le=10, description="Beam size for beam search")
    vad_min_silence_duration_ms: int = Field(default=500, ge=0, description="Minimum silence duration in milliseconds")
    presets: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "default": {
                "min_speakers": 1,
                "max_speakers": 2,
                "silence_threshold": 2.0
            },
            "conversation": {
                "min_speakers": 2,
                "max_speakers": 4,
                "silence_threshold": 1.5
            },
            "interview": {
                "min_speakers": 2,
                "max_speakers": 3,
                "silence_threshold": 2.5
            }
        },
        description="Speaker diarization presets"
    )
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid" 