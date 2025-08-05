#!/usr/bin/env python3
"""
Data Utilities
Handles data validation, conversion, and processing
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import is_dataclass, asdict
import json


class DataUtils:
    """Data utility functions"""
    
    @staticmethod
    def is_transcription_result(obj: Any) -> bool:
        """Check if object is a TranscriptionResult dataclass or Pydantic model"""
        # Check for Pydantic models
        if hasattr(obj, 'model_dump') and hasattr(obj, 'speakers'):
            return True
        
        # Check for dataclasses
        return is_dataclass(obj) and hasattr(obj, 'speakers')
    
    @staticmethod
    def convert_transcription_result_to_dict(transcription_data: Any) -> Dict[str, Any]:
        """Convert TranscriptionResult dataclass or Pydantic model to dictionary"""
        # Handle Pydantic models
        if hasattr(transcription_data, 'model_dump'):
            return transcription_data.model_dump()
        
        # Handle dataclasses
        if DataUtils.is_transcription_result(transcription_data):
            return asdict(transcription_data)
        
        # If it's already a dict, return as is
        if isinstance(transcription_data, dict):
            return transcription_data
        
        # For other types, return as a simple dict with the string representation
        return {"content": str(transcription_data)}
    
    @staticmethod
    def extract_speakers_data(data: Any) -> Dict[str, List[Dict[str, Any]]]:
        """Extract speakers data from transcription data"""
        # Handle list of segments (from faster-whisper)
        if isinstance(data, list):
            # Convert segments to speakers format
            speakers = {}
            for segment in data:
                speaker = segment.get('speaker', 'Unknown')
                if speaker not in speakers:
                    speakers[speaker] = []
                speakers[speaker].append(segment)
            return speakers
        
        # Handle dictionary format
        if isinstance(data, dict):
            if 'speakers' in data:
                return data['speakers']
            elif 'segments' in data:
                # Convert segments to speakers format
                speakers = {}
                for segment in data['segments']:
                    speaker = segment.get('speaker', 'Unknown')
                    if speaker not in speakers:
                        speakers[speaker] = []
                    speakers[speaker].append(segment)
                return speakers
            elif 'content' in data and isinstance(data['content'], str):
                # Handle case where data is stored as string representation
                try:
                    import ast
                    content_data = ast.literal_eval(data['content'])
                    if isinstance(content_data, list):
                        # Convert segments to speakers format
                        speakers = {}
                        for segment in content_data:
                            speaker = segment.get('speaker', 'Unknown')
                            if speaker not in speakers:
                                speakers[speaker] = []
                            speakers[speaker].append(segment)
                        return speakers
                except (ValueError, SyntaxError) as e:
                    # If ast.literal_eval fails, try to extract as text
                    pass
        
        return {}
    
    @staticmethod
    def extract_text_content(data: Any) -> str:
        """Extract text content from transcription data"""
        # Handle list of segments (from faster-whisper)
        if isinstance(data, list):
            text_parts = []
            for segment in data:
                if isinstance(segment, dict) and 'text' in segment:
                    text_parts.append(segment['text'])
            return ' '.join(text_parts)
        
        # Handle dictionary format
        if isinstance(data, dict):
            # Try different possible text fields
            text_fields = ['full_text', 'text', 'transcription']
            
            for field in text_fields:
                if field in data and data[field]:
                    return str(data[field])
            
            # Handle case where data is stored as string representation
            if 'content' in data and isinstance(data['content'], str):
                try:
                    import ast
                    content_data = ast.literal_eval(data['content'])
                    if isinstance(content_data, list):
                        text_parts = []
                        for segment in content_data:
                            if isinstance(segment, dict) and 'text' in segment:
                                text_parts.append(segment['text'])
                        return ' '.join(text_parts)
                except (ValueError, SyntaxError) as e:
                    # If ast.literal_eval fails, return the content as is
                    return data['content']
            
            # If no direct text field, try to extract from speakers
            speakers = DataUtils.extract_speakers_data(data)
            if speakers:
                text_parts = []
                for speaker_name, segments in speakers.items():
                    for segment in segments:
                        if isinstance(segment, dict) and 'text' in segment:
                            text_parts.append(segment['text'])
                return ' '.join(text_parts)
        
        return ""
    
    @staticmethod
    def validate_transcription_data(data: Any) -> bool:
        """Validate transcription data structure"""
        if not data:
            return False
        
        # Check if it's a dataclass
        if DataUtils.is_transcription_result(data):
            return True
        
        # Check if it's a dictionary with required fields
        if isinstance(data, dict):
            required_fields = ['speakers', 'full_text']
            return any(field in data for field in required_fields)
        
        return False
    
    @staticmethod
    def get_model_name(data: Any) -> str:
        """Extract model name from transcription data"""
        if DataUtils.is_transcription_result(data):
            return getattr(data, 'model_name', 'unknown')
        
        if isinstance(data, dict):
            return data.get('model_name', data.get('model', 'unknown'))
        
        return 'unknown'
    
    @staticmethod
    def get_audio_file(data: Any) -> str:
        """Extract audio file path from transcription data"""
        if DataUtils.is_transcription_result(data):
            return getattr(data, 'audio_file', 'unknown')
        
        if isinstance(data, dict):
            return data.get('audio_file', data.get('file_path', 'unknown'))
        
        return 'unknown' 