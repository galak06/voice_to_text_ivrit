"""
Unit tests for the unified FileValidator
Tests all validation scenarios and edge cases
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.logic.file_validator import FileValidator
from src.core.factories.file_validator_factory import FileValidatorFactory
from src.models import AppConfig


class TestFileValidator:
    """Test cases for the unified FileValidator"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock AppConfig for testing"""
        config = Mock(spec=AppConfig)
        config.runpod = Mock()
        config.runpod.max_payload_size = 100 * 1024 * 1024  # 100MB
        config.input = Mock()
        config.input.supported_formats = None
        return config
    
    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'dummy audio content')
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.fixture
    def temp_large_file(self):
        """Create a temporary large file for testing size limits"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Create a file larger than the limit
            f.write(b'x' * (101 * 1024 * 1024))  # 101MB
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_validate_existing_file(self, mock_config, temp_audio_file):
        """Test validation of an existing file"""
        validator = FileValidator(mock_config)
        result = validator.validate(temp_audio_file)
        
        assert result['valid'] is True
        assert result['file_path'] == temp_audio_file
        assert result['file_name'] == Path(temp_audio_file).name
        assert result['file_size'] > 0
        assert result['file_format'] == '.wav'
        assert result['is_readable'] is True
    
    def test_validate_nonexistent_file(self, mock_config):
        """Test validation of a non-existent file"""
        validator = FileValidator(mock_config)
        result = validator.validate('/nonexistent/file.wav')
        
        assert result['valid'] is False
        assert 'not exist' in result['error']
    
    def test_validate_directory(self, mock_config):
        """Test validation of a directory (should fail)"""
        validator = FileValidator(mock_config)
        result = validator.validate('/tmp')
        
        assert result['valid'] is False
        assert 'not a file' in result['error']
    
    def test_validate_empty_file(self, mock_config):
        """Test validation of an empty file"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            empty_file = f.name
        
        try:
            validator = FileValidator(mock_config)
            result = validator.validate(empty_file)
            
            assert result['valid'] is False
            assert 'empty' in result['error']
        finally:
            if os.path.exists(empty_file):
                os.unlink(empty_file)
    
    def test_validate_audio_file_success(self, mock_config, temp_audio_file):
        """Test audio-specific validation of a valid audio file"""
        validator = FileValidator(mock_config)
        result = validator.validate_audio_file(temp_audio_file)
        
        assert result['valid'] is True
        assert result['file_path'] == temp_audio_file
        assert result['file_format'] == '.wav'
    
    def test_validate_audio_file_wrong_format(self, mock_config):
        """Test audio-specific validation with wrong format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'dummy content')
            text_file = f.name
        
        try:
            validator = FileValidator(mock_config)
            result = validator.validate_audio_file(text_file)
            
            assert result['valid'] is False
            assert 'Unsupported audio format' in result['error']
        finally:
            if os.path.exists(text_file):
                os.unlink(text_file)
    
    def test_validate_file_size_limit(self, mock_config, temp_large_file):
        """Test file size validation with RunPod limits"""
        validator = FileValidator(mock_config)
        result = validator.validate_audio_file(temp_large_file)
        
        assert result['valid'] is False
        assert 'too large' in result['error']
        assert 'RunPod' in result['error']
    
    def test_validate_file_exists(self, mock_config, temp_audio_file):
        """Test simple existence check"""
        validator = FileValidator(mock_config)
        
        # Test existing file
        result = validator.validate_file_exists(temp_audio_file)
        assert result is None
        
        # Test non-existing file
        result = validator.validate_file_exists('/nonexistent/file.wav')
        assert 'not found' in result
    
    def test_validate_file_size(self, mock_config, temp_audio_file):
        """Test file size validation"""
        validator = FileValidator(mock_config)
        
        # Test valid file size
        result = validator.validate_file_size(temp_audio_file, max_size_bytes=1024*1024)
        assert result is None
        
        # Test file too large
        result = validator.validate_file_size(temp_audio_file, max_size_bytes=1)
        assert 'too large' in result
    
    def test_validate_file_format(self, mock_config, temp_audio_file):
        """Test file format validation"""
        validator = FileValidator(mock_config)
        
        # Test valid format
        result = validator.validate_file_format(temp_audio_file)
        assert result is None
        
        # Test invalid format
        result = validator.validate_file_format(temp_audio_file, allowed_formats={'.mp3'})
        assert 'Unsupported file format' in result
    
    def test_add_remove_supported_formats(self, mock_config):
        """Test adding and removing supported formats"""
        validator = FileValidator(mock_config)
        
        # Test adding format
        validator.add_supported_format('.mp4')
        assert '.mp4' in validator.supported_formats
        
        # Test removing format
        validator.remove_supported_format('.mp4')
        assert '.mp4' not in validator.supported_formats
    
    def test_get_supported_formats(self, mock_config):
        """Test getting supported formats"""
        validator = FileValidator(mock_config)
        formats = validator.get_supported_formats()
        
        assert isinstance(formats, list)
        assert '.wav' in formats
        assert '.mp3' in formats
    
    def test_validate_multiple_files(self, mock_config, temp_audio_file):
        """Test validation of multiple files"""
        validator = FileValidator(mock_config)
        
        # Create another temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'dummy content')
            temp_file2 = f.name
        
        try:
            results = validator.validate_multiple_files([temp_audio_file, temp_file2, '/nonexistent/file.wav'])
            
            assert results['valid'] is False
            assert results['total_files'] == 3
            assert results['valid_files'] == 2
            assert results['invalid_files'] == 1
            assert len(results['errors']) == 1
        finally:
            if os.path.exists(temp_file2):
                os.unlink(temp_file2)
    
    def test_config_supported_formats(self, mock_config):
        """Test that supported formats are loaded from config"""
        mock_config.input.supported_formats = ['.mp4', '.avi']
        
        validator = FileValidator(mock_config)
        assert '.mp4' in validator.supported_formats
        assert '.avi' in validator.supported_formats
        assert '.wav' not in validator.supported_formats  # Should be overridden


class TestFileValidatorFactory:
    """Test cases for the FileValidatorFactory"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock AppConfig for testing"""
        return Mock(spec=AppConfig)
    
    def test_create_audio_validator(self, mock_config):
        """Test creating an audio validator"""
        validator = FileValidatorFactory.create_audio_validator(mock_config)
        
        assert isinstance(validator, FileValidator)
        assert '.wav' in validator.supported_formats
        assert '.mp3' in validator.supported_formats
        assert '.webm' in validator.supported_formats
    
    def test_create_video_validator(self, mock_config):
        """Test creating a video validator"""
        validator = FileValidatorFactory.create_video_validator(mock_config)
        
        assert isinstance(validator, FileValidator)
        assert '.mp4' in validator.supported_formats
        assert '.avi' in validator.supported_formats
        assert '.wav' not in validator.supported_formats
    
    def test_create_document_validator(self, mock_config):
        """Test creating a document validator"""
        validator = FileValidatorFactory.create_document_validator(mock_config)
        
        assert isinstance(validator, FileValidator)
        assert '.pdf' in validator.supported_formats
        assert '.doc' in validator.supported_formats
        assert '.wav' not in validator.supported_formats
    
    def test_create_custom_validator(self, mock_config):
        """Test creating a custom validator"""
        custom_formats = {'.xyz', '.abc'}
        validator = FileValidatorFactory.create_custom_validator(mock_config, custom_formats)
        
        assert isinstance(validator, FileValidator)
        assert '.xyz' in validator.supported_formats
        assert '.abc' in validator.supported_formats
        assert '.wav' not in validator.supported_formats
    
    def test_create_general_validator(self, mock_config):
        """Test creating a general validator"""
        validator = FileValidatorFactory.create_general_validator(mock_config)
        
        assert isinstance(validator, FileValidator)
        # Should have default audio formats
        assert '.wav' in validator.supported_formats
        assert '.mp3' in validator.supported_formats
