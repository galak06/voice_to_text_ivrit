"""
Interfaces package for data utilities
Contains Protocol definitions for data processing components
"""

from .transcription_data_validator_interface import TranscriptionDataValidatorInterface
from .transcription_data_converter_interface import TranscriptionDataConverterInterface
from .speakers_data_extractor_interface import SpeakersDataExtractorInterface
from .text_content_extractor_interface import TextContentExtractorInterface
from .metadata_extractor_interface import MetadataExtractorInterface

__all__ = [
    'TranscriptionDataValidatorInterface',
    'TranscriptionDataConverterInterface', 
    'SpeakersDataExtractorInterface',
    'TextContentExtractorInterface',
    'MetadataExtractorInterface'
] 