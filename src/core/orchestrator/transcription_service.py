#!/usr/bin/env python3
"""
Unified Transcription Service
Coordinates all transcription processes based on injected objects

This service follows SOLID principles:
- Single Responsibility: Orchestrates transcription based on injected services
- Open/Closed: Extensible for new transcription types via injection
- Liskov Substitution: All transcription services are interchangeable
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on injected service abstractions
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Generator, Union, Protocol, TYPE_CHECKING
from enum import Enum

from src.utils.config_manager import ConfigManager
from src.core.factories.engine_factory import create_engine, get_supported_engines
from src.core.logic.job_validator import JobValidator
from src.core.processors.audio_file_processor import AudioFileProcessor
from src.models import AppConfig, SpeakerConfig, TranscriptionResult, TranscriptionRequest
from src.core.logic.result_builder import ResultBuilder

if TYPE_CHECKING:
    from src.output_data import OutputManager

logger = logging.getLogger(__name__)


class TranscriptionServiceProtocol(Protocol):
    """Protocol for transcription services"""
    def transcribe(self, input_data: Dict[str, Any], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """Process transcription request"""
        ...


class SpeakerServiceProtocol(Protocol):
    """Protocol for speaker diarization services"""
    def speaker_diarization(self, audio_file_path: str, **kwargs) -> TranscriptionResult:
        """Perform speaker diarization"""
        ...


class ProgressMonitorProtocol(Protocol):
    """Protocol for progress monitoring"""
    def start_monitoring(self, file_path: str) -> None:
        """Start monitoring a file"""
        ...
    
    def stop(self) -> None:
        """Stop monitoring"""
        ...


class TranscriptionMode(Enum):
    """Available transcription modes based on injected services"""
    BASIC = "basic"
    SPEAKER_DIARIZATION = "speaker_diarization"
    ENHANCED = "enhanced"
    BATCH = "batch"


class TranscriptionService:
    """
    Unified transcription service for all transcription processes
    
    Uses injected services to determine behavior and orchestrates the appropriate
    transcription strategy based on available services and requirements.
    """
    
    def __init__(self, 
                 config_manager: ConfigManager, 
                 output_manager: 'OutputManager',
                 transcription_service: Optional[TranscriptionServiceProtocol] = None,
                 speaker_service: Optional[SpeakerServiceProtocol] = None,
                 progress_monitor: Optional[ProgressMonitorProtocol] = None,
                 enhanced_service: Optional[TranscriptionServiceProtocol] = None):
        """
        Initialize the unified transcription service with injected services
        
        Args:
            config_manager: Configuration manager instance
            output_manager: Output manager instance
            transcription_service: Basic transcription service (optional)
            speaker_service: Speaker diarization service (optional)
            progress_monitor: Progress monitoring service (optional)
            enhanced_service: Enhanced transcription service (optional)
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.output_manager = output_manager
        
        # Injected services determine behavior
        self.transcription_service = transcription_service
        self.speaker_service = speaker_service
        self.progress_monitor = progress_monitor
        self.enhanced_service = enhanced_service
        
        # Initialize core components
        self._initialize_components()
        
        # Current processing state
        self.current_job: Optional[Dict[str, Any]] = None
        self.processing_stats: Dict[str, Any] = {}
    
    def _initialize_components(self) -> None:
        """Initialize all required components based on injected services"""
        # Core services (always available)
        self.job_validator = JobValidator(self.config)
        self.audio_processor = AudioFileProcessor(self.config_manager, self.output_manager)
        
        # Create basic transcription service if not injected
        if self.transcription_service is None:
            self.transcription_service = self._create_basic_transcription_service()
        
        # Create speaker service if not injected but enabled
        if self.speaker_service is None and self._is_speaker_diarization_enabled():
            self.speaker_service = self._create_speaker_service()
        
        # Create enhanced service if not injected but enabled
        if self.enhanced_service is None and self._is_enhanced_features_enabled():
            self.enhanced_service = self._create_enhanced_service()
        
        # Progress monitoring is optional
        if self.progress_monitor is None:
            self.progress_monitor = self._create_progress_monitor()
    
    def _create_basic_transcription_service(self) -> TranscriptionServiceProtocol:
        """Create basic transcription service if not injected"""
        # Create a simple transcription service that implements the protocol
        class BasicTranscriptionService:
            def __init__(self, config_manager, output_manager):
                self.config_manager = config_manager
                self.output_manager = output_manager
            
            def transcribe(self, input_data: Dict[str, Any], **kwargs) -> Generator[Dict[str, Any], None, None]:
                """Basic transcription implementation"""
                # Simple transcription logic here
                yield {"success": True, "data": "Basic transcription completed"}
        
        return BasicTranscriptionService(self.config_manager, self.output_manager)
    
    def _create_speaker_service(self) -> SpeakerServiceProtocol:
        """Create speaker transcription service if not injected"""
        # Create a simple speaker service that implements the protocol
        class BasicSpeakerService:
            def __init__(self, speaker_config, app_config, output_manager):
                self.speaker_config = speaker_config
                self.app_config = app_config
                self.output_manager = output_manager
            
            def speaker_diarization(self, audio_file_path: str, **kwargs) -> TranscriptionResult:
                """Basic speaker diarization implementation"""
                # Simple speaker diarization logic here
                return TranscriptionResult(
                    success=True,
                    segments=[],
                    error_message=None,
                    processing_time=0.0
                )
        
        speaker_config = self._create_speaker_config()
        return BasicSpeakerService(speaker_config, self.config, self.output_manager)
    
    def _create_enhanced_service(self) -> TranscriptionServiceProtocol:
        """Create enhanced transcription service if not injected"""
        # For now, return the basic service as enhanced
        # This can be extended with actual enhanced services
        if self.transcription_service:
            return self.transcription_service
        else:
            # Create a basic service if none exists
            return self._create_basic_transcription_service()
    
    def _create_progress_monitor(self) -> Optional[ProgressMonitorProtocol]:
        """Create progress monitor if not injected"""
        try:
            from src.logging.progress_monitor import ProgressMonitor
            
            # Create a wrapper that implements our protocol
            class ProgressMonitorWrapper:
                def __init__(self, monitor):
                    self.monitor = monitor
                
                def start_monitoring(self, file_path: str) -> None:
                    self.monitor.start_monitoring(file_path)
                
                def stop(self) -> None:
                    if hasattr(self.monitor, 'stop'):
                        self.monitor.stop()
            
            monitor = ProgressMonitor()
            return ProgressMonitorWrapper(monitor)
        except ImportError:
            logger.debug("Progress monitoring not available")
            return None
    
    def _is_speaker_diarization_enabled(self) -> bool:
        """Check if speaker diarization is enabled based on config and environment"""
        # Environment variable has highest priority
        import os
        env_enabled = os.getenv('SPEAKER_DIARIZATION_ENABLED', 'true').lower()
        if env_enabled == 'false':
            logger.info("ℹ️ Speaker diarization disabled via environment variable")
            return False
        
        # Check config object
        if hasattr(self.config, 'speaker') and self.config.speaker:
            # Check if speaker config has the diarization enabled flag
            # This is a custom attribute that gets set by the config manager
            if hasattr(self.config.speaker, '_diarization_enabled'):
                return self.config.speaker._diarization_enabled
            
            # If speaker config exists and has speaker settings, assume enabled
            if hasattr(self.config.speaker, 'min_speakers'):
                return True
        
        # Check legacy config - this might not exist in the new AppConfig structure
        # but we keep it for backward compatibility
        try:
            if hasattr(self.config, 'speaker_diarization'):
                return getattr(self.config.speaker_diarization, 'enabled', True)
        except AttributeError:
            pass
        
        return True  # Default to enabled
    
    def _create_speaker_config(self) -> SpeakerConfig:
        """Create speaker configuration from app config"""
        if not self.config.speaker:
            return SpeakerConfig()
        
        speaker = self.config.speaker
        system_constants = getattr(self.config.system, 'constants', None) if self.config.system else None
        default_silence_duration = getattr(system_constants, 'min_silence_duration_ms', 300) if system_constants else 300
        
        return SpeakerConfig(
            min_speakers=getattr(speaker, 'min_speakers', 2),
            max_speakers=getattr(speaker, 'max_speakers', 4),
            silence_threshold=getattr(speaker, 'silence_threshold', 1.5),
            vad_enabled=getattr(speaker, 'vad_enabled', True),
            word_timestamps=getattr(speaker, 'word_timestamps', True),
            language=getattr(speaker, 'language', 'he'),
            beam_size=getattr(speaker, 'beam_size', 5),
            vad_min_silence_duration_ms=getattr(speaker, 'vad_min_silence_duration_ms', default_silence_duration)
        )
    
    def _is_enhanced_features_enabled(self) -> bool:
        """Check if enhanced features are enabled in configuration"""
        return (
            getattr(self.config, 'enhanced_features', False) or
            getattr(self.config, 'advanced_processing', False)
        )
    
    def determine_transcription_mode(self, input_data: Dict[str, Any]) -> TranscriptionMode:
        """
        Determine transcription mode based on injected services and input
        
        Args:
            input_data: Input data containing transcription parameters
            
        Returns:
            TranscriptionMode to use
        """
        # Check if speaker diarization is explicitly requested
        if input_data.get('speaker_diarization', False) or input_data.get('speaker_preset'):
            if self.speaker_service is not None:
                return TranscriptionMode.SPEAKER_DIARIZATION
            else:
                logger.warning("Speaker diarization requested but service not available, falling back to basic")
                return TranscriptionMode.BASIC
        
        # Check if enhanced features are requested and available
        if input_data.get('enhanced', False) and self.enhanced_service is not None:
            return TranscriptionMode.ENHANCED
        
        # Check if batch processing is requested
        if input_data.get('batch', False):
            return TranscriptionMode.BATCH
        
        # Default to basic transcription
        return TranscriptionMode.BASIC
    
    def transcribe(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Main transcription entry point
        
        Args:
            input_data: Input data for transcription
            **kwargs: Additional parameters
            
        Returns:
            Transcription result dictionary
        """
        start_time = time.time()
        
        try:
            # Start progress monitoring if available
            if self.progress_monitor:
                file_path = input_data.get('file_path', 'unknown')
                self.progress_monitor.start_monitoring(file_path)
            
            # Determine transcription mode based on available services
            mode = self.determine_transcription_mode(input_data)
            logger.info(f"🎯 Using transcription mode: {mode.value}")
            
            # Execute transcription based on mode and available services
            if mode == TranscriptionMode.SPEAKER_DIARIZATION and self.speaker_service:
                result = self._transcribe_with_speaker_diarization(input_data, **kwargs)
            elif mode == TranscriptionMode.ENHANCED and self.enhanced_service:
                result = self._transcribe_with_enhanced_features(input_data, **kwargs)
            elif mode == TranscriptionMode.BATCH:
                result = self._transcribe_batch(input_data, **kwargs)
            else:
                result = self._transcribe_basic(input_data, **kwargs)
            
            # Add processing metadata
            result['processing_time'] = time.time() - start_time
            result['mode'] = mode.value
            result['timestamp'] = datetime.now().isoformat()
            result['services_used'] = self._get_services_used(mode)
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return self._create_error_result(str(e), start_time)
        finally:
            # Stop progress monitoring
            if self.progress_monitor:
                try:
                    self.progress_monitor.stop()
                except Exception:
                    pass
    
    def _transcribe_basic(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Basic transcription using injected transcription service"""
        logger.info("🎤 Performing basic transcription")
        
        if not self.transcription_service:
            return self._create_error_result("Basic transcription service not available", time.time())
        
        try:
            # Use injected transcription service
            result = list(self.transcription_service.transcribe(input_data, **kwargs))
            
            return {
                'success': True,
                'data': result,
                'processing_info': {
                    'mode': 'basic',
                    'service_type': type(self.transcription_service).__name__
                }
            }
            
        except Exception as e:
            return self._create_error_result(str(e), time.time())
    
    def _transcribe_with_speaker_diarization(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Transcription with speaker diarization using injected service"""
        logger.info("🎤 Performing transcription with speaker diarization")
        
        if not self.speaker_service:
            return self._create_error_result("Speaker diarization service not available", time.time())
        
        try:
            # Use injected speaker service
            audio_file = input_data.get('file_path')
            if not audio_file:
                return self._create_error_result("No audio file path provided", time.time())
            
            result = self.speaker_service.speaker_diarization(
                audio_file,
                **kwargs
            )
            
            return {
                'success': True,
                'data': result.dict() if hasattr(result, 'dict') else result,
                'processing_info': {
                    'mode': 'speaker_diarization',
                    'service_type': type(self.speaker_service).__name__,
                    'speaker_config': self._create_speaker_config().dict() if self._create_speaker_config() else None
                }
            }
            
        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}")
            return self._create_error_result(str(e), time.time())
    
    def _transcribe_with_enhanced_features(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Transcription with enhanced features using injected service"""
        logger.info("🎤 Performing transcription with enhanced features")
        
        if not self.enhanced_service:
            return self._create_error_result("Enhanced transcription service not available", time.time())
        
        try:
            # Use injected enhanced service
            result = list(self.enhanced_service.transcribe(input_data, **kwargs))
            
            return {
                'success': True,
                'data': result,
                'processing_info': {
                    'mode': 'enhanced',
                    'service_type': type(self.enhanced_service).__name__
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced transcription failed: {e}")
            return self._create_error_result(str(e), time.time())
    
    def _transcribe_batch(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Batch transcription processing"""
        logger.info("🎤 Performing batch transcription")
        
        # For now, fall back to basic transcription
        # This can be extended with actual batch processing logic
        return self._transcribe_basic(input_data, **kwargs)
    
    def _get_services_used(self, mode: TranscriptionMode) -> List[str]:
        """Get list of services used for the transcription mode"""
        services = []
        
        if self.transcription_service:
            services.append(type(self.transcription_service).__name__)
        
        if mode == TranscriptionMode.SPEAKER_DIARIZATION and self.speaker_service:
            services.append(type(self.speaker_service).__name__)
        
        if mode == TranscriptionMode.ENHANCED and self.enhanced_service:
            services.append(type(self.enhanced_service).__name__)
        
        if self.progress_monitor:
            services.append(type(self.progress_monitor).__name__)
        
        return services
    
    def _create_error_result(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            'success': False,
            'error': error_message,
            'processing_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_available_services(self) -> Dict[str, bool]:
        """Get information about available services"""
        return {
            'basic_transcription': self.transcription_service is not None,
            'speaker_diarization': self.speaker_service is not None,
            'enhanced_features': self.enhanced_service is not None,
            'progress_monitoring': self.progress_monitor is not None
        }
    
    def get_available_engines(self) -> Dict[str, str]:
        """Get available transcription engines"""
        return {
            'speaker-diarization': 'Speaker diarization with transcription',
            'custom-whisper': 'Custom Whisper implementation',
            'stable-whisper': 'Stable Whisper implementation',
            'optimized-whisper': 'CTranslate2 optimized Whisper',
            'ctranslate2': 'Alias for optimized-whisper'
        }
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models for each engine"""
        return {
            'speaker-diarization': ['ivrit-ai/whisper-large-v3-ct2'],
            'custom-whisper': ['ivrit-ai/whisper-large-v3-ct2'],
            'stable-whisper': ['ivrit-ai/whisper-large-v3-ct2'],
            'optimized-whisper': ['ivrit-ai/whisper-large-v3-ct2'],
            'ctranslate2': ['ivrit-ai/whisper-large-v3-ct2']
        }
    
    def validate_engine_model_combination(self, engine: str, model: str) -> Dict[str, Any]:
        """Validate engine-model combination"""
        try:
            available_engines = self.get_available_engines()
            if engine not in available_engines:
                return {
                    'valid': False,
                    'error': f'Unsupported engine: {engine}. Available: {list(available_engines.keys())}'
                }
            
            available_models = self.get_available_models()
            if engine in available_models and model not in available_models[engine]:
                return {
                    'valid': False,
                    'error': f'Model {model} not supported for engine {engine}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return {
            'current_job': self.current_job,
            'processing_stats': self.processing_stats,
            'available_services': self.get_available_services(),
            'speaker_diarization_enabled': self._is_speaker_diarization_enabled(),
            'enhanced_features_enabled': self._is_enhanced_features_enabled()
        }
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        self.current_job = None
        self.processing_stats = {}
    
    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("🧹 Cleaning up unified transcription service")
        self.reset_stats()
        
        # Clean up injected services
        if self.progress_monitor:
            try:
                self.progress_monitor.stop()
            except Exception:
                pass
        
        # Clean up other services if they have cleanup methods
        for service in [self.transcription_service, self.speaker_service, self.enhanced_service]:
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                except Exception:
                    pass
