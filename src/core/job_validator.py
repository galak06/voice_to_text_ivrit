#!/usr/bin/env python3
"""
Job validation utility
Validates job input parameters and provides error messages
"""

from typing import Dict, Any, Optional

class JobValidator:
    """Validates job input parameters following Single Responsibility Principle"""
    
    @staticmethod
    def validate_job_input(job: Dict[str, Any]) -> Optional[str]:
        """
        Validate job input parameters following Single Responsibility Principle.
        
        Args:
            job: The job dictionary containing input parameters
            
        Returns:
            Error message if validation fails, None if valid
        """
        datatype = job['input'].get('type', None)
        engine = job['input'].get('engine', 'speaker-diarization')
        
        if not datatype:
            return "datatype field not provided. Should be 'blob', 'url', or 'file'."
        
        if datatype not in ['blob', 'url', 'file']:
            return f"datatype should be 'blob', 'url', or 'file', but is {datatype} instead."
        
        if engine not in ['speaker-diarization', 'stable-whisper']:
            return f"engine should be 'speaker-diarization' or 'stable-whisper', but is {engine} instead."
        
        return None
    
    @staticmethod
    def validate_audio_file(audio_file: str) -> Optional[str]:
        """
        Validate that the audio file exists and is accessible
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Error message if validation fails, None if valid
        """
        from pathlib import Path
        
        if not audio_file:
            return "No audio file specified"
            
        if not Path(audio_file).exists():
            return f"Audio file not found: {audio_file}"
            
        file_size = Path(audio_file).stat().st_size
        if file_size == 0:
            return f"Audio file is empty: {audio_file}"
            
        return None
    
    @staticmethod
    def validate_model_name(model_name: str) -> Optional[str]:
        """
        Validate model name format
        
        Args:
            model_name: Model name to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not model_name:
            return "Model name is required"
        
        if not isinstance(model_name, str):
            return "Model name must be a string"
        
        if len(model_name.strip()) == 0:
            return "Model name cannot be empty"
        
        return None 