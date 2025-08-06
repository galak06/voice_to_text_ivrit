#!/usr/bin/env python3
"""
Data Utilities
Handles data validation, conversion, and processing following SOLID principles
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import is_dataclass, asdict
import json
import ast
from abc import ABC, abstractmethod

# Import interfaces from the new interfaces package
from .interfaces import (
    TranscriptionDataValidatorInterface,
    TranscriptionDataConverterInterface,
    SpeakersDataExtractorInterface,
    TextContentExtractorInterface,
    MetadataExtractorInterface
)


class BaseDataValidator:
    """Base class for data validation"""
    
    @staticmethod
    def is_transcription_result(obj: Any) -> bool:
        """Check if object is a TranscriptionResult dataclass or Pydantic model"""
        # Check for Pydantic models
        if hasattr(obj, 'model_dump') and hasattr(obj, 'speakers'):
            return True
        
        # Check for dataclasses
        return is_dataclass(obj) and hasattr(obj, 'speakers')


class TranscriptionDataValidatorImpl(BaseDataValidator):
    """Implementation of transcription data validation"""
    
    def validate(self, data: Any) -> bool:
        """Validate transcription data structure"""
        if not data:
            return False
        
        # Check if it's a dataclass or Pydantic model
        if self.is_transcription_result(data):
            return True
        
        # Check if it's a dictionary with required fields
        if isinstance(data, dict):
            required_fields = ['speakers', 'full_text']
            return any(field in data for field in required_fields)
        
        return False


class TranscriptionDataConverterImpl:
    """Implementation of transcription data conversion"""
    
    def convert(self, data: Any) -> Dict[str, Any]:
        """Convert TranscriptionResult dataclass or Pydantic model to dictionary"""
        # Handle Pydantic models
        if hasattr(data, 'model_dump'):
            return data.model_dump()
        
        # Handle dataclasses
        if BaseDataValidator.is_transcription_result(data):
            return asdict(data)
        
        # If it's already a dict, return as is
        if isinstance(data, dict):
            return data
        
        # Handle lists (from faster-whisper)
        if isinstance(data, list):
            return {"segments": data}
        
        # For other types, return as a simple dict with the string representation
        return {"content": str(data)}


class SegmentProcessor:
    """Handles segment processing operations"""
    
    @staticmethod
    def convert_segments_to_speakers(segments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Convert list of segments to speakers format"""
        speakers = {}
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            if speaker not in speakers:
                speakers[speaker] = []
            speakers[speaker].append(segment)
        return speakers
    
    @staticmethod
    def extract_text_from_segments(segments: List[Dict[str, Any]]) -> str:
        """Extract text content from list of segments"""
        text_parts = []
        for segment in segments:
            if isinstance(segment, dict) and 'text' in segment:
                text_parts.append(segment['text'])
        return ' '.join(text_parts)


class StringContentParser:
    """Handles parsing of string content representations"""
    
    @staticmethod
    def parse_string_content(content: str) -> Optional[List[Dict[str, Any]]]:
        """Parse string content representation to list of segments"""
        try:
            content_data = ast.literal_eval(content)
            if isinstance(content_data, list):
                return content_data
        except (ValueError, SyntaxError):
            pass
        return None


