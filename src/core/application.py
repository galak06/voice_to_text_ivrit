"""
Main Application Class
Orchestrates the entire transcription process using dependency injection
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from datetime import datetime

from src.core.input_processor import InputProcessor
from src.core.output_processor import OutputProcessor
from src.core.transcription_orchestrator import TranscriptionOrchestrator
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager
from src.logging import LoggingService

logger = logging.getLogger(__name__)

class TranscriptionApplication:
    """
    Main application class for voice-to-text transcription
    
    This class follows the Single Responsibility Principle by orchestrating
    the transcription process while delegating specific responsibilities
    to specialized components through dependency injection.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the transcription application
        
        Args:
            config_path: Optional path to configuration file or directory
        """
        # Initialize configuration first (dependency)
        if config_path:
            # Check if it's a file or directory
            config_path_obj = Path(config_path)
            if config_path_obj.is_file():
                # It's a file, use the parent directory
                config_dir = str(config_path_obj.parent)
            else:
                # It's a directory or doesn't exist, use as is
                config_dir = config_path
            self.config_manager = ConfigManager(config_dir)
        else:
            self.config_manager = ConfigManager()
        
        self.config = self.config_manager.config
        
        # Ensure configuration sections are initialized
        self._ensure_config_initialized()
        
        # Generate session ID
        self.current_session_id = self._generate_session_id()
        
        # Initialize core components with dependency injection
        # At this point, config.output is guaranteed to be initialized
        assert self.config.output is not None, "Output configuration must be initialized"
        self.output_manager = OutputManager(
            output_base_path=self.config.output.output_dir
        )
        
        # Initialize specialized processors with ConfigManager injection
        self.input_processor = InputProcessor(self.config_manager, self.output_manager)
        self.output_processor = OutputProcessor(self.config_manager, self.output_manager)
        self.transcription_orchestrator = TranscriptionOrchestrator(
            self.config_manager, 
            self.output_manager
        )
        
        # Setup logging with ConfigManager
        self._setup_logging()
        
        # Application state
        self.processing_stats: Dict[str, Any] = {}
        
        # Get logging service for application events
        self.logging_service = LoggingService(self.config_manager)
        
        # Log application start
        self.logging_service.log_application_start()
        if config_path:
            self.logging_service.log_configuration_loaded(config_path)
    
    def _ensure_config_initialized(self):
        """Ensure all configuration sections are properly initialized"""
        from src.models import (
            TranscriptionConfig, SpeakerConfig, BatchConfig, 
            DockerConfig, RunPodConfig, OutputConfig, 
            SystemConfig, InputConfig
        )
        
        # Initialize any None configuration sections with defaults
        if self.config.transcription is None:
            self.config.transcription = TranscriptionConfig()
        if self.config.speaker is None:
            self.config.speaker = SpeakerConfig()
        if self.config.batch is None:
            self.config.batch = BatchConfig()
        if self.config.docker is None:
            self.config.docker = DockerConfig()
        if self.config.runpod is None:
            self.config.runpod = RunPodConfig()
        if self.config.output is None:
            self.config.output = OutputConfig()
        if self.config.system is None:
            self.config.system = SystemConfig()
        if self.config.input is None:
            self.config.input = InputConfig()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for this application run"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"
    
    def _setup_logging(self):
        """Setup application-level logging"""
        logger.info(f"🚀 Transcription Application Started: {self._generate_session_id()}")
    
    def process_single_file(self, audio_file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a single audio file through the complete pipeline
        
        Args:
            audio_file_path: Path to the audio file
            **kwargs: Additional parameters (model, engine, etc.)
            
        Returns:
            Dictionary containing processing results
        """
        try:
            logger.info(f"🎤 Processing single file: {audio_file_path}")
            
            # Log processing start
            self.logging_service.log_processing_start(1, batch_mode=False)
            
            # Input processing
            input_result = self.input_processor.process_input(audio_file_path)
            if not input_result['success']:
                return input_result
            
            # Transcription orchestration
            transcription_result = self.transcription_orchestrator.transcribe(
                input_result['data'], 
                **kwargs
            )
            
            # Output processing
            output_result = self.output_processor.process_output(
                transcription_result,
                input_result['metadata']
            )
            
            # Compile final result
            final_result = {
                'success': True,
                'input': input_result,
                'transcription': transcription_result,
                'output': output_result,
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log processing completion
            self.logging_service.log_processing_complete(1, 1, batch_mode=False)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing file {audio_file_path}: {e}")
            self.logging_service.log_error(e, f"process_single_file: {audio_file_path}")
            return {
                'success': False,
                'error': str(e),
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def process_batch(self, input_directory: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Process multiple audio files in batch mode
        
        Args:
            input_directory: Directory containing audio files
            **kwargs: Additional parameters (model, engine, etc.)
            
        Returns:
            Dictionary containing batch processing results
        """
        try:
            # Discover audio files
            if input_directory:
                audio_files = self.input_processor.discover_files(input_directory)
            else:
                # Use config input directory if available
                if self.config.input and self.config.input.directory:
                    audio_files = self.input_processor.discover_files(self.config.input.directory)
                else:
                    return {
                        'success': False,
                        'error': 'No input directory specified',
                        'session_id': self.current_session_id,
                        'timestamp': datetime.now().isoformat()
                    }
            
            if not audio_files:
                return {
                    'success': False,
                    'error': 'No audio files found',
                    'session_id': self.current_session_id,
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"🎤 Processing batch of {len(audio_files)} files")
            
            # Log processing start
            self.logging_service.log_processing_start(len(audio_files), batch_mode=True)
            
            # Process each file
            results = []
            success_count = 0
            
            for audio_file in audio_files:
                try:
                    result = self.process_single_file(audio_file, **kwargs)
                    results.append(result)
                    if result['success']:
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error processing {audio_file}: {e}")
                    self.logging_service.log_error(e, f"process_batch: {audio_file}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'file': audio_file,
                        'session_id': self.current_session_id,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Compile batch result
            batch_result = {
                'success': success_count > 0,
                'total_files': len(audio_files),
                'successful_files': success_count,
                'failed_files': len(audio_files) - success_count,
                'results': results,
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log processing completion
            self.logging_service.log_processing_complete(success_count, len(audio_files), batch_mode=True)
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            self.logging_service.log_error(e, "process_batch")
            return {
                'success': False,
                'error': str(e),
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current application status"""
        return {
            'session_id': self.current_session_id,
            'config_loaded': self.config is not None,
            'output_manager_ready': self.output_manager is not None,
            'input_processor_ready': self.input_processor is not None,
            'output_processor_ready': self.output_processor is not None,
            'transcription_orchestrator_ready': self.transcription_orchestrator is not None,
            'processing_stats': self.processing_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Clean up any temporary resources
            logger.info("🧹 Cleaning up application resources")
            
            # Log application shutdown
            self.logging_service.log_application_shutdown()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            self.logging_service.log_error(e, "cleanup")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup() 