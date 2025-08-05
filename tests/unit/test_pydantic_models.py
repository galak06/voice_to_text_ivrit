#!/usr/bin/env python3
"""
Unit tests for Pydantic configuration models
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models import (
    Environment,
    TranscriptionConfig,
    SpeakerConfig,
    BatchConfig,
    DockerConfig,
    RunPodConfig,
    OutputConfig,
    SystemConfig,
    InputConfig,
    AppConfig
)


class TestPydanticModels(unittest.TestCase):
    """Test cases for Pydantic configuration models"""
    
    def test_environment_enum(self):
        """Test Environment enum values"""
        self.assertEqual(Environment.BASE, "base")
        self.assertEqual(Environment.DEVELOPMENT, "development")
        self.assertEqual(Environment.PRODUCTION, "production")
    
    def test_transcription_config_defaults(self):
        """Test TranscriptionConfig with default values"""
        config = TranscriptionConfig()
        
        self.assertEqual(config.default_model, "base")
        self.assertEqual(config.fallback_model, "tiny")
        self.assertEqual(config.default_engine, "speaker-diarization")
        self.assertEqual(config.beam_size, 5)
        self.assertEqual(config.language, "he")
        self.assertTrue(config.word_timestamps)
        self.assertTrue(config.vad_enabled)
        self.assertEqual(config.vad_min_silence_duration_ms, 500)
        self.assertIsNotNone(config.available_models)
        self.assertIsNotNone(config.available_engines)
    
    def test_transcription_config_validation(self):
        """Test TranscriptionConfig field validation"""
        # Test valid values
        config = TranscriptionConfig(beam_size=3, language="en")
        self.assertEqual(config.beam_size, 3)
        self.assertEqual(config.language, "en")
        
        # Test invalid beam_size (should raise validation error)
        with self.assertRaises(Exception):
            TranscriptionConfig(beam_size=15)  # Should be <= 10
    
    def test_speaker_config_defaults(self):
        """Test SpeakerConfig with default values"""
        config = SpeakerConfig()
        
        self.assertEqual(config.min_speakers, 1)
        self.assertEqual(config.max_speakers, 4)
        self.assertEqual(config.silence_threshold, 2.0)
        self.assertTrue(config.vad_enabled)
        self.assertTrue(config.word_timestamps)
        self.assertEqual(config.language, "he")
        self.assertEqual(config.beam_size, 5)
        self.assertEqual(config.vad_min_silence_duration_ms, 500)
        self.assertIsNotNone(config.presets)
    
    def test_batch_config_defaults(self):
        """Test BatchConfig with default values"""
        config = BatchConfig()
        
        self.assertTrue(config.enabled)
        self.assertFalse(config.parallel_processing)
        self.assertEqual(config.max_workers, 1)
        self.assertEqual(config.delay_between_files, 0)
        self.assertTrue(config.progress_tracking)
        self.assertTrue(config.continue_on_error)
        self.assertEqual(config.timeout_per_file, 600)
        self.assertTrue(config.retry_failed_files)
        self.assertEqual(config.max_retries, 3)
    
    def test_docker_config_defaults(self):
        """Test DockerConfig with default values"""
        config = DockerConfig()
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.image_name, "whisper-runpod-serverless")
        self.assertEqual(config.tag, "latest")
        self.assertEqual(config.container_name_prefix, "whisper-batch")
        self.assertTrue(config.auto_cleanup)
        self.assertEqual(config.timeout_seconds, 3600)
        self.assertEqual(config.memory_limit, "4g")
        self.assertEqual(config.cpu_limit, "2")
        self.assertTrue(config.kill_existing_containers)
        self.assertTrue(config.detached_mode)
    
    def test_runpod_config_defaults(self):
        """Test RunPodConfig with default values"""
        config = RunPodConfig()
        
        self.assertIsNone(config.api_key)
        self.assertIsNone(config.endpoint_id)
        self.assertEqual(config.max_payload_size, 200 * 1024 * 1024)
        self.assertTrue(config.streaming_enabled)
        self.assertEqual(config.in_queue_timeout, 300)
        self.assertEqual(config.max_stream_timeouts, 5)
        self.assertEqual(config.max_payload_len, 10 * 1024 * 1024)
        self.assertFalse(config.enabled)
        self.assertTrue(config.serverless_mode)
        self.assertTrue(config.auto_scale)
    
    def test_output_config_defaults(self):
        """Test OutputConfig with default values"""
        config = OutputConfig()
        
        self.assertEqual(config.output_dir, "output/transcriptions")
        self.assertEqual(config.logs_dir, "output/logs")
        self.assertEqual(config.transcriptions_dir, "output/transcriptions")
        self.assertEqual(config.temp_dir, "output/temp")
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.log_file, "transcription.log")
        self.assertTrue(config.save_json)
        self.assertTrue(config.save_txt)
        self.assertTrue(config.save_docx)
        self.assertTrue(config.cleanup_temp_files)
        self.assertEqual(config.temp_file_retention_hours, 24)
        self.assertTrue(config.auto_organize)
        self.assertTrue(config.include_metadata)
        self.assertTrue(config.include_timestamps)
    
    def test_system_config_defaults(self):
        """Test SystemConfig with default values"""
        config = SystemConfig()
        
        self.assertFalse(config.debug)
        self.assertFalse(config.dev_mode)
        self.assertIsNone(config.hugging_face_token)
        self.assertEqual(config.timeout_seconds, 300)
        self.assertEqual(config.retry_attempts, 3)
        self.assertTrue(config.auto_cleanup)
        self.assertTrue(config.session_management)
        self.assertTrue(config.error_reporting)
    
    def test_input_config_defaults(self):
        """Test InputConfig with default values"""
        config = InputConfig()
        
        self.assertEqual(config.directory, "examples/audio/voice")
        self.assertIsNotNone(config.supported_formats)
        self.assertTrue(config.recursive_search)
        self.assertEqual(config.max_file_size_mb, 100)
        self.assertTrue(config.validate_files)
        self.assertTrue(config.auto_discover)
    
    def test_app_config_defaults(self):
        """Test AppConfig with default values"""
        config = AppConfig()
        
        self.assertEqual(config.environment, Environment.BASE)
        self.assertIsNotNone(config.transcription)
        self.assertIsNotNone(config.speaker)
        self.assertIsNotNone(config.batch)
        self.assertIsNotNone(config.docker)
        self.assertIsNotNone(config.runpod)
        self.assertIsNotNone(config.output)
        self.assertIsNotNone(config.system)
        self.assertIsNotNone(config.input)
    
    def test_app_config_custom_values(self):
        """Test AppConfig with custom values"""
        config = AppConfig(
            environment=Environment.PRODUCTION,
            transcription=TranscriptionConfig(default_model="large"),
            speaker=SpeakerConfig(min_speakers=2, max_speakers=6)
        )
        
        self.assertEqual(config.environment, Environment.PRODUCTION)
        self.assertEqual(config.transcription.default_model, "large")
        self.assertEqual(config.speaker.min_speakers, 2)
        self.assertEqual(config.speaker.max_speakers, 6)
    
    def test_model_serialization(self):
        """Test model serialization to dict and JSON"""
        config = TranscriptionConfig(default_model="large", beam_size=7)
        
        # Test to dict
        config_dict = config.model_dump()
        self.assertEqual(config_dict["default_model"], "large")
        self.assertEqual(config_dict["beam_size"], 7)
        
        # Test to JSON
        config_json = config.model_dump_json()
        self.assertIn("large", config_json)
        self.assertIn("7", config_json)


if __name__ == '__main__':
    unittest.main() 