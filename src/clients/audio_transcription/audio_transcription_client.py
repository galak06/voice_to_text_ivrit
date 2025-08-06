"""
Main audio transcription client
"""

import time
from typing import Optional, Dict, Any
from src.utils.config_manager import ConfigManager
from src.models import AppConfig

from .models import TranscriptionRequest, TranscriptionResult
from .interfaces import (
    AudioFileValidatorInterface,
    TranscriptionPayloadBuilderInterface,
    TranscriptionResultCollectorInterface,
    OutputSaverInterface,
    ResultDisplayInterface,
    RunPodEndpointFactoryInterface
)
from .audio_file_validator import DefaultAudioFileValidator
from .transcription_payload_builder import DefaultTranscriptionPayloadBuilder
from .transcription_result_collector import DefaultTranscriptionResultCollector
from .output_saver import DefaultOutputSaver
from .result_display import DefaultResultDisplay
from .transcription_parameter_provider import TranscriptionParameterProvider
from .queue_waiter import QueueWaiter
from .runpod_endpoint_factory import DefaultRunPodEndpointFactory

import logging
logger = logging.getLogger(__name__)

# Type hint for DataUtils   
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.output_data.utils.data_utils import DataUtils


class AudioTranscriptionClient:
    """
    Client for sending audio files to RunPod endpoint for transcription
    
    This class follows SOLID principles:
    - Single Responsibility: Orchestrates transcription process
    - Open/Closed: Extensible through dependency injection
    - Liskov Substitution: Uses protocols for dependencies
    - Interface Segregation: Small, focused interfaces
    - Dependency Inversion: Depends on abstractions, not concretions
    """
    
    def __init__(
        self, 
        config: Optional[AppConfig] = None,
        endpoint_factory: Optional[RunPodEndpointFactoryInterface] = None,
        file_validator: Optional[AudioFileValidatorInterface] = None,
        payload_builder: Optional[TranscriptionPayloadBuilderInterface] = None,
        result_collector: Optional[TranscriptionResultCollectorInterface] = None,
        output_saver: Optional[OutputSaverInterface] = None,
        result_display: Optional[ResultDisplayInterface] = None,
        parameter_provider: Optional[TranscriptionParameterProvider] = None,
        queue_waiter: Optional[QueueWaiter] = None,
        data_utils: Optional['DataUtils'] = None
    ):
        """
        Initialize the audio transcription client with dependency injection
        
        Args:
            config: Optional application configuration
            endpoint_factory: Factory for creating RunPod endpoints
            file_validator: Validator for audio files
            payload_builder: Builder for transcription payloads
            result_collector: Collector for transcription results
            output_saver: Saver for transcription outputs
            result_display: Display for transcription results
            parameter_provider: Provider for transcription parameters
            queue_waiter: Waiter for queue processing
            data_utils: DataUtils instance for data processing
        """
        self.config = config or self._load_default_config()
        self.config_manager = ConfigManager()
        
        # Initialize dependencies with defaults if not provided
        self.endpoint_factory = endpoint_factory or DefaultRunPodEndpointFactory()
        self.file_validator = file_validator or DefaultAudioFileValidator(self.config)
        self.payload_builder = payload_builder or DefaultTranscriptionPayloadBuilder()
        self.result_collector = result_collector or DefaultTranscriptionResultCollector()
        self.output_saver = output_saver or DefaultOutputSaver(data_utils=data_utils)
        self.result_display = result_display or DefaultResultDisplay()
        self.parameter_provider = parameter_provider or TranscriptionParameterProvider(self.config)
        self.queue_waiter = queue_waiter or QueueWaiter()
        
        self.endpoint = None
        self._validate_configuration()
    
    def _load_default_config(self) -> AppConfig:
        """Load default configuration"""
        config_manager = ConfigManager()
        return config_manager.config
    
    def _validate_configuration(self) -> None:
        """Validate configuration and setup RunPod endpoint"""
        if not self.config_manager.validate():
            raise ValueError("Configuration validation failed! Please set up your environment variables first.")
        
        if not self.config.runpod:
            raise ValueError("RunPod configuration not found!")
        
        # Configure RunPod
        if hasattr(self.config, 'runpod') and self.config.runpod:
            # Optional import for RunPod
            try:
                import runpod
                runpod.api_key = self.config.runpod.api_key
                endpoint_id = self.config.runpod.endpoint_id
                if endpoint_id is None:
                    raise ValueError("RunPod endpoint ID not configured!")
                self.endpoint = self.endpoint_factory.create_endpoint(endpoint_id)
            except ImportError:
                pass  # RunPod not available, will be handled during transcription
    
    def transcribe_audio(self, audio_file_path: str, model: Optional[str] = None, 
                        engine: Optional[str] = None, save_output: bool = True) -> bool:
        """
        Transcribe an audio file using RunPod
        
        Args:
            audio_file_path: Path to the audio file
            model: Optional model to use for transcription
            engine: Optional engine to use for transcription
            save_output: Whether to save outputs in all formats
            
        Returns:
            True if transcription was successful, False otherwise
        """
        try:
            start_time = time.time()
            
            # Validate audio file
            file_info = self.file_validator.validate(audio_file_path)
            self._log_file_info(file_info)
            
            # Get transcription parameters
            params = self.parameter_provider.get_parameters(model, engine)
            self._log_parameters(params)
            
            # Create transcription request
            request = TranscriptionRequest(
                audio_file_path=audio_file_path,
                model=params['model'],
                engine=params['engine'],
                streaming_enabled=self.config.runpod.streaming_enabled if self.config.runpod else False
            )
            
            # Execute transcription
            result = self._execute_transcription(request, save_output)
            
            # Log processing time
            processing_time = time.time() - start_time
            logger.info(f"Processing time: {processing_time:.2f} seconds")
            
            return result.success
            
        except Exception as e:
            logger.error(f"Error transcribing audio file: {e}")
            return False
    
    def _execute_transcription(self, request: TranscriptionRequest, save_output: bool) -> TranscriptionResult:
        """Execute the transcription process"""
        # Prepare and send payload
        payload = self.payload_builder.build(request)
        logger.info("Sending to RunPod endpoint...")
        
        if self.endpoint is None:
            raise RuntimeError("RunPod endpoint not initialized!")
        run_request = self.endpoint.run(payload)
        
        # Wait for task to be queued
        logger.info("Waiting for task to be queued...")
        status = self.queue_waiter.wait_for_queue(run_request)
        logger.info(f"Task status: {status}")
        
        # Collect results
        logger.info("Collecting transcription results...")
        segments = self.result_collector.collect(run_request)
        
        # Display results
        self.result_display.display(segments)
        
        # Save outputs if requested
        saved_files = {}
        if save_output and segments:
            try:
                saved_files = self.output_saver.save(
                    request.audio_file_path, segments, request.model, request.engine
                )
                self._log_saved_files(saved_files)
            except Exception as e:
                logger.warning(f"Failed to save outputs: {e}")
        elif not save_output:
            logger.info("Output saving disabled")
        
        return TranscriptionResult(
            success=True,
            segments=segments,
            processing_time=time.time()
        )
    
    def _log_file_info(self, file_info: Dict[str, Any]) -> None:
        """Log file information"""
        logger.info(f"Audio file: {file_info['path']}")
        logger.info(f"File size: {file_info['size']:,} bytes ({file_info['size_mb']:.1f} MB)")
    
    def _log_parameters(self, params: Dict[str, str]) -> None:
        """Log transcription parameters"""
        logger.info(f"Model: {params['model']}")
        logger.info(f"Engine: {params['engine']}")
        if self.config.runpod and self.config.runpod.endpoint_id:
            logger.info(f"Endpoint: {self.config.runpod.endpoint_id}")
    
    def _log_saved_files(self, saved_files: Dict[str, str]) -> None:
        """Log saved files information"""
        logger.info("All formats saved:")
        for format_type, file_path in saved_files.items():
            logger.info(f"  {format_type.upper()}: {file_path}") 