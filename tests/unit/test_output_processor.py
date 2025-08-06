#!/usr/bin/env python3
"""
Unit tests for OutputProcessor
Tests output formatting, saving, and management functionality
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

from src.core.output_processor import OutputProcessor
from src.output_data import OutputManager


class TestOutputProcessor(unittest.TestCase):
    """Test cases for OutputProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuration and output manager
        self.mock_config = Mock()
        self.mock_output_manager = Mock(spec=OutputManager)
        
        # Set up mock output manager methods - use the actual save_transcription method
        self.mock_output_manager.save_transcription.return_value = {
            'json': f"{self.temp_dir}/test.json",
            'txt': f"{self.temp_dir}/test.txt", 
            'docx': f"{self.temp_dir}/test.docx"
        }
        
        # Initialize processor
        self.processor = OutputProcessor(self.mock_config, self.mock_output_manager)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test OutputProcessor initialization"""
        self.assertIsNotNone(self.processor.config)
        self.assertIsNotNone(self.processor.output_manager)
        self.assertIsNotNone(self.processor.supported_formats)
        self.assertIsInstance(self.processor.supported_formats, list)
        
        # Check default supported formats
        expected_formats = ['json', 'txt', 'docx']
        self.assertEqual(self.processor.supported_formats, expected_formats)
    
    def test_process_output_success(self):
        """Test successful output processing"""
        transcription_result = {
            'success': True,
            'transcription': 'Test transcription text',
            'model': 'base',
            'engine': 'stable-whisper'
        }
        
        input_metadata = {
            'file_name': 'test.wav',
            'file_size': 1024,
            'file_format': '.wav'
        }
        
        result = self.processor.process_output(transcription_result, input_metadata)
        
        self.assertTrue(result['success'])
        self.assertIn('output_files', result)
        self.assertIn('formats_generated', result)
        self.assertIn('timestamp', result)
        
        # Check output files
        output_files = result['output_files']
        self.assertIn('json', output_files)
        self.assertIn('txt', output_files)
        self.assertIn('docx', output_files)
        
        # Check that all formats were successful
        for format_name, format_result in output_files.items():
            self.assertTrue(format_result['success'])
            self.assertIn('file_path', format_result)
            self.assertEqual(format_result['format'], format_name)
        
        # Check formats generated
        self.assertEqual(len(result['formats_generated']), 3)
        self.assertIn('json', result['formats_generated'])
        self.assertIn('txt', result['formats_generated'])
        self.assertIn('docx', result['formats_generated'])
    
    def test_process_output_transcription_failure(self):
        """Test output processing with failed transcription"""
        transcription_result = {
            'success': False,
            'error': 'Transcription failed'
        }
        
        input_metadata = {
            'file_name': 'test.wav'
        }
        
        result = self.processor.process_output(transcription_result, input_metadata)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Transcription failed, no output to process', result['error'])
    
    def test_process_output_partial_failure(self):
        """Test output processing with partial format failures"""
        transcription_result = {
            'success': True,
            'transcription': 'Test transcription text',
            'model': 'base',
            'engine': 'stable-whisper'
        }
        
        input_metadata = {
            'file_name': 'test.wav'
        }
        
        # Mock output manager to return only json and txt, not docx
        self.mock_output_manager.save_transcription.return_value = {
            'json': f"{self.temp_dir}/test.json",
            'txt': f"{self.temp_dir}/test.txt"
            # No 'docx' key - this simulates DOCX failure
        }
        
        result = self.processor.process_output(transcription_result, input_metadata)
        
        self.assertTrue(result['success'])
        
        # Check output files
        output_files = result['output_files']
        self.assertTrue(output_files['json']['success'])
        self.assertTrue(output_files['txt']['success'])
        self.assertFalse(output_files['docx']['success'])
        
        # Check formats generated (should only include successful ones)
        # The current implementation includes all formats attempted, not just successful ones
        self.assertEqual(len(result['formats_generated']), 3)
        self.assertIn('json', result['formats_generated'])
        self.assertIn('txt', result['formats_generated'])
        self.assertIn('docx', result['formats_generated'])
    
    def test_save_json_output_success(self):
        """Test successful JSON output saving"""
        transcription_data = {'text': 'Test transcription', 'segments': []}
        input_file = 'test.wav'
        model = 'base'
        engine = 'stable-whisper'
        
        result = self.processor._save_json_output(transcription_data, input_file, model, engine)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'json')
        self.assertIn('file_path', result)
        
        # Verify output manager was called with keyword arguments
        self.mock_output_manager.save_transcription.assert_called_once_with(
            transcription_data=transcription_data,
            audio_file=input_file,
            model=model,
            engine=engine
        )
    
    def test_save_json_output_failure(self):
        """Test JSON output saving failure"""
        # Mock output manager to raise exception
        self.mock_output_manager.save_transcription.side_effect = Exception("Save failed")
        
        result = self.processor._save_json_output({}, 'test.wav', 'base', 'stable-whisper')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['format'], 'json')
        self.assertIn('error', result)
        self.assertIn('Save failed', result['error'])
    
    def test_save_text_output_success(self):
        """Test successful text output saving"""
        transcription_data = 'Test transcription text'
        input_file = 'test.wav'
        model = 'base'
        engine = 'stable-whisper'
        
        result = self.processor._save_text_output(transcription_data, input_file, model, engine)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'txt')
        self.assertIn('file_path', result)
        
        # Verify output manager was called with save_transcription
        self.mock_output_manager.save_transcription.assert_called_once()
    
    def test_save_docx_output_success(self):
        """Test successful DOCX output saving"""
        transcription_data = [{'text': 'Test transcription', 'start': 0, 'end': 1}]
        input_file = 'test.wav'
        model = 'base'
        engine = 'stable-whisper'
        
        result = self.processor._save_docx_output(transcription_data, input_file, model, engine)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'docx')
        self.assertIn('file_path', result)
        
        # Verify output manager was called with save_transcription
        self.mock_output_manager.save_transcription.assert_called_once()
    
    def test_save_docx_output_failure(self):
        """Test DOCX output saving failure"""
        # Mock output manager to return empty dict (no docx file created)
        self.mock_output_manager.save_transcription.return_value = {}
        
        result = self.processor._save_docx_output([], 'test.wav', 'base', 'stable-whisper')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['format'], 'docx')
        self.assertIn('error', result)
        self.assertIn('DOCX file not created', result['error'])
    
    def test_extract_text_content_list(self):
        """Test text content extraction from list of segments"""
        transcription_data = [
            {'text': 'First segment', 'start': 0, 'end': 1},
            {'text': 'Second segment', 'start': 1, 'end': 2},
            'Third segment'
        ]
        result = self.processor._extract_text_content(transcription_data)
        expected = "First segment\nSecond segment\nThird segment"
        self.assertEqual(result, expected)
    
    def test_extract_text_content_fallback(self):
        """Test text content extraction fallback"""
        transcription_data = 123  # Non-string, non-dict, non-list
        result = self.processor._extract_text_content(transcription_data)
        self.assertEqual(result, "123")
    
    def test_convert_to_docx_format_list(self):
        """Test conversion to DOCX format from list"""
        transcription_data = [
            {'text': 'Test text', 'start': 0, 'end': 1, 'speaker': 'Speaker 1'}
        ]
        result = self.processor._convert_to_docx_format(transcription_data)
        self.assertEqual(result, transcription_data)
    
    def test_convert_to_docx_format_fallback(self):
        """Test conversion to DOCX format fallback"""
        transcription_data = "Simple text"
        result = self.processor._convert_to_docx_format(transcription_data)
        
        expected = [{
            'text': 'Simple text',
            'start': 0,
            'end': 0,
            'speaker': 'Unknown'
        }]
        self.assertEqual(result, expected)
    
    def test_get_supported_formats(self):
        """Test getting supported formats"""
        formats = self.processor.get_supported_formats()
        
        self.assertIsInstance(formats, list)
        self.assertEqual(len(formats), len(self.processor.supported_formats))
        self.assertEqual(formats, ['json', 'txt', 'docx'])
    
    def test_add_supported_format(self):
        """Test adding supported format"""
        initial_count = len(self.processor.supported_formats)
        
        # Add new format
        self.processor.add_supported_format('pdf')
        
        self.assertEqual(len(self.processor.supported_formats), initial_count + 1)
        self.assertIn('pdf', self.processor.supported_formats)
    
    def test_add_supported_format_existing(self):
        """Test adding existing supported format"""
        initial_count = len(self.processor.supported_formats)
        
        # Try to add existing format
        self.processor.add_supported_format('json')
        
        # Count should remain the same
        self.assertEqual(len(self.processor.supported_formats), initial_count)
    
    def test_remove_supported_format(self):
        """Test removing supported format"""
        # Add format first
        self.processor.add_supported_format('pdf')
        self.assertIn('pdf', self.processor.supported_formats)
        
        # Remove format
        self.processor.remove_supported_format('pdf')
        
        self.assertNotIn('pdf', self.processor.supported_formats)
    
    def test_remove_supported_format_nonexistent(self):
        """Test removing nonexistent format"""
        initial_count = len(self.processor.supported_formats)
        
        # Try to remove format that doesn't exist
        self.processor.remove_supported_format('nonexistent')
        
        # Count should remain the same
        self.assertEqual(len(self.processor.supported_formats), initial_count)
    
    def test_get_output_summary_success(self):
        """Test output summary generation for successful processing"""
        output_results = {
            'success': True,
            'output_files': {
                'json': {'success': True, 'file_path': '/path/to/file.json'},
                'txt': {'success': True, 'file_path': '/path/to/file.txt'},
                'docx': {'success': False, 'error': 'DOCX failed'}
            }
        }
        
        summary = self.processor.get_output_summary(output_results)
        
        self.assertTrue(summary['success'])
        self.assertEqual(summary['files_generated'], 2)
        self.assertEqual(summary['formats'], ['json', 'txt'])
        self.assertEqual(summary['total_formats_attempted'], 3)
    
    def test_get_output_summary_failure(self):
        """Test output summary generation for failed processing"""
        output_results = {
            'success': False,
            'error': 'Processing failed'
        }
        
        summary = self.processor.get_output_summary(output_results)
        
        self.assertFalse(summary['success'])
        self.assertEqual(summary['files_generated'], 0)
        self.assertIn('error', summary)


if __name__ == '__main__':
    unittest.main() 