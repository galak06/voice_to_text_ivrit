#!/usr/bin/env python3
"""
Pydantic models for speaker transcription service
Provides data validation and serialization for speaker diarization
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pathlib import Path


class SpeakerConfig(BaseModel):
    """Configuration for speaker diarization with validation"""
    
    min_speakers: int = Field(default=2, ge=1, le=10, description="Minimum number of speakers")
    max_speakers: int = Field(default=4, ge=1, le=10, description="Maximum number of speakers")
    strict_two_speakers: bool = Field(default=True, description="Force exactly 2 speakers regardless of detection")
    silence_threshold: float = Field(default=1.5, ge=0.1, le=10.0, description="Silence threshold in seconds")
    min_speaker_duration: float = Field(default=0.5, ge=0.1, le=10.0, description="Minimum duration for a speaker segment in seconds")
    min_segment_duration: float = Field(default=2.0, ge=0.5, le=10.0, description="Minimum duration for merged segments in seconds")
    speaker_similarity_threshold: float = Field(default=0.7, ge=0.1, le=1.0, description="Threshold for speaker similarity")
    vad_enabled: bool = Field(default=True, description="Enable Voice Activity Detection")
    word_timestamps: bool = Field(default=True, description="Include word-level timestamps")
    language: str = Field(default="he", min_length=2, max_length=5, description="Language code")
    beam_size: int = Field(default=5, ge=1, le=20, description="Beam size for transcription")
    vad_min_silence_duration_ms: int = Field(default=300, ge=100, le=5000, description="Minimum silence duration in ms")
    
    @field_validator('max_speakers')
    @classmethod
    def max_speakers_must_be_greater_than_min(cls, v: int, info) -> int:
        if 'min_speakers' in info.data and v < info.data['min_speakers']:
            raise ValueError('max_speakers must be greater than or equal to min_speakers')
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        valid_languages = ['he', 'en', 'ar', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        if v not in valid_languages:
            raise ValueError(f'Language must be one of: {valid_languages}')
        return v


class TranscriptionSegment(BaseModel):
    """Individual transcription segment with speaker information"""
    
    text: str = Field(..., description="Transcribed text content")
    start: float = Field(..., ge=0, description="Start time in seconds")
    end: float = Field(..., ge=0, description="End time in seconds")
    speaker: str = Field(..., description="Speaker identifier")
    words: Optional[List[Dict[str, Any]]] = Field(default=None, description="Word-level timestamps")
    confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Confidence score")
    chunk_file: Optional[str] = Field(default=None, description="Source audio chunk file name")
    chunk_number: Optional[int] = Field(default=None, description="Chunk number in sequence")
    
    @field_validator('end')
    @classmethod
    def end_must_be_after_start(cls, v: float, info) -> float:
        if 'start' in info.data and v <= info.data['start']:
            raise ValueError('end time must be after start time')
        return v
    
    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('text cannot be empty')
        return v.strip()


class TranscriptionResult(BaseModel):
    """Result of speaker transcription with validation"""
    
    success: bool = Field(..., description="Whether transcription was successful")
    speakers: Dict[str, List[TranscriptionSegment]] = Field(default_factory=dict, description="Speaker-separated segments")
    full_text: str = Field(default="", description="Complete transcription text")
    transcription_time: float = Field(..., ge=0, description="Time taken for transcription in seconds")
    model_name: str = Field(..., description="Name of the model used")
    audio_file: str = Field(..., description="Path to the audio file")
    speaker_count: int = Field(..., ge=0, description="Number of speakers detected")
    error_message: Optional[str] = Field(default=None, description="Error message if transcription failed")
    
    @field_validator('audio_file')
    @classmethod
    def validate_audio_file_exists(cls, v: str) -> str:
        if not Path(v).exists():
            raise ValueError(f'Audio file does not exist: {v}')
        return v
    
    @field_validator('speaker_count')
    @classmethod
    def validate_speaker_count(cls, v: int, info) -> int:
        if 'speakers' in info.data and v != len(info.data['speakers']):
            raise ValueError('speaker_count must match the number of speakers in the speakers dict')
        return v
    
    def get_speaker_names(self) -> List[str]:
        """Get list of speaker names"""
        return list(self.speakers.keys())
    
    def get_total_segments(self) -> int:
        """Get total number of segments across all speakers"""
        return sum(len(segments) for segments in self.speakers.values())
    
    def get_speaker_segment_count(self, speaker_name: str) -> int:
        """Get number of segments for a specific speaker"""
        return len(self.speakers.get(speaker_name, []))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return self.model_dump()
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"  # Prevent additional fields
    )


class SpeakerDiarizationRequest(BaseModel):
    """Request model for speaker diarization"""
    
    audio_file_path: str = Field(..., description="Path to the audio file")
    model_name: Optional[str] = Field(default=None, description="Model to use for transcription")
    save_output: bool = Field(default=True, description="Whether to save outputs")
    run_session_id: Optional[str] = Field(default=None, description="Session ID for tracking")
    speaker_config: Optional[SpeakerConfig] = Field(default=None, description="Speaker configuration")
    
    @field_validator('audio_file_path')
    @classmethod
    def validate_audio_file_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('audio_file_path cannot be empty')
        return v.strip()
    
    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('model_name cannot be empty if provided')
        return v.strip() if v else None 