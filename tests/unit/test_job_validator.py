#!/usr/bin/env python3
"""
Unit tests for JobValidator
Tests the job validation functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logic.job_validator import JobValidator


class TestJobValidator(unittest.TestCase):
    """Test cases for JobValidator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock configuration
        self.mock_config = Mock()
        self.mock_config.transcription = Mock()
        self.mock_config.transcription.default_model = "base"
        self.mock_config.transcription.default_engine = "speaker-diarization"
        self.mock_config.transcription.supported_models = ["base", "small", "medium", "large"]
        self.mock_config.transcription.supported_engines = ["speaker-diarization", "custom-whisper", "stable-whisper"]
        
        # Initialize job validator instance
        self.validator = JobValidator(self.mock_config)
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test job validator initialization"""
        self.assertIsNotNone(self.validator)
        self.assertTrue(hasattr(self.validator, 'validate_job_input'))
        self.assertTrue(hasattr(self.validator, 'validate_audio_file'))
        self.assertTrue(hasattr(self.validator, 'validate_model_name'))
    
    def test_validate_job_input_success(self):
        """Test successful job input validation"""
        job_data = {
            'input': {
                'type': 'file',
                'engine': 'speaker-diarization'
            }
        }
        
        result = self.validator.validate_job_input(job_data)
        
        self.assertIsNone(result)  # No error means validation passed
    
    def test_validate_job_input_missing_datatype(self):
        """Test job input validation with missing datatype"""
        job_data = {
            'input': {
                'engine': 'speaker-diarization'
                # Missing type
            }
        }
        
        result = self.validator.validate_job_input(job_data)
        
        self.assertIsNotNone(result)
        self.assertIn('datatype field not provided', result)
    
    def test_validate_job_input_invalid_datatype(self):
        """Test job input validation with invalid datatype"""
        job_data = {
            'input': {
                'type': 'invalid-type',
                'engine': 'speaker-diarization'
            }
        }
        
        result = self.validator.validate_job_input(job_data)
        
        self.assertIsNotNone(result)
        self.assertIn('datatype should be', result)
    
    def test_validate_job_input_invalid_engine(self):
        """Test job input validation with invalid engine"""
        job_data = {
            'input': {
                'type': 'file',
                'engine': 'invalid-engine'
            }
        }
        
        result = self.validator.validate_job_input(job_data)
        
        self.assertIsNotNone(result)
        self.assertIn('engine should be', result)
    
    def test_validate_audio_file_success(self):
        """Test audio file validation success"""
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'test audio content')
            temp_file = f.name
        
        try:
            result = self.validator.validate_audio_file(temp_file)
            self.assertIsNone(result)  # No error means validation passed
        finally:
            import os
            os.unlink(temp_file)
    
    def test_validate_audio_file_not_found(self):
        """Test audio file validation with non-existent file"""
        result = self.validator.validate_audio_file('/nonexistent/file.wav')
        
        self.assertIsNotNone(result)
        self.assertIn('Audio file not found', result)
    
    def test_validate_audio_file_empty(self):
        """Test audio file validation with empty file"""
        # Create a temporary empty file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name  # Empty file
        
        try:
            result = self.validator.validate_audio_file(temp_file)
            self.assertIsNotNone(result)
            self.assertIn('Audio file is empty', result)
        finally:
            import os
            os.unlink(temp_file)
    
    def test_validate_model_name_success(self):
        """Test model name validation success"""
        result = self.validator.validate_model_name('base')
        self.assertIsNone(result)  # No error means validation passed
    
    def test_validate_model_name_empty(self):
        """Test model name validation with empty string"""
        result = self.validator.validate_model_name('')
        self.assertIsNotNone(result)
        self.assertIn('Model name is required', result)
    
    def test_validate_model_name_none(self):
        """Test model name validation with None"""
        result = self.validator.validate_model_name(None)
        self.assertIsNotNone(result)
        self.assertIn('Model name is required', result)
    
    def test_validate_model_name_not_string(self):
        """Test model name validation with non-string input"""
        result = self.validator.validate_model_name(123)
        self.assertIsNotNone(result)
        self.assertIn('Model name must be a string', result)
    
    def test_validate_audio_file_none(self):
        """Test audio file validation with None"""
        result = self.validator.validate_audio_file(None)
        
        self.assertIsNotNone(result)
        self.assertIn('No audio file specified', result)


if __name__ == '__main__':
    unittest.main()
