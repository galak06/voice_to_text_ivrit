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
    
    # Additional fields from config file
    disable_completely: bool = Field(default=False, description="Completely disable speaker diarization")
    fast_processing: bool = Field(default=False, description="Enable fast processing with Silero VAD (much faster than Pyannote)")
    enhanced_processing: bool = Field(default=True, description="Enable enhanced processing")
    use_pyannote: bool = Field(default=True, description="Use Pyannote for speaker diarization")
    model: str = Field(default="pyannote/speaker-diarization@2.1", description="Speaker diarization model")
    min_speaker_duration: float = Field(default=0.5, ge=0.1, le=10.0, description="Minimum duration for a speaker segment")
    min_segment_duration: float = Field(default=1.0, ge=0.5, le=10.0, description="Minimum duration for merged segments")
    speaker_similarity_threshold: float = Field(default=0.7, ge=0.1, le=1.0, description="Threshold for speaker similarity")
    
    # Complex nested objects
    chunked_processing: Optional[Dict[str, Any]] = Field(default=None, description="Chunked processing configuration")
    disable_options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "disable_speaker_detection": False,
            "disable_speaker_labeling": False,
            "disable_speaker_segmentation": False,
            "use_single_speaker_mode": False
        },
        description="Disable options configuration"
    )
    strict_two_speakers: bool = Field(default=False, description="Strict two speakers mode")
    
    # Additional fields from production config
    min_speaker_duration: float = Field(default=0.5, ge=0.1, le=10.0, description="Minimum speaker duration in seconds")
    min_segment_duration: float = Field(default=2.0, ge=0.1, le=10.0, description="Minimum segment duration in seconds")
    speaker_similarity_threshold: float = Field(default=0.7, ge=0.1, le=1.0, description="Threshold for speaker similarity")
    
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
    
    # Conversation formatting configuration
    conversation_formatting: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "enabled": True,
            "time_gap_threshold": 3.0,
            "min_segment_duration": 0.5,
            "include_timing": True,
            "include_chunk_source": False,
            "paragraph_grouping": {
                "enabled": True,
                "max_gap_seconds": 2.0,
                "min_paragraph_duration": 1.0
            },
            "output_formats": {
                "txt": True,
                "json": True,
                "docx": False
            },
            "speaker_display": {
                "show_emojis": True,
                "show_timing": True,
                "show_duration": True
            }
        },
        description="Conversation formatting configuration"
    )
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid" 