"""
Transcription parameter provider implementations
"""

from typing import Dict, Any
from src.models import AppConfig


class TranscriptionParameterProvider:
    """Provider for transcription parameters"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def get_parameters(self, model: str = None, engine: str = None) -> Dict[str, Any]:
        """Get transcription parameters from configuration"""
        params = {}
        
        # Get model parameters
        if model:
            params['model'] = model
        elif hasattr(self.config, 'transcription') and self.config.transcription:
            params['model'] = getattr(self.config.transcription, 'default_model', 'whisper-large-v3')
        
        # Get engine parameters
        if engine:
            params['engine'] = engine
        elif hasattr(self.config, 'transcription') and self.config.transcription:
            params['engine'] = getattr(self.config.transcription, 'default_engine', 'speaker-diarization')
        
        # Get streaming configuration
        if hasattr(self.config, 'transcription') and self.config.transcription:
            params['streaming'] = getattr(self.config.transcription, 'streaming_enabled', False)
        
        return params
