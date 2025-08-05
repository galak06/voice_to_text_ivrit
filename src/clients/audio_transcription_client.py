#!/usr/bin/env python3
"""
Audio transcription client for RunPod endpoint
Refactored to follow SOLID principles and clean code practices
"""

import os
import time
import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any, Protocol
from dataclasses import dataclass
from src.utils.config_manager import ConfigManager
from src.models import AppConfig

# Optional import for RunPod
try:
    import runpod
    RUNPOD_AVAILABLE = True
except ImportError:
    runpod = None
    RUNPOD_AVAILABLE = False


@dataclass
class TranscriptionRequest:
    """Data class for transcription request parameters"""
    audio_file_path: str
    model: str
    engine: str
    streaming_enabled: bool = False


@dataclass
class TranscriptionResult:
    """Data class for transcription results"""
    success: bool
    segments: List[Dict[str, Any]]
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class AudioFileValidator(Protocol):
    """Protocol for audio file validation"""
    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file and return file information"""
        ...


class TranscriptionPayloadBuilder(Protocol):
    """Protocol for building transcription payloads"""
    def build(self, request: TranscriptionRequest) -> Dict[str, Any]:
        """Build payload for transcription request"""
        ...


class TranscriptionResultCollector(Protocol):
    """Protocol for collecting transcription results"""
    def collect(self, run_request, max_timeouts: int = 5) -> List[Dict[str, Any]]:
        """Collect transcription results"""
        ...


class OutputSaver(Protocol):
    """Protocol for saving transcription outputs"""
    def save(self, audio_file_path: str, segments: List[Dict[str, Any]], 
             model: str, engine: str) -> Dict[str, str]:
        """Save transcription outputs in multiple formats"""
        ...


class ResultDisplay(Protocol):
    """Protocol for displaying transcription results"""
    def display(self, segments: List[Dict[str, Any]]) -> None:
        """Display transcription results"""
        ...


class RunPodEndpoint(Protocol):
    """Protocol for RunPod endpoint operations"""
    def run(self, request_input: Dict[str, Any]) -> Any:
        """Run transcription request"""
        ...


class RunPodEndpointFactory(ABC):
    """Abstract factory for creating RunPod endpoints"""
    
    @abstractmethod
    def create_endpoint(self, endpoint_id: str) -> RunPodEndpoint:
        """Create a RunPod endpoint"""
        pass


class DefaultRunPodEndpointFactory(RunPodEndpointFactory):
    """Default implementation of RunPod endpoint factory"""
    
    def create_endpoint(self, endpoint_id: str) -> RunPodEndpoint:
        """Create a RunPod endpoint"""
        if not RUNPOD_AVAILABLE:
            raise ImportError("RunPod module not available. Please install it with: pip install runpod")
        
        if runpod is None:
            raise RuntimeError("RunPod module not properly imported")
        
        return runpod.Endpoint(endpoint_id)


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


class DefaultTranscriptionPayloadBuilder:
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


class DefaultTranscriptionResultCollector:
    """Default implementation of transcription result collector"""
    
    def collect(self, run_request, max_timeouts: int = 5) -> List[Dict[str, Any]]:
        """Collect transcription results from RunPod"""
        segments = []
        timeouts = 0
        
        while True:
            try:
                for segment in run_request.stream():
                    if "error" in segment:
                        raise RuntimeError(f"Transcription error: {segment['error']}")
                    
                    segments.append(segment)
                
                break  # Successfully completed
                
            except Exception as e:
                timeouts += 1
                if timeouts > max_timeouts:
                    raise RuntimeError(f"Too many timeouts ({max_timeouts})")
                
                time.sleep(1)
        
        return segments


class DefaultOutputSaver:
    """Default implementation of output saver"""
    
    def save(self, audio_file_path: str, segments: List[Dict[str, Any]], 
             model: str, engine: str) -> Dict[str, str]:
        """Save transcription outputs in multiple formats"""
        try:
            from src.output_data import OutputManager
            
            output_manager = OutputManager()
            
            # Save all formats using the unified method
            saved_files = output_manager.save_transcription(
                transcription_data=segments,
                audio_file=audio_file_path,
                model=model,
                engine=engine
            )
            
            return saved_files
            
        except Exception as e:
            raise RuntimeError(f"Failed to save outputs: {e}")


class DefaultResultDisplay:
    """Default implementation of result display"""
    
    def display(self, segments: List[Dict[str, Any]]) -> None:
        """Display transcription results"""
        print("\n🎉 Transcription completed!")
        print("=" * 50)
        
        if segments:
            for i, segment in enumerate(segments, 1):
                if 'text' in segment:
                    print(f"{i}. {segment['text']}")
                if 'start' in segment and 'end' in segment:
                    print(f"   Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
                print()
        else:
            print("No transcription segments received")


class TranscriptionParameterProvider:
    """Provider for transcription parameters with defaults"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def get_parameters(self, model: Optional[str] = None, engine: Optional[str] = None) -> Dict[str, str]:
        """Get transcription parameters with defaults"""
        if self.config.transcription:
            default_model = self.config.transcription.default_model
            default_engine = self.config.transcription.default_engine
        else:
            default_model = "ivrit-ai/whisper-large-v3-ct2"
            default_engine = "faster-whisper"
        
        return {
            'model': model or default_model,
            'engine': engine or default_engine
        }