class SpeakersDataExtractorImpl:
    """Implementation of speakers data extraction"""
    
    def __init__(self):
        self.segment_processor = SegmentProcessor()
        self.string_parser = StringContentParser()
    
    def extract(self, data: Any) -> Dict[str, List[Dict[str, Any]]]:
        """Extract speakers data from transcription data"""
        # Handle list of segments (from faster-whisper)
        if isinstance(data, list):
            return self.segment_processor.convert_segments_to_speakers(data)
        
        # Handle dictionary format
        if isinstance(data, dict):
            return self._extract_from_dict(data)
        
        return {}
    
    def _extract_from_dict(self, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract speakers data from dictionary"""
        # Direct speakers field
        if 'speakers' in data:
            return data['speakers']
        
        # Segments field
        if 'segments' in data:
            return self.segment_processor.convert_segments_to_speakers(data['segments'])
        
        # String content field
        if 'content' in data and isinstance(data['content'], str):
            return self._extract_from_string_content(data['content'])
        
        return {}
    
    def _extract_from_string_content(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract speakers data from string content"""
        parsed_content = self.string_parser.parse_string_content(content)
        if parsed_content:
            return self.segment_processor.convert_segments_to_speakers(parsed_content)
        return {}


class TextContentExtractorImpl:
    """Implementation of text content extraction"""
    
    def __init__(self):
        self.segment_processor = SegmentProcessor()
        self.string_parser = StringContentParser()
        self.speakers_extractor = SpeakersDataExtractorImpl()
    
    def extract(self, data: Any) -> str:
        """Extract text content from transcription data"""
        # Handle list of segments (from faster-whisper)
        if isinstance(data, list):
            return self.segment_processor.extract_text_from_segments(data)
        
        # Handle dictionary format
        if isinstance(data, dict):
            return self._extract_from_dict(data)
        
        return ""
    
    def _extract_from_dict(self, data: Dict[str, Any]) -> str:
        """Extract text content from dictionary"""
        # Try different possible text fields
        text_fields = ['full_text', 'text', 'transcription']
        
        for field in text_fields:
            if field in data and data[field]:
                return str(data[field])
        
        # Handle string content field
        if 'content' in data and isinstance(data['content'], str):
            return self._extract_from_string_content(data['content'])
        
        # Extract from speakers
        speakers = self.speakers_extractor.extract(data)
        if speakers:
            return self._extract_from_speakers(speakers)
        
        return ""
    
    def _extract_from_string_content(self, content: str) -> str:
        """Extract text content from string content"""
        parsed_content = self.string_parser.parse_string_content(content)
        if parsed_content:
            return self.segment_processor.extract_text_from_segments(parsed_content)
        return content
    
    def _extract_from_speakers(self, speakers: Dict[str, List[Dict[str, Any]]]) -> str:
        """Extract text content from speakers data"""
        text_parts = []
        for speaker_name, segments in speakers.items():
            for segment in segments:
                if isinstance(segment, dict) and 'text' in segment:
                    text_parts.append(segment['text'])
        return ' '.join(text_parts)


class MetadataExtractorImpl:
    """Implementation of metadata extraction"""
    
    def get_model_name(self, data: Any) -> str:
        """Extract model name from transcription data"""
        if BaseDataValidator.is_transcription_result(data):
            return getattr(data, 'model_name', 'unknown')
        
        if isinstance(data, dict):
            return data.get('model_name', data.get('model', 'unknown'))
        
        return 'unknown'
    
    def get_audio_file(self, data: Any) -> str:
        """Extract audio file path from transcription data"""
        if BaseDataValidator.is_transcription_result(data):
            return getattr(data, 'audio_file', 'unknown')
        
        if isinstance(data, dict):
            return data.get('audio_file', data.get('file_path', 'unknown'))
        
        return 'unknown'


class DataUtils:
    """Main data utilities class following Facade pattern"""
    
    def __init__(self):
        self.validator: TranscriptionDataValidatorInterface = TranscriptionDataValidatorImpl()
        self.converter: TranscriptionDataConverterInterface = TranscriptionDataConverterImpl()
        self.speakers_extractor: SpeakersDataExtractorInterface = SpeakersDataExtractorImpl()
        self.text_extractor: TextContentExtractorInterface = TextContentExtractorImpl()
        self.metadata_extractor: MetadataExtractorInterface = MetadataExtractorImpl()
    
    def is_transcription_result(self, obj: Any) -> bool:
        """Check if object is a TranscriptionResult dataclass or Pydantic model"""
        return BaseDataValidator.is_transcription_result(obj)
    
    def convert_transcription_result_to_dict(self, transcription_data: Any) -> Dict[str, Any]:
        """Convert TranscriptionResult dataclass or Pydantic model to dictionary"""
        return self.converter.convert(transcription_data)
    

    
    # Instance methods for dependency injection
    def extract_speakers_data(self, data: Any) -> Dict[str, List[Dict[str, Any]]]:
        """Extract speakers data from transcription data"""
        return self.speakers_extractor.extract(data)
    
    def extract_text_content(self, data: Any) -> str:
        """Extract text content from transcription data"""
        return self.text_extractor.extract(data)
    
    def validate_transcription_data(self, data: Any) -> bool:
        """Validate transcription data structure"""
        return self.validator.validate(data)
    
    def get_model_name(self, data: Any) -> str:
        """Extract model name from transcription data"""
        return self.metadata_extractor.get_model_name(data)
    
    def get_audio_file(self, data: Any) -> str:
        """Extract audio file path from transcription data"""
        return self.metadata_extractor.get_audio_file(data)


 