"""
Parameter provider implementations
"""

from typing import Optional, Dict
from src.models import AppConfig


class TranscriptionParameterProvider:
    """Provider for transcription parameters with defaults"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def get_parameters(self, model: Optional[str] = None, engine: Optional[str] = None) -> Dict[str, str]:
        """Get transcription parameters with defaults"""
        if self.config.transcription:
            default_model = self.config.transcription.default_model
            default_engine = self.config.transcription.default_engine
        else:
            # Set defaults
            default_model = "large-v3"
            default_engine = "speaker-diarization"
        
        return {
            'model': model or default_model,
            'engine': engine or default_engine
        } 