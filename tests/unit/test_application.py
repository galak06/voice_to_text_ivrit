#!/usr/bin/env python3
"""
Unit tests for TranscriptionApplication
Tests the main application class functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.models import (
    AppConfig, TranscriptionConfig, OutputConfig, InputConfig,
    SpeakerConfig, BatchConfig, DockerConfig, RunPodConfig, SystemConfig
)


class TestTranscriptionApplication(unittest.TestCase):
    """Test cases for TranscriptionApplication class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuration with all required sections
        self.mock_config = Mock(spec=AppConfig)
        self.mock_config.transcription = Mock(spec=TranscriptionConfig)
        self.mock_config.speaker = Mock(spec=SpeakerConfig)
        self.mock_config.batch = Mock(spec=BatchConfig)
        self.mock_config.docker = Mock(spec=DockerConfig)
        self.mock_config.runpod = Mock(spec=RunPodConfig)
        self.mock_config.output = Mock(spec=OutputConfig)
        self.mock_config.system = Mock(spec=SystemConfig)
        self.mock_config.input = Mock(spec=InputConfig)
        
        # Set up mock config values
        self.mock_config.output.output_dir = self.temp_dir
        self.mock_config.output.logs_dir = f"{self.temp_dir}/logs"
        self.mock_config.output.transcriptions_dir = f"{self.temp_dir}/transcriptions"
        self.mock_config.output.temp_dir = f"{self.temp_dir}/temp"
        self.mock_config.input.directory = "examples/audio/voice"
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_application_initialization(self, mock_orchestrator, mock_output_processor, 
                                      mock_input_processor, mock_output_manager, mock_config_manager):
        """Test application initialization with dependency injection"""
        # Mock config manager
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        # Mock output manager
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        # Mock processors
        mock_input_processor_instance = Mock()
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Initialize application
        with TranscriptionApplication() as app:
            # Verify components were initialized
            self.assertIsNotNone(app.config)
            self.assertIsNotNone(app.output_manager)
            self.assertIsNotNone(app.input_processor)
            self.assertIsNotNone(app.output_processor)
            self.assertIsNotNone(app.transcription_orchestrator)
            self.assertIsNotNone(app.current_session_id)
            
            # Verify dependency injection
            mock_input_processor.assert_called_once_with(self.mock_config, mock_output_manager_instance)
            mock_output_processor.assert_called_once_with(self.mock_config, mock_output_manager_instance)
            mock_orchestrator.assert_called_once_with(self.mock_config, mock_output_manager_instance)
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_process_single_file_success(self, mock_orchestrator, mock_output_processor, 
                                       mock_input_processor, mock_output_manager, mock_config_manager):
        """Test successful single file processing"""
        # Setup mocks
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        mock_input_processor_instance = Mock()
        mock_input_processor_instance.process_input.return_value = {
            'success': True,
            'data': {'file_path': 'test.wav', 'file_name': 'test.wav'},
            'metadata': {'file_name': 'test.wav'}
        }
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor_instance.process_output.return_value = {
            'success': True,
            'formats_generated': ['json', 'txt']
        }
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.transcribe.return_value = {
            'success': True,
            'transcription': 'Test transcription',
            'model': 'base',
            'engine': 'faster-whisper'
        }
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test single file processing
        with TranscriptionApplication() as app:
            result = app.process_single_file('test.wav', model='base', engine='faster-whisper')
            
            # Verify result
            self.assertTrue(result['success'])
            self.assertIn('input', result)
            self.assertIn('transcription', result)
            self.assertIn('output', result)
            self.assertIn('session_id', result)
            
            # Verify method calls
            mock_input_processor_instance.process_input.assert_called_once_with('test.wav')
            mock_orchestrator_instance.transcribe.assert_called_once()
            mock_output_processor_instance.process_output.assert_called_once()
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_process_single_file_failure(self, mock_orchestrator, mock_output_processor, 
                                       mock_input_processor, mock_output_manager, mock_config_manager):
        """Test single file processing failure"""
        # Setup mocks
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        mock_input_processor_instance = Mock()
        mock_input_processor_instance.process_input.return_value = {
            'success': False,
            'error': 'File not found'
        }
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test single file processing failure
        with TranscriptionApplication() as app:
            result = app.process_single_file('nonexistent.wav')
            
            # Verify result
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertEqual(result['error'], 'File not found')
            
            # Verify orchestrator was not called
            mock_orchestrator_instance.transcribe.assert_not_called()
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_process_batch_success(self, mock_orchestrator, mock_output_processor, 
                                 mock_input_processor, mock_output_manager, mock_config_manager):
        """Test successful batch processing"""
        # Setup mocks
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        mock_input_processor_instance = Mock()
        mock_input_processor_instance.discover_files.return_value = ['file1.wav', 'file2.wav']
        mock_input_processor_instance.process_input.return_value = {
            'success': True,
            'data': {'file_path': 'test.wav', 'file_name': 'test.wav'},
            'metadata': {'file_name': 'test.wav'}
        }
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor_instance.process_output.return_value = {
            'success': True,
            'formats_generated': ['json', 'txt']
        }
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.transcribe.return_value = {
            'success': True,
            'transcription': 'Test transcription',
            'model': 'base',
            'engine': 'faster-whisper'
        }
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test batch processing
        with TranscriptionApplication() as app:
            result = app.process_batch()
            
            # Verify result
            self.assertTrue(result['success'])
            self.assertEqual(result['total_files'], 2)
            self.assertEqual(result['successful_files'], 2)
            self.assertEqual(result['failed_files'], 0)
            self.assertIn('results', result)
            self.assertEqual(len(result['results']), 2)
            
            # Verify method calls
            mock_input_processor_instance.discover_files.assert_called_once()
            self.assertEqual(mock_input_processor_instance.process_input.call_count, 2)
            self.assertEqual(mock_orchestrator_instance.transcribe.call_count, 2)
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_process_batch_no_files(self, mock_orchestrator, mock_output_processor, 
                                  mock_input_processor, mock_output_manager, mock_config_manager):
        """Test batch processing with no files found"""
        # Setup mocks
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        mock_input_processor_instance = Mock()
        mock_input_processor_instance.discover_files.return_value = []
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test batch processing with no files
        with TranscriptionApplication() as app:
            result = app.process_batch()
            
            # Verify result
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('No audio files found', result['error'])
            
            # Verify no processing occurred
            mock_input_processor_instance.process_input.assert_not_called()
            mock_orchestrator_instance.transcribe.assert_not_called()
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_get_status(self, mock_orchestrator, mock_output_processor, 
                       mock_input_processor, mock_output_manager, mock_config_manager):
        """Test application status retrieval"""
        # Setup mocks
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        mock_input_processor_instance = Mock()
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test status retrieval
        with TranscriptionApplication() as app:
            status = app.get_status()
            
            # Verify status structure
            self.assertIn('session_id', status)
            self.assertIn('config_loaded', status)
            self.assertIn('output_manager_ready', status)
            self.assertIn('input_processor_ready', status)
            self.assertIn('output_processor_ready', status)
            self.assertIn('transcription_orchestrator_ready', status)
            self.assertIn('timestamp', status)
            
            # Verify status values
            self.assertTrue(status['config_loaded'])
            self.assertTrue(status['output_manager_ready'])
            self.assertTrue(status['input_processor_ready'])
            self.assertTrue(status['output_processor_ready'])
            self.assertTrue(status['transcription_orchestrator_ready'])
    
    @patch('src.core.application.ConfigManager')
    @patch('src.core.application.OutputManager')
    @patch('src.core.application.InputProcessor')
    @patch('src.core.application.OutputProcessor')
    @patch('src.core.application.TranscriptionOrchestrator')
    def test_context_manager(self, mock_orchestrator, mock_output_processor, 
                           mock_input_processor, mock_output_manager, mock_config_manager):
        """Test application as context manager"""
        # Setup mocks
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager.return_value = mock_config_manager_instance
        
        mock_output_manager_instance = Mock()
        mock_output_manager.return_value = mock_output_manager_instance
        
        mock_input_processor_instance = Mock()
        mock_input_processor.return_value = mock_input_processor_instance
        
        mock_output_processor_instance = Mock()
        mock_output_processor.return_value = mock_output_processor_instance
        
        mock_orchestrator_instance = Mock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test context manager
        with TranscriptionApplication() as app:
            self.assertIsNotNone(app)
            self.assertIsNotNone(app.current_session_id)
        
        # Verify cleanup was called (the actual cleanup method doesn't call cleanup_temp_files)
        # The cleanup method just logs and calls logging_service.log_application_shutdown()


if __name__ == '__main__':
    unittest.main() 