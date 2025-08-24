#!/usr/bin/env python3
"""
Transcription configuration model
"""

from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, BaseModel
from enum import Enum

from .base_models import BaseConfigModel


class TranscriptionModel(str, Enum):
    """Available transcription models"""
    IVRIT_LARGE_V3 = "ivrit-ai/whisper-large-v3-ct2"


class TranscriptionEngine(str, Enum):
    """Available transcription engines"""
    FASTER_WHISPER = "faster-whisper"
    STABLE_WHISPER = "stable-whisper"
    SPEAKER_DIARIZATION = "speaker-diarization"
    CUSTOM_WHISPER = "custom-whisper"
    CTRANSLATE2_WHISPER = "ctranslate2-whisper"


class TranscriptionRequest(BaseModel):
    """Pydantic model for transcription request parameters"""
    audio_file_path: str
    model: str
    engine: str
    streaming_enabled: bool = False


class TranscriptionResult(BaseModel):
    """Pydantic model for transcription results"""
    success: bool
    segments: List[Dict[str, Any]]
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class TranscriptionConfig(BaseConfigModel):
    """Transcription engine configuration with improved validation"""
    
    # Model configuration
    default_model: TranscriptionModel = Field(
        default=TranscriptionModel.IVRIT_LARGE_V3, 
        description="Default model to use for transcription"
    )
    fallback_model: TranscriptionModel = Field(
        default=TranscriptionModel.IVRIT_LARGE_V3, 
        description="Fallback model if default fails"
    )
    
    # Engine configuration
    default_engine: TranscriptionEngine = Field(
        default=TranscriptionEngine.SPEAKER_DIARIZATION, 
        description="Default transcription engine"
    )
    
    # Processing parameters
    beam_size: int = Field(
        default=5, 
        ge=1, 
        le=10, 
        description="Beam size for beam search"
    )
    language: str = Field(
        default="he", 
        description="Language code for transcription"
    )
    word_timestamps: bool = Field(
        default=True, 
        description="Enable word-level timestamps"
    )
    
    # Voice Activity Detection
    vad_enabled: bool = Field(
        default=True, 
        description="Enable Voice Activity Detection"
    )
    vad_min_silence_duration_ms: int = Field(
        default=500, 
        ge=0, 
        description="Minimum silence duration in milliseconds"
    )
    
    # Available options (computed properties)
    @property
    def available_models(self) -> List[str]:
        """Get list of available transcription models"""
        return [model.value for model in TranscriptionModel]
    
    @property
    def available_engines(self) -> List[str]:
        """Get list of available transcription engines"""
        return [engine.value for engine in TranscriptionEngine]
    
    # Validation methods
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code format"""
        if not v or len(v) != 2:
            raise ValueError("Language code must be a 2-character ISO code")
        return v.lower()
    
    @field_validator('beam_size')
    @classmethod
    def validate_beam_size(cls, v: int) -> int:
        """Validate beam size is reasonable"""
        if v < 1 or v > 10:
            raise ValueError("Beam size must be between 1 and 10")
        return v
    
    def get_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        model = model_name or self.default_model.value
        return {
            'model': model,
            'engine': self.default_engine.value,
            'language': self.language,
            'word_timestamps': self.word_timestamps,
            'beam_size': self.beam_size,
            'vad_enabled': self.vad_enabled,
            'vad_min_silence_duration_ms': self.vad_min_silence_duration_ms
        }
    
    def validate_model_engine_combination(self, model: str, engine: str) -> bool:
        """Validate if model and engine combination is supported"""
        try:
            TranscriptionModel(model)
            TranscriptionEngine(engine)
            return True
        except ValueError:
            return False 