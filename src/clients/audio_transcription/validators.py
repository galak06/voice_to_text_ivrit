"""
Audio file validation implementations
"""

from pathlib import Path
from typing import Dict, Any
from src.models import AppConfig


class DefaultAudioFileValidator:
    """Default implementation of audio file validator"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file and return file information"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        file_size = path.stat().st_size
        
        if self.config.runpod and self.config.runpod.max_payload_size:
            max_size = self.config.runpod.max_payload_size
            if file_size > max_size:
                raise ValueError(
                    f"File too large! Max size: {max_size:,} bytes, "
                    f"actual size: {file_size:,} bytes"
                )
        
        return {
            'path': str(path),
            'size': file_size,
            'size_mb': file_size / 1024 / 1024
        } 