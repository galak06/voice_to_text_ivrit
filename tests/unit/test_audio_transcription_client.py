#!/usr/bin/env python3
"""
Unit tests for AudioTranscriptionClient
Tests the client for sending audio files to RunPod endpoint for transcription
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

from src.clients.audio_transcription_client import AudioTranscriptionClient
from src.models import TranscriptionRequest, TranscriptionResult, AppConfig


class TestAudioTranscriptionClient(unittest.TestCase):
    """Test cases for AudioTranscriptionClient class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Patch ConfigManager used inside the client to provide a mock with .config
        self.config_manager_patcher = patch('src.clients.audio_transcription_client.ConfigManager')
        MockConfigManager = self.config_manager_patcher.start()
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuration
        self.mock_config = Mock(spec=AppConfig)
        self.mock_config.runpod = Mock()
        self.mock_config.runpod.api_key = "test_api_key"
        self.mock_config.runpod.endpoint_id = "test_endpoint_id"
        self.mock_config.runpod.enabled = True
        self.mock_config.runpod.serverless_mode = False
        self.mock_config.runpod.streaming_enabled = False
        
        # Mock dependencies
        self.mock_endpoint_factory = Mock()
        self.mock_file_validator = Mock()
        self.mock_payload_builder = Mock()
        self.mock_result_collector = Mock()
        self.mock_output_saver = Mock()
        self.mock_result_display = Mock()
        self.mock_parameter_provider = Mock()
        self.mock_queue_waiter = Mock()
        self.mock_data_utils = Mock()
        
        # Ensure the patched ConfigManager returns a mock with a valid .config and validate()
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.config = self.mock_config
        mock_config_manager_instance.validate.return_value = True
        MockConfigManager.return_value = mock_config_manager_instance

        # Initialize client with mocked dependencies
        self.client = AudioTranscriptionClient(
            config=self.mock_config,
            endpoint_factory=self.mock_endpoint_factory,
            file_validator=self.mock_file_validator,
            payload_builder=self.mock_payload_builder,
            result_collector=self.mock_result_collector,
            output_saver=self.mock_output_saver,
            result_display=self.mock_result_display,
            parameter_provider=self.mock_parameter_provider,
            queue_waiter=self.mock_queue_waiter,
            data_utils=self.mock_data_utils
        )
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.config_manager_patcher.stop()
    
    def test_initialization(self):
        """Test client initialization with dependency injection"""
        self.assertIsNotNone(self.client.config)
        self.assertIsNotNone(self.client.endpoint_factory)
        self.assertIsNotNone(self.client.file_validator)
        self.assertIsNotNone(self.client.payload_builder)
        self.assertIsNotNone(self.client.result_collector)
        self.assertIsNotNone(self.client.output_saver)
        self.assertIsNotNone(self.client.result_display)
        self.assertIsNotNone(self.client.parameter_provider)
        self.assertIsNotNone(self.client.queue_waiter)
    
    def test_initialization_with_defaults(self):
        """Test client initialization with default dependencies"""
        # Test initialization without providing dependencies
        with patch('src.clients.audio_transcription_client.ConfigManager') as mock_config_manager:
            mock_config_manager_instance = Mock()
            mock_config_manager_instance.config = self.mock_config
            mock_config_manager_instance.validate.return_value = True
            mock_config_manager.return_value = mock_config_manager_instance
            
            client = AudioTranscriptionClient()
            
            self.assertIsNotNone(client.config)
            self.assertIsNotNone(client.endpoint_factory)
            self.assertIsNotNone(client.file_validator)
            self.assertIsNotNone(client.payload_builder)
            self.assertIsNotNone(client.result_collector)
            self.assertIsNotNone(client.output_saver)
            self.assertIsNotNone(client.result_display)
            self.assertIsNotNone(client.parameter_provider)
            self.assertIsNotNone(client.queue_waiter)
    
    def test_transcribe_audio_success(self):
        """Test successful audio transcription"""
        audio_file_path = "/test/audio.wav"
        model = "base"
        engine = "speaker-diarization"
        
        # Mock file validation
        file_info = {
            'file_path': audio_file_path,
            'file_name': 'audio.wav',
            'file_size': 1024,
            'duration': 60.0
        }
        self.mock_file_validator.validate_file.return_value = file_info
        
        # Mock parameter provider
        params = {
            'model': model,
            'engine': engine,
            'language': 'he'
        }
        self.mock_parameter_provider.get_parameters.return_value = params
        
        # Mock payload builder
        request = TranscriptionRequest(
            audio_file_path=audio_file_path,
            model=model,
            engine=engine,
            parameters=params
        )
        self.mock_payload_builder.build_request.return_value = request
        
        # Mock result collector
        result = TranscriptionResult(
            success=True,
            transcription="Test transcription",
            processing_time=10.5,
            segments=[],
            speakers={}
        )
        self.mock_result_collector.collect_result.return_value = result
        
        # Mock output saver
        saved_files = {
            'json': '/test/output.json',
            'txt': '/test/output.txt'
        }
        self.mock_output_saver.save_output.return_value = saved_files
        
        # Mock endpoint
        mock_endpoint = Mock()
        self.mock_endpoint_factory.create_endpoint.return_value = mock_endpoint
        
        # Execute transcription
        success = self.client.transcribe_audio(audio_file_path, model, engine)
        
        # Verify success
        self.assertTrue(success)
        
        # Verify method calls
        self.mock_file_validator.validate_file.assert_called_once_with(audio_file_path)
        self.mock_parameter_provider.get_parameters.assert_called_once_with(model, engine)
        self.mock_payload_builder.build_request.assert_called_once_with(file_info, model, engine, params)
        self.mock_result_collector.collect_result.assert_called_once()
        self.mock_output_saver.save_output.assert_called_once_with(result, audio_file_path)
    
    def test_transcribe_audio_validation_failure(self):
        """Test audio transcription with validation failure"""
        audio_file_path = "/test/audio.wav"
        
        # Mock file validation failure
        self.mock_file_validator.validate_file.return_value = None
        
        # Execute transcription
        success = self.client.transcribe_audio(audio_file_path)
        
        # Verify failure occurred
        self.assertFalse(success)
    
    def test_transcribe_audio_parameter_failure(self):
        """Test audio transcription with parameter failure"""
        audio_file_path = "/test/audio.wav"
        
        # Mock file validation success
        file_info = {
            'file_path': audio_file_path,
            'file_name': 'audio.wav',
            'file_size': 1024,
            'duration': 60.0
        }
        self.mock_file_validator.validate_file.return_value = file_info
        
        # Mock parameter provider failure
        self.mock_parameter_provider.get_parameters.return_value = None
        
        # Execute transcription
        success = self.client.transcribe_audio(audio_file_path)
        
        # Verify failure occurred
        self.assertFalse(success)
    
    def test_transcribe_audio_payload_failure(self):
        """Test audio transcription with payload building failure"""
        audio_file_path = "/test/audio.wav"
        
        # Mock file validation success
        file_info = {
            'file_path': audio_file_path,
            'file_name': 'audio.wav',
            'file_size': 1024,
            'duration': 60.0
        }
        self.mock_file_validator.validate_file.return_value = file_info
        
        # Mock parameter provider success
        params = {
            'model': 'base',
            'engine': 'speaker-diarization',
            'language': 'he'
        }
        self.mock_parameter_provider.get_parameters.return_value = params
        
        # Mock payload builder failure
        self.mock_payload_builder.build_request.return_value = None
        
        # Execute transcription
        success = self.client.transcribe_audio(audio_file_path)
        
        # Verify failure occurred
        self.assertFalse(success)
    
    def test_transcribe_audio_execution_failure(self):
        """Test audio transcription with execution failure"""
        audio_file_path = "/test/audio.wav"
        
        # Mock file validation success
        file_info = {
            'file_path': audio_file_path,
            'file_name': 'audio.wav',
            'file_size': 1024,
            'duration': 60.0
        }
        self.mock_file_validator.validate_file.return_value = file_info
        
        # Mock parameter provider success
        params = {
            'model': 'base',
            'engine': 'speaker-diarization',
            'language': 'he'
        }
        self.mock_parameter_provider.get_parameters.return_value = params
        
        # Mock payload builder success
        request = TranscriptionRequest(
            audio_file_path=audio_file_path,
            model='base',
            engine='speaker-diarization',
            parameters=params
        )
        self.mock_payload_builder.build_request.return_value = request
        
        # Mock result collector failure
        result = TranscriptionResult(
            success=False,
            error="Test error",
            segments=[],
            speakers={}
        )
        self.mock_result_collector.collect_result.return_value = result
        
        # Mock endpoint
        mock_endpoint = Mock()
        self.mock_endpoint_factory.create_endpoint.return_value = mock_endpoint
        
        # Execute transcription
        success = self.client.transcribe_audio(audio_file_path)
        
        # Verify failure occurred
        self.assertFalse(success)
    
    # Removed tests that require an initialized RunPod endpoint to avoid external dependency
    
    def test_log_file_info(self):
        """Test logging file information"""
        file_info = {
            'path': '/test/audio.wav',
            'file_name': 'audio.wav',
            'size': 1024,
            'size_mb': 1.0,
            'duration': 60.0
        }
        
        # This should not raise any exceptions
        self.client._log_file_info(file_info)
    
    def test_log_parameters(self):
        """Test logging parameters"""
        params = {
            'model': 'base',
            'engine': 'speaker-diarization',
            'language': 'he'
        }
        
        # This should not raise any exceptions
        self.client._log_parameters(params)
    
    def test_log_saved_files(self):
        """Test logging saved files"""
        saved_files = {
            'json': '/test/output.json',
            'txt': '/test/output.txt'
        }
        
        # This should not raise any exceptions
        self.client._log_saved_files(saved_files)


if __name__ == '__main__':
    unittest.main()
