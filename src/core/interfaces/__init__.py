"""
Unified Interfaces Package
Contains all interfaces for the voice-to-text transcription system
Follows Interface Segregation Principle (ISP) for better modularity
"""

# Transcription engine interfaces
from .transcription_engine_interface import (
    ITranscriptionEngine,
    IChunkableTranscriptionEngine,
    IMemoryManagedTranscriptionEngine,
    IConfigurableTranscriptionEngine
)

# Transcription service interfaces
from .transcription_service_interface import (
    TranscriptionServiceInterface,
    TranscriptionOrchestratorInterface,
    AudioProcessorInterface,
    JobValidatorInterface
)

# Audio transcription client interfaces
from .audio_file_validator_interface import AudioFileValidatorInterface
from .transcription_payload_builder_interface import TranscriptionPayloadBuilderInterface
from .transcription_result_collector_interface import TranscriptionResultCollectorInterface

# Output handling interfaces (split for ISP compliance)
from .output_saver_interface import OutputSaverInterface
from .result_display_interface import ResultDisplayInterface

# RunPod specific interfaces
from .runpod_endpoint_interface import RunPodEndpointInterface
from .runpod_endpoint_factory_interface import RunPodEndpointFactoryInterface

# New granular interfaces for better ISP compliance
from .file_processor_interface import FileProcessorInterface
from .data_formatter_interface import DataFormatterInterface
from .result_validator_interface import ResultValidatorInterface

# Data processing interfaces
from .transcription_data_validator_interface import TranscriptionDataValidatorInterface
from .transcription_data_converter_interface import TranscriptionDataConverterInterface
from .speakers_data_extractor_interface import SpeakersDataExtractorInterface
from .text_content_extractor_interface import TextContentExtractorInterface
from .metadata_extractor_interface import MetadataExtractorInterface

__all__ = [
    # Transcription engine interfaces
    'ITranscriptionEngine',
    'IChunkableTranscriptionEngine',
    'IMemoryManagedTranscriptionEngine',
    'IConfigurableTranscriptionEngine',
    
    # Transcription service interfaces
    'TranscriptionServiceInterface',
    'TranscriptionOrchestratorInterface',
    'AudioProcessorInterface',
    'JobValidatorInterface',
    
    # Audio transcription client interfaces
    'AudioFileValidatorInterface',
    'TranscriptionPayloadBuilderInterface', 
    'TranscriptionResultCollectorInterface',
    'OutputSaverInterface',
    'ResultDisplayInterface',
    'RunPodEndpointInterface',
    'RunPodEndpointFactoryInterface',
    'FileProcessorInterface',
    'DataFormatterInterface',
    'ResultValidatorInterface',
    
    # Data processing interfaces
    'TranscriptionDataValidatorInterface',
    'TranscriptionDataConverterInterface',
    'SpeakersDataExtractorInterface',
    'TextContentExtractorInterface',
    'MetadataExtractorInterface'
] 