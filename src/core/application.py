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
from src.utils.output_manager import OutputManager


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
            base_output_dir=self.config.output.output_dir,
            run_session_id=self.current_session_id
        )
        
        # Initialize specialized processors
        self.input_processor = InputProcessor(self.config, self.output_manager)
        self.output_processor = OutputProcessor(self.config, self.output_manager)
        self.transcription_orchestrator = TranscriptionOrchestrator(
            self.config, 
            self.output_manager
        )
        
        # Setup logging
        self._setup_logging()
        
        # Application state
        self.processing_stats: Dict[str, Any] = {}
    
    def _ensure_config_initialized(self):
        """Ensure all configuration sections are properly initialized"""
        from src.utils.config_manager import (
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
        self.logger = logging.getLogger('transcription-app')
        self.logger.info(f"🚀 Transcription Application Started: {self._generate_session_id()}")
    
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
            self.logger.info(f"🎤 Processing single file: {audio_file_path}")
            
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
            
            self.logger.info(f"✅ Single file processing completed: {audio_file_path}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"❌ Error processing single file {audio_file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': audio_file_path,
                'timestamp': datetime.now().isoformat()
            }
    
    def process_batch(self, input_directory: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Process multiple audio files in batch
        
        Args:
            input_directory: Directory containing audio files (uses config if None)
            **kwargs: Additional parameters for transcription
            
        Returns:
            Dictionary containing batch processing results
        """
        try:
            self.logger.info("🔄 Starting batch processing")
            
            # Discover input files - use config input directory if available
            if input_directory is None:
                # At this point, config.input is guaranteed to be initialized
                assert self.config.input is not None, "Input configuration must be initialized"
                input_dir = self.config.input.directory
            else:
                input_dir = input_directory
                
            input_files = self.input_processor.discover_files(input_dir)
            
            if not input_files:
                return {
                    'success': False,
                    'error': f"No audio files found in {input_dir}",
                    'timestamp': datetime.now().isoformat()
                }
            
            self.logger.info(f"📁 Found {len(input_files)} files to process")
            
            # Process each file
            results = []
            successful_count = 0
            failed_count = 0
            
            for i, audio_file in enumerate(input_files, 1):
                self.logger.info(f"📝 Processing {i}/{len(input_files)}: {audio_file}")
                
                result = self.process_single_file(audio_file, **kwargs)
                results.append(result)
                
                if result['success']:
                    successful_count += 1
                else:
                    failed_count += 1
            
            # Compile batch results
            batch_result = {
                'success': True,
                'total_files': len(input_files),
                'successful': successful_count,
                'failed': failed_count,
                'results': results,
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Batch processing completed: {successful_count}/{len(input_files)} successful")
            return batch_result
            
        except Exception as e:
            self.logger.error(f"❌ Error in batch processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current application status
        
        Returns:
            Dictionary containing application status information
        """
        return {
            'session_id': self.current_session_id,
            'config_loaded': self.config is not None,
            'output_manager_ready': hasattr(self, 'output_manager'),
            'input_processor_ready': hasattr(self, 'input_processor'),
            'output_processor_ready': hasattr(self, 'output_processor'),
            'transcription_orchestrator_ready': hasattr(self, 'transcription_orchestrator'),
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Cleanup application resources"""
        try:
            self.logger.info("🧹 Cleaning up application resources")
            
            # Cleanup temporary files
            if hasattr(self, 'output_manager'):
                self.output_manager.cleanup_temp_files()
            
            # Cleanup transcription orchestrator
            if hasattr(self, 'transcription_orchestrator'):
                self.transcription_orchestrator.cleanup()
            
            self.logger.info("✅ Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup() 