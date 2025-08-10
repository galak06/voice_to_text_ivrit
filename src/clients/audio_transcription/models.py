"""
Pydantic models for audio transcription
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


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