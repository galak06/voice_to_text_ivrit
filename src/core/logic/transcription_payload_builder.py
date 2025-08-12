"""
Transcription payload builder implementations
"""

import base64
from typing import Dict, Any
from src.models import TranscriptionRequest


class TranscriptionPayloadBuilder:
    """Default implementation of transcription payload builder"""
    
    def build(self, request: TranscriptionRequest) -> Dict[str, Any]:
        """Build payload for transcription request"""
        with open(request.audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "input": {
                "type": "blob",
                "data": audio_data_b64,
                "model": request.model,
                "engine": request.engine,
                "streaming": request.streaming_enabled
            }
        }
