#!/usr/bin/env python3
"""
Unit tests for InputProcessor
Tests file discovery, validation, and processing functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.input_processor import InputProcessor
from src.output_data import OutputManager


class TestInputProcessor(unittest.TestCase):
    """Test cases for InputProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test audio files
        self.test_files = []
        for i, ext in enumerate(['.wav', '.mp3', '.m4a', '.flac']):
            test_file = Path(self.temp_dir) / f"test_audio_{i}{ext}"
            test_file.write_text("fake audio content")
            self.test_files.append(str(test_file))
        
        # Create a non-audio file
        self.non_audio_file = Path(self.temp_dir) / "test.txt"
        self.non_audio_file.write_text("text content")
        
        # Mock configuration and output manager
        self.mock_config = Mock()
        self.mock_output_manager = Mock(spec=OutputManager)
        
        # Initialize processor
        self.processor = InputProcessor(self.mock_config, self.mock_output_manager)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test InputProcessor initialization"""
        self.assertIsNotNone(self.processor.config)
        self.assertIsNotNone(self.processor.output_manager)
        self.assertIsNotNone(self.processor.supported_formats)
        self.assertIsInstance(self.processor.supported_formats, set)
        
        # Check default supported formats
        expected_formats = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
        self.assertEqual(self.processor.supported_formats, expected_formats)
    
    def test_discover_files_success(self):
        """Test successful file discovery"""
        files = self.processor.discover_files(self.temp_dir)
        
        # Should find all audio files
        self.assertEqual(len(files), 4)
        
        # Check that all discovered files are in our test files
        for file_path in files:
            self.assertIn(file_path, self.test_files)
        
        # Should not include non-audio files
        self.assertNotIn(str(self.non_audio_file), files)
    
    def test_discover_files_empty_directory(self):
        """Test file discovery in empty directory"""
        empty_dir = tempfile.mkdtemp()
        try:
            files = self.processor.discover_files(empty_dir)
            self.assertEqual(len(files), 0)
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_discover_files_nonexistent_directory(self):
        """Test file discovery with nonexistent directory"""
        files = self.processor.discover_files("/nonexistent/directory")
        self.assertEqual(len(files), 0)
    
    def test_discover_files_file_path(self):
        """Test file discovery with file path instead of directory"""
        files = self.processor.discover_files(self.test_files[0])
        self.assertEqual(len(files), 0)
    
    def test_validate_file_success(self):
        """Test successful file validation"""
        test_file = self.test_files[0]
        result = self.processor.validate_file(test_file)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_path'], test_file)
        self.assertEqual(result['file_name'], Path(test_file).name)
        self.assertGreater(result['file_size'], 0)
        self.assertEqual(result['file_format'], '.wav')
        self.assertIn('last_modified', result)
    
    def test_validate_file_nonexistent(self):
        """Test file validation with nonexistent file"""
        result = self.processor.validate_file("/nonexistent/file.wav")
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        self.assertIn('File does not exist', result['error'])
    
    def test_validate_file_directory(self):
        """Test file validation with directory path"""
        result = self.processor.validate_file(self.temp_dir)
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        self.assertIn('Path is not a file', result['error'])
    
    def test_validate_file_unsupported_format(self):
        """Test file validation with unsupported format"""
        result = self.processor.validate_file(str(self.non_audio_file))
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        self.assertIn('Unsupported file format', result['error'])
    
    def test_validate_file_empty(self):
        """Test file validation with empty file"""
        empty_file = Path(self.temp_dir) / "empty.wav"
        empty_file.write_text("")
        
        result = self.processor.validate_file(str(empty_file))
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        self.assertIn('File is empty', result['error'])
    
    @patch('builtins.open')
    def test_validate_file_unreadable(self, mock_open):
        """Test file validation with unreadable file"""
        mock_open.side_effect = PermissionError("Permission denied")
        
        result = self.processor.validate_file(self.test_files[0])
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        self.assertIn('File is not readable', result['error'])
    
    def test_process_input_success(self):
        """Test successful input processing"""
        test_file = self.test_files[0]
        result = self.processor.process_input(test_file)
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertIn('metadata', result)
        self.assertIn('validation', result)
        
        # Check data structure
        data = result['data']
        self.assertEqual(data['file_path'], test_file)
        self.assertEqual(data['file_name'], Path(test_file).name)
        self.assertGreater(data['file_size'], 0)
        self.assertEqual(data['file_format'], '.wav')
        
        # Check metadata structure
        metadata = result['metadata']
        self.assertEqual(metadata['file_name'], Path(test_file).name)
        self.assertGreater(metadata['file_size'], 0)
        self.assertEqual(metadata['file_format'], '.wav')
        self.assertIn('last_modified', metadata)
        self.assertIn('processing_timestamp', metadata)
        
        # Check validation result
        validation = result['validation']
        self.assertTrue(validation['valid'])
    
    def test_process_input_failure(self):
        """Test input processing failure"""
        result = self.processor.process_input("/nonexistent/file.wav")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('File does not exist', result['error'])
        self.assertEqual(result['file_path'], "/nonexistent/file.wav")
    
    def test_get_supported_formats(self):
        """Test getting supported formats"""
        formats = self.processor.get_supported_formats()
        
        self.assertIsInstance(formats, list)
        self.assertEqual(len(formats), len(self.processor.supported_formats))
        
        # Check that all formats are strings starting with '.'
        for fmt in formats:
            self.assertIsInstance(fmt, str)
            self.assertTrue(fmt.startswith('.'))
    
    def test_add_supported_format(self):
        """Test adding supported format"""
        initial_count = len(self.processor.supported_formats)
        
        # Add new format
        self.processor.add_supported_format('.mp4')
        
        self.assertEqual(len(self.processor.supported_formats), initial_count + 1)
        self.assertIn('.mp4', self.processor.supported_formats)
    
    def test_add_supported_format_invalid(self):
        """Test adding invalid format"""
        initial_count = len(self.processor.supported_formats)
        
        # Try to add format without dot
        self.processor.add_supported_format('mp4')
        
        # Should not be added
        self.assertEqual(len(self.processor.supported_formats), initial_count)
        self.assertNotIn('mp4', self.processor.supported_formats)
    
    def test_remove_supported_format(self):
        """Test removing supported format"""
        # Add format first
        self.processor.add_supported_format('.mp4')
        self.assertIn('.mp4', self.processor.supported_formats)
        
        # Remove format
        self.processor.remove_supported_format('.mp4')
        
        self.assertNotIn('.mp4', self.processor.supported_formats)
    
    def test_remove_supported_format_nonexistent(self):
        """Test removing nonexistent format"""
        initial_count = len(self.processor.supported_formats)
        
        # Try to remove format that doesn't exist
        self.processor.remove_supported_format('.nonexistent')
        
        # Count should remain the same
        self.assertEqual(len(self.processor.supported_formats), initial_count)
    
    def test_extract_metadata(self):
        """Test metadata extraction"""
        validation_result = {
            'valid': True,
            'file_path': '/path/to/file.wav',
            'file_name': 'file.wav',
            'file_size': 1024,
            'file_format': '.wav',
            'last_modified': '2023-01-01T00:00:00'
        }
        
        metadata = self.processor._extract_metadata(validation_result)
        
        self.assertEqual(metadata['file_name'], 'file.wav')
        self.assertEqual(metadata['file_size'], 1024)
        self.assertEqual(metadata['file_format'], '.wav')
        self.assertEqual(metadata['last_modified'], '2023-01-01T00:00:00')
        self.assertIn('processing_timestamp', metadata)


if __name__ == '__main__':
    unittest.main() 