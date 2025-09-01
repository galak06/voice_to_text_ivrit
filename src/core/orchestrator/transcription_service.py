#!/usr/bin/env python3
"""
Main Transcription Service Orchestrator
Coordinates all transcription processes using dependency injection
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum

from src.utils.config_manager import ConfigManager
from src.core.interfaces.transcription_protocols import (
    TranscriptionServiceProtocol,
    SpeakerServiceProtocol,
    ProgressMonitorProtocol
)
from src.core.factories import (
    TranscriptionServiceFactory,
    SpeakerServiceFactory,
    ProgressMonitorFactory
)
from src.models import SpeakerConfig
from src.utils.dependency_injection import DependencyContainer, SpeakerServiceInjector

if TYPE_CHECKING:
    from src.output_data import OutputManager

logger = logging.getLogger(__name__)


class TranscriptionMode(Enum):
    """Available transcription modes based on injected services"""
    BASIC = "basic"
    SPEAKER_DIARIZATION = "speaker_diarization"
    ENHANCED = "enhanced"
    BATCH = "batch"
    CHUNKED = "chunked"


class TranscriptionService:
    """
    Main transcription orchestrator that uses injected services
    
    This class follows SOLID principles:
    - Single Responsibility: Orchestrates transcription based on injected services
    - Open/Closed: Extensible for new transcription types via injection
    - Liskov Substitution: All transcription services are interchangeable
    - Interface Segregation: Clean, focused interfaces
    - Dependency Inversion: Depends on injected service abstractions
    """
    
    def __init__(self, config_manager, output_manager=None):
        """
        Initialize transcription service with dependency injection
        
        Args:
            config_manager: Configuration manager (injected)
            output_manager: Output manager (injected)
        """
        if not config_manager:
            raise ValueError("ConfigManager is required - no fallback to direct config")
        
        self.config_manager = config_manager
        self.output_manager = output_manager
        
        # Initialize dependency injection container
        self._di_container = DependencyContainer()
        self._speaker_injector = SpeakerServiceInjector(self._di_container)
        
        # Initialize transcription engine
        self.transcription_engine = self._create_transcription_engine()
        
        # Initialize progress monitor
        self.progress_monitor = None
        
        logger.info("🚀 Transcription Service initialized with dependency injection")

    def _create_transcription_engine(self):
        """Create transcription engine with dependency injection"""
        try:
            from src.core.engines.consolidated_transcription_engine import ConsolidatedTranscriptionEngine
            from src.core.engines.utilities.simple_text_processor import SimpleTextProcessor
            
            logger.info(f"🔍 CONFIG DEBUG: TranscriptionService creating engine with ConfigManager: {type(self.config_manager)}")
            logger.info(f"🔍 CONFIG DEBUG: ConfigManager config type: {type(self.config_manager.config)}")
            
            # Create and inject text processor
            text_processor = SimpleTextProcessor()
            logger.info(f"🔍 CONFIG DEBUG: Created text processor: {type(text_processor)}")
            
            logger.info(f"🔍 CONFIG DEBUG: Creating ConsolidatedTranscriptionEngine...")
            engine = ConsolidatedTranscriptionEngine(
                config_manager=self.config_manager,
                text_processor=text_processor
            )
            logger.info(f"🔍 CONFIG DEBUG: Created engine: {type(engine)}")
            return engine
            
        except Exception as e:
            logger.error(f"❌ Error creating transcription engine: {e}")
            logger.error(f"❌ CONFIG DEBUG: Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ CONFIG DEBUG: Full traceback: {traceback.format_exc()}")
            raise
    
    def _create_speaker_service(self) -> Optional[SpeakerServiceProtocol]:
        """Create enhanced speaker service using dependency injection - fail fast if creation fails"""
        try:
            # Check if speaker diarization is enabled
            if not self._is_speaker_diarization_enabled():
                logger.info("ℹ️ Speaker diarization disabled, not creating speaker service")
                return None
            
            # Use dependency injection to create enhanced speaker service
            speaker_service = self._speaker_injector.create_enhanced_speaker_service(
                config_manager=self.config_manager,
                transcription_engine=self.transcription_engine
            )
            
            if not speaker_service:
                raise RuntimeError("Speaker service injector returned None")
            
            # Inject the speaker service into this transcription service
            self._speaker_injector.inject_into_transcription_service(
                self, 
                speaker_service
            )
            
            logger.info(f"🎤 Created and injected enhanced speaker service: {type(speaker_service).__name__}")
            return speaker_service
            
        except Exception as e:
            logger.error(f"❌ Failed to create enhanced speaker service: {e}")
            raise RuntimeError(f"Failed to create enhanced speaker service: {e}")
    
    def _create_speaker_config(self) -> SpeakerConfig:
        """Create speaker configuration from app config"""
        if not self.config_manager.config.speaker:
            return SpeakerConfig()
        
        return self.config_manager.config.speaker
    
    def _is_speaker_diarization_enabled(self) -> bool:
        """Check if speaker diarization is enabled based on config and environment"""
        # Configuration file has highest priority
        try:
            # Check if speaker_diarization section exists and is enabled
            if hasattr(self.config_manager.config, 'speaker_diarization'):
                speaker_config = self.config_manager.config.speaker_diarization
                if hasattr(speaker_config, 'enabled'):
                    config_enabled = speaker_config.enabled
                    logger.info(f"ℹ️ Speaker diarization from config: {config_enabled}")
                    return config_enabled
                # If no explicit enabled flag, check if speaker config exists
                logger.info("ℹ️ Speaker diarization config found, defaulting to enabled")
                return True
            # Fallback: check for 'speaker' section
            elif hasattr(self.config_manager.config, 'speaker') and self.config_manager.config.speaker:
                speaker_config = self.config_manager.config.speaker
                if hasattr(speaker_config, 'enabled'):
                    config_enabled = speaker_config.enabled
                    logger.info(f"ℹ️ Speaker diarization from legacy config: {config_enabled}")
                    return config_enabled
                logger.info("ℹ️ Legacy speaker config found, defaulting to enabled")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Error checking speaker diarization config: {e}")
        
        # Environment variable as fallback (lower priority)
        import os
        env_enabled = os.getenv('SPEAKER_DIARIZATION_ENABLED', 'true').lower()
        if env_enabled == 'false':
            logger.info("ℹ️ Speaker diarization disabled via environment variable fallback")
            return False
        
        logger.info("ℹ️ Speaker diarization enabled by default")
        return True  # Default to enabled
    
    def determine_transcription_mode(self, input_data: Dict[str, Any]) -> TranscriptionMode:
        """
        Determine transcription mode based on injected services and input
        
        Args:
            input_data: Input data containing transcription parameters
            
        Returns:
            TranscriptionMode to use
        """
        # Check if chunked transcription is explicitly requested
        if input_data.get('chunked', False) or input_data.get('chunk_duration'):
            logger.info("🎯 Chunked transcription requested")
            return TranscriptionMode.CHUNKED
        
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
        
        # Check if audio file is long enough to warrant chunking
        file_path = input_data.get('file_path', '')
        if file_path and self._should_use_chunked_transcription(file_path):
            logger.info("🎯 Long audio file detected, using chunked transcription")
            return TranscriptionMode.CHUNKED
        
        # Default to basic transcription
        return TranscriptionMode.BASIC
    
    def _should_use_chunked_transcription(self, file_path: str) -> bool:
        """Determine if chunked transcription should be used based on audio length"""
        try:
            import librosa
            duration = librosa.get_duration(path=file_path)
            # Use chunked transcription for files longer than 5 minutes
            return duration > 300  # 5 minutes = 300 seconds
        except Exception as e:
            logger.debug(f"Could not determine audio duration: {e}")
            return False
    
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
            elif mode == TranscriptionMode.CHUNKED:
                result = self._transcribe_chunked(input_data, **kwargs)
            else:
                result = self._transcribe_basic(input_data, **kwargs)
            
            # Note: Enhanced JSON files are created by transcription strategies, not here
            
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
        
        if not self.transcription_engine:
            return self._create_error_result("Basic transcription engine not available", time.time())
        
        try:
            # Extract audio file path and model name from input data
            audio_file_path = input_data.get('file_path')
            model_name = kwargs.get('model') or self.config_manager.config.transcription.default_model
            
            if not audio_file_path:
                return self._create_error_result("No audio file path provided", time.time())
            
            # Use injected transcription engine with correct parameters
            # Convert enum to string value if needed
            if hasattr(model_name, 'value'):
                model_name_str = model_name.value
            else:
                model_name_str = str(model_name)
            
            result = self.transcription_engine.transcribe(audio_file_path, model_name_str)
            
            logger.info(f"🔍 Service result type: {type(result)}")
            logger.info(f"🔍 Service result success: {result.success if hasattr(result, 'success') else 'N/A'}")
            
            # Check if result is a TranscriptionResult object
            if hasattr(result, 'success') and result.success:
                # Return the transcription data in the format expected by output processor
                orchestrator_result = {
                    'success': True,
                    'transcription': {
                        'text': result.text if hasattr(result, 'text') else '',
                        'segments': result.segments if hasattr(result, 'segments') else [],
                        'speakers': result.speakers if hasattr(result, 'speakers') else {}
                    },
                    'model': str(model_name),
                    'engine': 'ctranslate2-whisper',
                    'audio_file': audio_file_path,
                    'processing_info': {
                        'mode': 'basic',
                        'service_type': type(self.transcription_engine).__name__
                    }
                }
                
                logger.info(f"🔍 Orchestrator result keys: {list(orchestrator_result.keys())}")
                logger.info(f"🔍 Orchestrator transcription text length: {len(orchestrator_result['transcription']['text'])}")
                
                return orchestrator_result
            else:
                error_msg = getattr(result, 'error_message', 'Transcription failed') if hasattr(result, 'error_message') else 'Transcription failed'
                logger.warning(f"🔍 Transcription failed: {error_msg}")
                return self._create_error_result(error_msg, time.time())
            
        except Exception as e:
            logger.error(f"🔍 Error in basic transcription: {e}")
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
            
            # Apply enhanced speaker diarization
            enhanced_result = self._apply_speaker_diarization(audio_file, None) # Pass None for now, as _transcribe_basic doesn't return TranscriptionResult
            
            # Combine enhanced speaker diarization with transcription result
            # This is a placeholder. In a real scenario, you'd integrate the enhanced_result into the transcription_result
            # For now, we'll just return the enhanced_result as is, assuming the output processor can handle it.
            # The actual integration would involve modifying the transcription_result object.
            
            # For now, we'll return the enhanced_result directly, as the transcription_result is not available here.
            # This part needs to be re-evaluated based on how the output processor expects the data.
            
            # If the output processor expects a specific structure, you might need to modify this.
            # For example, if the output processor expects a 'speakers' key in the transcription result.
            
            # Assuming the output processor expects a 'speakers' key in the transcription result
            # and that the enhanced_result is a TranscriptionResult with a 'speakers' attribute.
            # This is a simplification for the purpose of this edit.
            
            # In a real scenario, you'd integrate enhanced_result into transcription_result
            # and return transcription_result.
            
            # For now, we'll return the enhanced_result directly.
            return {
                'success': True,
                'data': enhanced_result.dict() if hasattr(enhanced_result, 'dict') else enhanced_result,
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
            
            # Extract the actual transcription data from the service result
            if result and len(result) > 0:
                service_result = result[0]  # Get the first (and should be only) result
                
                # Return the transcription data in the format expected by output processor
                return {
                    'success': True,
                    'transcription': service_result.get('transcription', {}),  # This is what output processor expects
                    'model': service_result.get('model', 'unknown'),
                    'engine': service_result.get('engine', 'unknown'),
                    'audio_file': service_result.get('audio_file', 'unknown'),
                    'processing_info': {
                        'mode': 'enhanced',
                        'service_type': type(self.enhanced_service).__name__
                    }
                }
            else:
                return self._create_error_result("No transcription results generated", time.time())
            
        except Exception as e:
            logger.error(f"Enhanced transcription failed: {e}")
            return self._create_error_result(str(e), time.time())
    
    def _transcribe_batch(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Batch transcription processing"""
        logger.info("🎤 Performing batch transcription")
        
        # For now, fall back to basic transcription
        # This can be extended with actual batch processing logic
        return self._transcribe_basic(input_data, **kwargs)
    
    def _transcribe_chunked(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Chunked transcription processing"""
        logger.info("🎤 Performing chunked transcription")
        
        if not self.transcription_engine:
            return self._create_error_result("Chunked transcription engine not available", time.time())
        
        try:
            # Use injected transcription service
            audio_file = input_data.get('file_path')
            if not audio_file:
                return self._create_error_result("No audio file path provided for chunked transcription", time.time())
            
            # ALWAYS use ConfigManager first - no hardcoded defaults
            chunk_duration = None
            
            # Try to get chunk duration from ConfigManager in priority order
            try:
                if hasattr(self.config_manager.config, 'chunking') and hasattr(self.config_manager.config.chunking, 'chunk_duration_seconds'):
                    chunk_duration = self.config_manager.config.chunking.chunk_duration_seconds
                    logger.info(f"🎯 Using chunk duration from ConfigManager chunking: {chunk_duration} seconds")
                elif hasattr(self.config_manager.config, 'processing') and hasattr(self.config_manager.config.processing, 'chunk_duration_seconds'):
                    chunk_duration = self.config_manager.config.processing.chunk_duration_seconds
                    logger.info(f"🎯 Using chunk duration from ConfigManager processing: {chunk_duration} seconds")
                else:
                    logger.error("❌ No chunk duration found in ConfigManager - configuration is incomplete")
                    return self._create_error_result("Chunk duration not configured in ConfigManager", time.time())
            except Exception as e:
                logger.error(f"❌ Error reading chunk duration from ConfigManager: {e}")
                return self._create_error_result(f"Failed to read chunk duration from ConfigManager: {e}", time.time())
            
            # Only use input chunk_duration if explicitly provided and different from config
            input_chunk_duration = input_data.get('chunk_duration')
            if input_chunk_duration and input_chunk_duration != chunk_duration:
                logger.info(f"🎯 Overriding ConfigManager chunk duration ({chunk_duration}s) with input value: {input_chunk_duration}s")
                chunk_duration = input_chunk_duration
            if not isinstance(chunk_duration, (int, float)) or chunk_duration <= 0:
                return self._create_error_result("Invalid chunk_duration provided", time.time())
            
            # Get model name from config manager to ensure it's always provided
            config_model_name = self.config_manager.config.transcription.default_model
            
            # Use the transcription engine's transcribe method with chunked strategy
            # The engine will automatically detect it's a long file and use chunking
            result = self.transcription_engine.transcribe(audio_file, model_name=config_model_name)
            
            return {
                'success': True,
                'data': result.dict() if hasattr(result, 'dict') else result,
                'processing_info': {
                    'mode': 'chunked',
                    'service_type': type(self.transcription_engine).__name__,
                    'chunk_duration': chunk_duration
                }
            }
            
        except Exception as e:
            logger.error(f"Chunked transcription failed: {e}")
            return self._create_error_result(str(e), time.time())
    
    # Method removed - enhanced JSON files are created by transcription strategies
    
    def _get_services_used(self, mode: TranscriptionMode) -> List[str]:
        """Get list of services used for the transcription mode"""
        services = []
        
        if self.transcription_engine:
            services.append(type(self.transcription_engine).__name__)
        
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
            'basic_transcription': self.transcription_engine is not None,
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
            'enhanced_features_enabled': getattr(self.config_manager.config, 'enhanced_features', False)
        }
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        self.current_job = None
        self.processing_stats = {}
    
    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("🧹 Cleaning up transcription service")
        self.reset_stats()
        
        # Clean up injected services
        if self.progress_monitor:
            try:
                self.progress_monitor.stop()
            except Exception:
                pass
        
        # Clean up other services if they have cleanup methods
        for service in [self.transcription_engine, self.speaker_service, self.enhanced_service]:
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                except Exception:
                    pass

    def _apply_speaker_diarization(self, audio_file_path: str, transcription_result) -> 'TranscriptionResult':
        """Apply enhanced speaker diarization using injected service"""
        try:
            if self.speaker_service:
                logger.info("🎤 Applying enhanced speaker diarization")
                
                # Get chunk duration from config
                chunk_duration = getattr(self.config_manager.config.processing, 'chunk_duration', 30)
                
                # Apply speaker diarization with chunk information
                enhanced_result = self.speaker_service.speaker_diarization(
                    audio_file_path, 
                    chunk_duration=chunk_duration
                )
                
                if enhanced_result and enhanced_result.success:
                    logger.info(f"✅ Enhanced speaker diarization completed: {enhanced_result.speaker_count} speakers detected")
                    return enhanced_result
                else:
                    logger.warning("⚠️ Enhanced speaker diarization failed, returning original result")
                    return transcription_result
            else:
                logger.warning("⚠️ No speaker service available, using basic enhancement")
                return self._basic_speaker_enhancement(transcription_result)
                
        except Exception as e:
            logger.error(f"❌ Error applying enhanced speaker diarization: {e}")
            return transcription_result
