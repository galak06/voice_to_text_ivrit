"""
Unit tests for ResultBuilder class
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from src.core.logic.result_builder import ResultBuilder


class TestResultBuilder:
    """Test cases for ResultBuilder class"""
    
    def test_init(self):
        """Test ResultBuilder initialization"""
        builder = ResultBuilder()
        assert builder._result == {}
        assert isinstance(builder._timestamp, str)
    
    def test_fluent_interface(self):
        """Test fluent interface method chaining"""
        result = (ResultBuilder()
                 .success(True)
                 .error("test error")
                 .file_path("/test/path")
                 .build())
        
        assert result['success'] is True
        assert result['error'] == "test error"
        assert result['file_path'] == "/test/path"
        assert 'timestamp' in result
    
    def test_success_method(self):
        """Test success method"""
        result = ResultBuilder().success(True).build()
        assert result['success'] is True
        
        result = ResultBuilder().success(False).build()
        assert result['success'] is False
    
    def test_error_method(self):
        """Test error method"""
        result = ResultBuilder().error("test error").build()
        assert result['error'] == "test error"
    
    def test_file_methods(self):
        """Test file-related methods"""
        result = (ResultBuilder()
                 .file_path("/test/file.mp3")
                 .file_name("file.mp3")
                 .file_size(1024)
                 .file_format(".mp3")
                 .build())
        
        assert result['file_path'] == "/test/file.mp3"
        assert result['file_name'] == "file.mp3"
        assert result['file_size'] == 1024
        assert result['file_format'] == ".mp3"
    
    def test_data_methods(self):
        """Test data and metadata methods"""
        data = {"key": "value"}
        metadata = {"meta": "data"}
        
        result = (ResultBuilder()
                 .data(data)
                 .metadata(metadata)
                 .build())
        
        assert result['data'] == data
        assert result['metadata'] == metadata
    
    def test_validation_method(self):
        """Test validation method"""
        validation = {"valid": True, "checks": ["format", "size"]}
        
        result = ResultBuilder().validation(validation).build()
        assert result['validation'] == validation
    
    def test_output_methods(self):
        """Test output-related methods"""
        output_files = {"json": "/path/file.json", "txt": "/path/file.txt"}
        formats = ["json", "txt"]
        
        result = (ResultBuilder()
                 .output_files(output_files)
                 .formats_generated(formats)
                 .build())
        
        assert result['output_files'] == output_files
        assert result['formats_generated'] == formats
    
    def test_session_methods(self):
        """Test session and timestamp methods"""
        session_id = "session_123"
        custom_timestamp = "2023-01-01T00:00:00"
        
        result = (ResultBuilder()
                 .session_id(session_id)
                 .timestamp(custom_timestamp)
                 .build())
        
        assert result['session_id'] == session_id
        assert result['timestamp'] == custom_timestamp
    
    def test_batch_methods(self):
        """Test batch processing methods"""
        result = (ResultBuilder()
                 .total_files(10)
                 .successful_files(8)
                 .failed_files(2)
                 .success_rate(80.0)
                 .results([{"file": "test1.mp3", "success": True}])
                 .failed_files_details([{"file": "test2.mp3", "error": "format error"}])
                 .build())
        
        assert result['total_files'] == 10
        assert result['successful_files'] == 8
        assert result['failed_files'] == 2
        assert result['success_rate'] == 80.0
        assert len(result['results']) == 1
        assert len(result['failed_files_details']) == 1
    
    def test_add_custom_field(self):
        """Test adding custom fields"""
        result = (ResultBuilder()
                 .add_custom_field("custom_key", "custom_value")
                 .add_custom_field("number", 42)
                 .build())
        
        assert result['custom_key'] == "custom_value"
        assert result['number'] == 42
    
    def test_build_ensures_timestamp(self):
        """Test that build always includes timestamp"""
        result = ResultBuilder().build()
        assert 'timestamp' in result
        assert isinstance(result['timestamp'], str)
    
    def test_build_returns_copy(self):
        """Test that build returns a copy of the result"""
        builder = ResultBuilder().success(True)
        result1 = builder.build()
        result2 = builder.build()
        
        assert result1 == result2
        assert result1 is not result2  # Should be different objects
    
    def test_create_validation_success(self, tmp_path):
        """Test create_validation_success class method"""
        # Create a temporary file
        test_file = tmp_path / "test.mp3"
        test_file.write_text("test content")
        
        result = ResultBuilder.create_validation_success(test_file)
        
        assert result['success'] is True
        assert result['file_path'] == str(test_file)
        assert result['file_name'] == "test.mp3"
        assert result['file_size'] == len("test content")
        assert result['file_format'] == ".mp3"
        assert 'last_modified' in result
        assert 'timestamp' in result
    
    def test_create_validation_error(self):
        """Test create_validation_error class method"""
        error_message = "File not found"
        result = ResultBuilder.create_validation_error(error_message)
        
        assert result['success'] is False
        assert result['error'] == error_message
        assert 'timestamp' in result
    
    def test_create_batch_result(self):
        """Test create_batch_result class method"""
        result = ResultBuilder.create_batch_result(
            success=True,
            error="test error",
            total_files=5,
            session_id="session_123"
        )
        
        assert result['success'] is True
        assert result['error'] == "test error"
        assert result['total_files'] == 5
        assert result['session_id'] == "session_123"
        assert result['successful_files'] == 0
        assert result['failed_files'] == 5
        assert result['success_rate'] == 0.0
        assert result['results'] == []
        assert result['failed_files_details'] == []
        assert 'timestamp' in result
    
    def test_create_batch_result_no_error(self):
        """Test create_batch_result without error"""
        result = ResultBuilder.create_batch_result(
            success=True,
            total_files=3
        )
        
        assert result['success'] is True
        assert 'error' not in result
        assert result['total_files'] == 3
    
    def test_create_success_result(self):
        """Test create_success_result class method"""
        output_results = {"json": "/path/file.json", "txt": "/path/file.txt"}
        result = ResultBuilder.create_success_result(output_results)
        
        assert result['success'] is True
        assert result['output_files'] == output_results
        assert result['formats_generated'] == ["json", "txt"]
        assert 'timestamp' in result
    
    def test_create_failure_result(self):
        """Test create_failure_result class method"""
        error_message = "Processing failed"
        transcription_result = {"model": "whisper", "engine": "openai"}
        
        result = ResultBuilder.create_failure_result(error_message, transcription_result)
        
        assert result['success'] is False
        assert result['error'] == error_message
        assert result['transcription_result'] == transcription_result
        assert 'timestamp' in result
    
    def test_create_failure_result_no_transcription(self):
        """Test create_failure_result without transcription result"""
        error_message = "Processing failed"
        result = ResultBuilder.create_failure_result(error_message)
        
        assert result['success'] is False
        assert result['error'] == error_message
        assert 'transcription_result' not in result
        assert 'timestamp' in result
    
    def test_create_already_saved_result(self):
        """Test create_already_saved_result class method"""
        result = ResultBuilder.create_already_saved_result()
        
        assert result['success'] is True
        assert result['message'] == "Transcription service already saved output, skipping duplicate save"
        assert 'timestamp' in result
    
    def test_complex_fluent_chain(self):
        """Test complex fluent method chaining"""
        result = (ResultBuilder()
                 .success(True)
                 .file_path("/audio/test.mp3")
                 .file_name("test.mp3")
                 .file_size(1024000)
                 .file_format(".mp3")
                 .data({"duration": 120, "channels": 2})
                 .metadata({"processed_at": "2023-01-01", "version": "1.0"})
                 .session_id("session_456")
                 .add_custom_field("processing_time", 5.2)
                 .build())
        
        assert result['success'] is True
        assert result['file_path'] == "/audio/test.mp3"
        assert result['file_name'] == "test.mp3"
        assert result['file_size'] == 1024000
        assert result['file_format'] == ".mp3"
        assert result['data']['duration'] == 120
        assert result['data']['channels'] == 2
        assert result['metadata']['processed_at'] == "2023-01-01"
        assert result['metadata']['version'] == "1.0"
        assert result['session_id'] == "session_456"
        assert result['processing_time'] == 5.2
        assert 'timestamp' in result
