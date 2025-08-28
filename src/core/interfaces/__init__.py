"""
Unified Interfaces Package
Contains all interfaces for the voice-to-text transcription system
Follows Interface Segregation Principle (ISP) for better modularity
"""

# Export existing interfaces
from .output_saver_interface import OutputSaverInterface
from .transcription_protocols import (
    TranscriptionServiceProtocol,
    SpeakerServiceProtocol,
    ProgressMonitorProtocol
)

# Export new engine selection protocols
from .engine_selection_protocols import (
    EngineSelectionStrategyProtocol,
    EngineConfigurationProviderProtocol
)

# Export new speaker labeling protocols
from .speaker_labeling_protocols import (
    SpeakerLabelingProtocol,
    SpeakerLabelingConfigProtocol
)

# Export interfaces that other parts of the system depend on
from .transcription_engine_interface import (
    ITranscriptionEngine,
    IChunkableTranscriptionEngine,
    IMemoryManagedTranscriptionEngine,
    IConfigurableTranscriptionEngine
)

from .transcription_service_interface import (
    TranscriptionServiceInterface,
    TranscriptionOrchestratorInterface,
    AudioProcessorInterface,
    JobValidatorInterface
)

from .runpod_endpoint_interface import RunPodEndpointInterface
from .runpod_endpoint_factory_interface import RunPodEndpointFactoryInterface

# Export data processing interfaces
from .transcription_data_validator_interface import TranscriptionDataValidatorInterface
from .transcription_data_converter_interface import TranscriptionDataConverterInterface
from .speakers_data_extractor_interface import SpeakersDataExtractorInterface
from .text_content_extractor_interface import TextContentExtractorInterface
from .metadata_extractor_interface import MetadataExtractorInterface

# Export additional interfaces
from .audio_file_validator_interface import AudioFileValidatorInterface
from .transcription_payload_builder_interface import TranscriptionPayloadBuilderInterface
from .transcription_result_collector_interface import TranscriptionResultCollectorInterface
from .result_display_interface import ResultDisplayInterface
from .file_processor_interface import FileProcessorInterface
from .data_formatter_interface import DataFormatterInterface
from .result_validator_interface import ResultValidatorInterface

__all__ = [
    'OutputSaverInterface',
    'TranscriptionServiceProtocol',
    'SpeakerServiceProtocol',
    'ProgressMonitorProtocol',
    'EngineSelectionStrategyProtocol',
    'EngineConfigurationProviderProtocol',
    'SpeakerLabelingProtocol',
    'SpeakerLabelingConfigProtocol',
    'ITranscriptionEngine',
    'IChunkableTranscriptionEngine',
    'IMemoryManagedTranscriptionEngine',
    'IConfigurableTranscriptionEngine',
    'TranscriptionServiceInterface',
    'TranscriptionOrchestratorInterface',
    'AudioProcessorInterface',
    'JobValidatorInterface',
    'RunPodEndpointInterface',
    'RunPodEndpointFactoryInterface',
    'TranscriptionDataValidatorInterface',
    'TranscriptionDataConverterInterface',
    'SpeakersDataExtractorInterface',
    'TextContentExtractorInterface',
    'MetadataExtractorInterface',
    'AudioFileValidatorInterface',
    'TranscriptionPayloadBuilderInterface',
    'TranscriptionResultCollectorInterface',
    'ResultDisplayInterface',
    'FileProcessorInterface',
    'DataFormatterInterface',
    'ResultValidatorInterface'
] 