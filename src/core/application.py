"""
Main Application Class
Orchestrates the entire transcription process using dependency injection
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from datetime import datetime
import time

from src.core.input_processor import InputProcessor
from src.core.output_processor import OutputProcessor
from src.core.transcription_orchestrator import TranscriptionOrchestrator
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager
from src.logging import LoggingService
from src.clients.audio_transcription.audio_transcription_client import AudioTranscriptionClient
from src.utils.ui_manager import ApplicationUI
from src.core.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class TranscriptionApplication:
    """
    Main application class for voice-to-text transcription
    
    This class follows the Single Responsibility Principle by orchestrating
    the transcription process while delegating specific responsibilities
    to specialized components through dependency injection.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, config_path: Optional[str] = None, ui_manager: Optional[ApplicationUI] = None):
        """
        Initialize the transcription application
        
        Args:
            config_manager: Optional ConfigManager instance (creates default if None)
            config_path: Optional path to configuration file or directory (used if config_manager is None)
            ui_manager: Optional ApplicationUI instance (creates default if None)
        """
        # Initialize configuration first (dependency)
        if config_manager is not None:
            # Use provided ConfigManager
            self.config_manager = config_manager
        elif config_path:
            # Create ConfigManager with custom path
            config_path_obj = Path(config_path)
            if config_path_obj.is_file():
                # It's a file, use the parent directory
                config_dir = str(config_path_obj.parent)
            else:
                # It's a directory or doesn't exist, use as is
                config_dir = config_path
            self.config_manager = ConfigManager(config_dir)
        else:
            # Create default ConfigManager
            self.config_manager = ConfigManager()
        
        self.config = self.config_manager.config
        
        # Ensure configuration sections are initialized
        self._ensure_config_initialized()
        
        # Generate session ID
        self.current_session_id = self._generate_session_id()
        
        # Initialize core components with dependency injection
        # At this point, config.output is guaranteed to be initialized
        assert self.config.output is not None, "Output configuration must be initialized"
        
        # Create DataUtils instance for dependency injection
        from src.output_data.utils.data_utils import DataUtils
        data_utils = DataUtils()
        
        self.output_manager = OutputManager(
            output_base_path=self.config.output.output_dir,
            data_utils=data_utils
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
        
        # Application state and performance metrics
        self.processing_stats: Dict[str, Any] = {
            'total_files_processed': 0,
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'memory_usage': [],
            'cpu_usage': [],
            'start_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        # Performance monitoring
        self._performance_monitor = PerformanceMonitor()
        
        # Get logging service for application events
        self.logging_service = LoggingService(self.config_manager)
        
        # Initialize UI manager with dependency injection
        self.ui_manager = ui_manager or ApplicationUI(self.config_manager)
        
        # Initialize audio transcription client lazily (only when needed)
        self._audio_client = None
        
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
        start_time = time.time()
        
        try:
            logger.info(f"🎤 Processing single file: {audio_file_path}")
            
            # Measure performance before processing
            pre_metrics = self._performance_monitor.get_current_metrics()
            
            # Log processing start
            self.logging_service.log_processing_start(1, batch_mode=False)
            
            # Input processing
            input_result = self.input_processor.process_input(audio_file_path)
            if not input_result['success']:
                return input_result
            
            # Transcription orchestration
            transcription_result = self.transcription_orchestrator.transcribe(
                input_result['data'], 
                session_id=self.current_session_id,
                **kwargs
            )
            
            # Output processing
            output_result = self.output_processor.process_output(
                transcription_result,
                input_result['metadata']
            )
            
            # Measure performance after processing
            post_metrics = self._performance_monitor.get_current_metrics()
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update processing statistics
            self._update_processing_stats(processing_time, transcription_result['success'])
            
            # Compile final result
            final_result = {
                'success': True,
                'input': input_result,
                'transcription': transcription_result,
                'output': output_result,
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'performance_metrics': {
                    'pre_processing': pre_metrics,
                    'post_processing': post_metrics,
                    'memory_delta_mb': post_metrics.get('memory_mb', 0) - pre_metrics.get('memory_mb', 0)
                }
            }
            
            # Log processing completion
            self.logging_service.log_processing_complete(1, 1, batch_mode=False)
            
            # Log performance summary if processing took significant time
            if processing_time > 30:  # Log for files taking more than 30 seconds
                logger.info(f"📊 File processing completed in {processing_time:.1f}s")
                self._performance_monitor.log_performance_summary()
            
            return final_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing file {audio_file_path}: {e}")
            self.logging_service.log_error(e, f"process_single_file: {audio_file_path}")
            
            # Update statistics even for failed processing
            self._update_processing_stats(processing_time, False)
            
            return {
                'success': False,
                'error': str(e),
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time
            }
    
    def _update_processing_stats(self, processing_time: float, success: bool):
        """Update processing statistics"""
        self.processing_stats['total_files_processed'] += 1
        self.processing_stats['total_processing_time'] += processing_time
        self.processing_stats['average_processing_time'] = (
            self.processing_stats['total_processing_time'] / self.processing_stats['total_files_processed']
        )
        self.processing_stats['last_activity'] = datetime.now().isoformat()
        
        if success:
            self.processing_stats['successful_transcriptions'] += 1
        else:
            self.processing_stats['failed_transcriptions'] += 1
        
        # Add current performance metrics to history
        current_metrics = self._performance_monitor.get_current_metrics()
        self.processing_stats['memory_usage'].append(current_metrics.get('memory_mb', 0))
        self.processing_stats['cpu_usage'].append(current_metrics.get('cpu_percent', 0))
        
        # Keep only last 100 measurements to prevent memory bloat
        if len(self.processing_stats['memory_usage']) > 100:
            self.processing_stats['memory_usage'] = self.processing_stats['memory_usage'][-100:]
        if len(self.processing_stats['cpu_usage']) > 100:
            self.processing_stats['cpu_usage'] = self.processing_stats['cpu_usage'][-100:]
    
    def process_batch(self, input_directory: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Process multiple audio files in batch mode with enhanced error recovery
        
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
            
            # Process each file with enhanced error handling
            results = []
            success_count = 0
            failed_files = []
            retry_queue = []
            
            # First pass: process all files
            for i, audio_file in enumerate(audio_files, 1):
                try:
                    logger.info(f"📊 Processing file {i}/{len(audio_files)}: {audio_file}")
                    
                    result = self.process_single_file(audio_file, **kwargs)
                    results.append(result)
                    
                    if result['success']:
                        success_count += 1
                        logger.info(f"✅ File {i}/{len(audio_files)} completed successfully")
                    else:
                        failed_files.append({
                            'file': audio_file,
                            'error': result.get('error', 'Unknown error'),
                            'attempt': 1
                        })
                        logger.warning(f"❌ File {i}/{len(audio_files)} failed: {result.get('error', 'Unknown error')}")
                        
                        # Add to retry queue if retries are enabled
                        if self.config.system and self.config.system.retry_attempts > 0:
                            retry_queue.append({
                                'file': audio_file,
                                'kwargs': kwargs,
                                'attempts': 0,
                                'max_attempts': self.config.system.retry_attempts
                            })
                
                except Exception as e:
                    logger.error(f"❌ Unexpected error processing {audio_file}: {e}")
                    self.logging_service.log_error(e, f"process_batch: {audio_file}")
                    
                    failed_files.append({
                        'file': audio_file,
                        'error': str(e),
                        'attempt': 1
                    })
                    
                    results.append({
                        'success': False,
                        'error': str(e),
                        'file': audio_file,
                        'session_id': self.current_session_id,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Second pass: retry failed files
            if retry_queue and self.config.system and self.config.system.retry_attempts > 0:
                logger.info(f"🔄 Retrying {len(retry_queue)} failed files...")
                
                for retry_item in retry_queue:
                    retry_item['attempts'] += 1
                    audio_file = retry_item['file']
                    
                    logger.info(f"🔄 Retry attempt {retry_item['attempts']}/{retry_item['max_attempts']} for {audio_file}")
                    
                    try:
                        # Add exponential backoff
                        if retry_item['attempts'] > 1:
                            backoff_time = min(2 ** (retry_item['attempts'] - 1), 30)  # Max 30 seconds
                            logger.info(f"⏳ Waiting {backoff_time} seconds before retry...")
                            import time
                            time.sleep(backoff_time)
                        
                        result = self.process_single_file(audio_file, **retry_item['kwargs'])
                        
                        if result['success']:
                            success_count += 1
                            logger.info(f"✅ Retry successful for {audio_file}")
                            
                            # Update the original result in results list
                            for i, original_result in enumerate(results):
                                if original_result.get('file') == audio_file:
                                    results[i] = result
                                    break
                            
                            # Remove from failed files
                            failed_files = [f for f in failed_files if f['file'] != audio_file]
                        else:
                            logger.warning(f"❌ Retry failed for {audio_file}: {result.get('error', 'Unknown error')}")
                            
                            # Update failed files list
                            for failed_file in failed_files:
                                if failed_file['file'] == audio_file:
                                    failed_file['attempt'] = retry_item['attempts']
                                    failed_file['error'] = result.get('error', 'Unknown error')
                                    break
                    
                    except Exception as e:
                        logger.error(f"❌ Retry attempt failed for {audio_file}: {e}")
                        
                        # Update failed files list
                        for failed_file in failed_files:
                            if failed_file['file'] == audio_file:
                                failed_file['attempt'] = retry_item['attempts']
                                failed_file['error'] = str(e)
                                break
            
            # Compile batch result with detailed statistics
            batch_result = {
                'success': success_count > 0,  # Consider batch successful if at least one file succeeded
                'total_files': len(audio_files),
                'successful_files': success_count,
                'failed_files': len(audio_files) - success_count,
                'success_rate': (success_count / len(audio_files)) * 100 if audio_files else 0,
                'results': results,
                'failed_files_details': failed_files,
                'retry_attempts': self.config.system.retry_attempts if self.config.system else 0,
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log detailed completion statistics
            logger.info(f"📊 BATCH PROCESSING COMPLETE:")
            logger.info(f"   - Total files: {len(audio_files)}")
            logger.info(f"   - Successful: {success_count}")
            logger.info(f"   - Failed: {len(audio_files) - success_count}")
            logger.info(f"   - Success rate: {batch_result['success_rate']:.1f}%")
            
            if failed_files:
                logger.warning(f"❌ Failed files:")
                for failed_file in failed_files:
                    logger.warning(f"   - {failed_file['file']}: {failed_file['error']} (attempts: {failed_file['attempt']})")
            
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
    
    def transcribe_with_runpod(self, audio_file_path: str, model: Optional[str] = None, 
                              engine: Optional[str] = None, save_output: bool = True) -> Dict[str, Any]:
        """
        Transcribe audio file using RunPod endpoint directly
        
        Args:
            audio_file_path: Path to the audio file
            model: Optional model to use for transcription
            engine: Optional engine to use for transcription
            save_output: Whether to save outputs in all formats
            
        Returns:
            Dictionary with transcription result
        """
        try:
            logger.info(f"🎤 Transcribing with RunPod: {audio_file_path}")
            
            # Check if AudioTranscriptionClient is available
            if self.audio_client is None:
                raise ImportError("RunPod module not available. Please install it with: pip install runpod")
            
            # Use the injected AudioTranscriptionClient
            success = self.audio_client.transcribe_audio(
                audio_file_path=audio_file_path,
                model=model,
                engine=engine,
                save_output=save_output
            )
            
            result = {
                'success': success,
                'file': audio_file_path,
                'method': 'runpod',
                'model': model,
                'engine': engine,
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                logger.info(f"✅ RunPod transcription completed: {audio_file_path}")
                self.logging_service.log_processing_complete(1, 1, batch_mode=False)
            else:
                logger.error(f"❌ RunPod transcription failed: {audio_file_path}")
                result['error'] = 'RunPod transcription failed'
                self.logging_service.log_error(Exception("RunPod transcription failed"), f"transcribe_with_runpod: {audio_file_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RunPod transcription: {e}")
            self.logging_service.log_error(e, f"transcribe_with_runpod: {audio_file_path}")
            return {
                'success': False,
                'error': str(e),
                'file': audio_file_path,
                'method': 'runpod',
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    @property
    def audio_client(self) -> Optional[AudioTranscriptionClient]:
        """Lazy-load AudioTranscriptionClient when needed"""
        if self._audio_client is None:
            try:
                # Get the DataUtils instance from OutputManager for injection
                data_utils = self.output_manager.data_utils if self.output_manager else None
                self._audio_client = AudioTranscriptionClient(
                    config=self.config,
                    data_utils=data_utils
                )
            except ImportError as e:
                # If RunPod is not available, log warning and return None
                logger.warning(f"RunPod not available: {e}")
                return None
        return self._audio_client
    
    def get_status(self) -> Dict[str, Any]:
        """Get current application status with performance metrics"""
        # Get performance report
        performance_report = self._performance_monitor.get_performance_report()
        
        return {
            'session_id': self.current_session_id,
            'config_loaded': self.config is not None,
            'output_manager_ready': self.output_manager is not None,
            'input_processor_ready': self.input_processor is not None,
            'output_processor_ready': self.output_processor is not None,
            'transcription_orchestrator_ready': self.transcription_orchestrator is not None,
            'audio_client_ready': self.audio_client is not None,
            'processing_stats': self.processing_stats,
            'performance_metrics': performance_report,
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Clean up any temporary resources
            logger.info("🧹 Cleaning up application resources")
            
            # Clean up performance monitor
            if hasattr(self, '_performance_monitor'):
                self._performance_monitor.cleanup()
            
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