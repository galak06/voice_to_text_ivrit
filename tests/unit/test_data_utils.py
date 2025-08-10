#!/usr/bin/env python3
"""
Unit tests for DataUtils
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.output_data.utils.data_utils import DataUtils


class TestDataUtils(unittest.TestCase):
    """Test DataUtils functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_utils = DataUtils()
    
    def test_extract_speakers_data_from_string_content(self):
        """Test extracting speakers data from string content representation"""
        # Simulate the actual data structure from the JSON file
        data = {
            "content": "[{'id': 1, 'seek': 0, 'start': 0.0, 'end': 5.32, 'text': 'Test Hebrew text', 'speaker': 'Speaker 1'}, {'id': 2, 'seek': 0, 'start': 5.32, 'end': 10.0, 'text': 'More Hebrew text', 'speaker': 'Speaker 2'}]"
        }
        
        result = self.data_utils.extract_speakers_data(data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('Speaker 1', result)
        self.assertIn('Speaker 2', result)
        self.assertEqual(len(result['Speaker 1']), 1)
        self.assertEqual(len(result['Speaker 2']), 1)
        self.assertEqual(result['Speaker 1'][0]['text'], 'Test Hebrew text')
        self.assertEqual(result['Speaker 2'][0]['text'], 'More Hebrew text')
    
    def test_extract_text_content_from_string_content(self):
        """Test extracting text content from string content representation"""
        # Simulate the actual data structure from the JSON file
        data = {
            "content": "[{'id': 1, 'seek': 0, 'start': 0.0, 'end': 5.32, 'text': 'Test Hebrew text', 'speaker': 'Speaker 1'}, {'id': 2, 'seek': 0, 'start': 5.32, 'end': 10.0, 'text': 'More Hebrew text', 'speaker': 'Speaker 2'}]"
        }
        
        result = self.data_utils.extract_text_content(data)
        
        self.assertIsInstance(result, str)
        self.assertIn('Test Hebrew text', result)
        self.assertIn('More Hebrew text', result)
    
    def test_extract_speakers_data_from_list(self):
        """Test extracting speakers data from list format"""
        data = [
            {'text': 'Test transcription', 'start': 0, 'end': 1, 'speaker': 'Speaker 1'},
            {'text': 'Another segment', 'start': 1, 'end': 2, 'speaker': 'Speaker 2'}
        ]
        
        result = self.data_utils.extract_speakers_data(data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('Speaker 1', result)
        self.assertIn('Speaker 2', result)
        self.assertEqual(len(result['Speaker 1']), 1)
        self.assertEqual(len(result['Speaker 2']), 1)
    
    def test_extract_text_content_from_list(self):
        """Test extracting text content from list format"""
        data = [
            {'text': 'Test transcription', 'start': 0, 'end': 1},
            {'text': 'Another segment', 'start': 1, 'end': 2}
        ]
        
        result = self.data_utils.extract_text_content(data)
        
        self.assertIsInstance(result, str)
        self.assertIn('Test transcription', result)
        self.assertIn('Another segment', result)
    
    def test_extract_speakers_data_from_dict_with_speakers(self):
        """Test extracting speakers data from dict with speakers field"""
        data = {
            'speakers': {
                'Speaker 1': [{'text': 'Test', 'start': 0, 'end': 1}],
                'Speaker 2': [{'text': 'Another', 'start': 1, 'end': 2}]
            }
        }
        
        result = self.data_utils.extract_speakers_data(data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('Speaker 1', result)
        self.assertIn('Speaker 2', result)
    
    def test_extract_speakers_data_from_dict_with_segments(self):
        """Test extracting speakers data from dict with segments field"""
        data = {
            'segments': [
                {'text': 'Test', 'start': 0, 'end': 1, 'speaker': 'Speaker 1'},
                {'text': 'Another', 'start': 1, 'end': 2, 'speaker': 'Speaker 2'}
            ]
        }
        
        result = self.data_utils.extract_speakers_data(data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('Speaker 1', result)
        self.assertIn('Speaker 2', result)
    
    def test_extract_text_content_from_dict_with_text_field(self):
        """Test extracting text content from dict with text field"""
        data = {
            'text': 'Simple text transcription'
        }
        
        result = self.data_utils.extract_text_content(data)
        
        self.assertEqual(result, 'Simple text transcription')
    
    def test_extract_speakers_data_empty_result(self):
        """Test extracting speakers data returns empty dict for invalid data"""
        invalid_data = "not a list or dict"
        
        result = self.data_utils.extract_speakers_data(invalid_data)
        
        self.assertEqual(result, {})
    
    def test_extract_text_content_fallback(self):
        """Test extracting text content fallback for invalid data"""
        invalid_data = 123
        
        result = self.data_utils.extract_text_content(invalid_data)
        
        self.assertEqual(result, "")
    
    def test_extract_speakers_data_invalid_string_content(self):
        """Test extracting speakers data with invalid string content"""
        data = {
            "content": "invalid python literal"
        }
        
        result = self.data_utils.extract_speakers_data(data)
        
        self.assertEqual(result, {})
    
    def test_extract_text_content_invalid_string_content(self):
        """Test extracting text content with invalid string content"""
        data = {
            "content": "invalid python literal"
        }
        
        result = self.data_utils.extract_text_content(data)
        
        self.assertEqual(result, "invalid python literal")


if __name__ == '__main__':
    unittest.main() 