class QueueWaiter:
    """Handles waiting for RunPod queue processing"""
    
    def wait_for_queue(self, run_request, timeout_seconds: int = 300) -> str:
        """Wait for task to be queued and return status"""
        status = "UNKNOWN"
        for i in range(timeout_seconds):
            status = run_request.status()
            if status == "IN_QUEUE":
                time.sleep(1)
                continue
            break
        
        return status


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
        endpoint_factory: Optional[RunPodEndpointFactory] = None,
        file_validator: Optional[AudioFileValidator] = None,
        payload_builder: Optional[TranscriptionPayloadBuilder] = None,
        result_collector: Optional[TranscriptionResultCollector] = None,
        output_saver: Optional[OutputSaver] = None,
        result_display: Optional[ResultDisplay] = None,
        parameter_provider: Optional[TranscriptionParameterProvider] = None,
        queue_waiter: Optional[QueueWaiter] = None
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
        """
        self.config = config or self._load_default_config()
        self.config_manager = ConfigManager()
        
        # Initialize dependencies with defaults if not provided
        self.endpoint_factory = endpoint_factory or DefaultRunPodEndpointFactory()
        self.file_validator = file_validator or DefaultAudioFileValidator(self.config)
        self.payload_builder = payload_builder or DefaultTranscriptionPayloadBuilder()
        self.result_collector = result_collector or DefaultTranscriptionResultCollector()
        self.output_saver = output_saver or DefaultOutputSaver()
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
        if runpod is not None:  # Type check for linter
            runpod.api_key = self.config.runpod.api_key
            endpoint_id = self.config.runpod.endpoint_id
            if endpoint_id is None:
                raise ValueError("RunPod endpoint ID not configured!")
            self.endpoint = self.endpoint_factory.create_endpoint(endpoint_id)
    
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
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            
            return result.success
            
        except Exception as e:
            print(f"❌ Error transcribing audio file: {e}")
            return False
    
    def _execute_transcription(self, request: TranscriptionRequest, save_output: bool) -> TranscriptionResult:
        """Execute the transcription process"""
        # Prepare and send payload
        payload = self.payload_builder.build(request)
        print("🚀 Sending to RunPod endpoint...")
        
        if self.endpoint is None:
            raise RuntimeError("RunPod endpoint not initialized!")
        run_request = self.endpoint.run(payload)
        
        # Wait for task to be queued
        print("⏳ Waiting for task to be queued...")
        status = self.queue_waiter.wait_for_queue(run_request)
        print(f"📊 Task status: {status}")
        
        # Collect results
        print("🎧 Collecting transcription results...")
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
                print(f"⚠️  Warning: Failed to save outputs: {e}")
        elif not save_output:
            print("💾 Output saving disabled")
        
        return TranscriptionResult(
            success=True,
            segments=segments,
            processing_time=time.time()
        )
    
    def _log_file_info(self, file_info: Dict[str, Any]) -> None:
        """Log file information"""
        print(f"📁 Audio file: {file_info['path']}")
        print(f"📊 File size: {file_info['size']:,} bytes ({file_info['size_mb']:.1f} MB)")
    
    def _log_parameters(self, params: Dict[str, str]) -> None:
        """Log transcription parameters"""
        print(f"🤖 Model: {params['model']}")
        print(f"⚙️  Engine: {params['engine']}")
        if self.config.runpod and self.config.runpod.endpoint_id:
            print(f"☁️  Endpoint: {self.config.runpod.endpoint_id}")
    
    def _log_saved_files(self, saved_files: Dict[str, str]) -> None:
        """Log saved files information"""
        print(f"💾 All formats saved:")
        for format_type, file_path in saved_files.items():
            print(f"   📄 {format_type.upper()}: {file_path}")





 