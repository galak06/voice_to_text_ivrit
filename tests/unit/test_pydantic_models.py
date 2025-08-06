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