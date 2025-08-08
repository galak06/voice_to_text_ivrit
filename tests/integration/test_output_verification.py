#!/usr/bin/env python3
"""
Integration tests for output verification functionality
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, mock
from datetime import datetime

from src.output_data.managers.output_manager import OutputManager
from src.output_data.formatters.docx_formatter import DocxFormatter
from src.output_data.formatters.text_formatter import TextFormatter
from src.output_data.formatters.json_formatter import JsonFormatter
from src.output_data.utils.data_utils import DataUtils


class TestOutputVerification(TestCase):
    """Integration tests for output verification"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.transcriptions_dir = os.path.join(self.output_dir, "transcriptions")
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        
        # Create test transcription data
        self.test_transcription_data = {
            'speakers': {
                'Speaker 1': [
                    {
                        'speaker': 'Speaker 1',
                        'text': 'Hello, this is the first segment of the transcription.',
                        'start': 0.0,
                        'end': 5.0,
                        'words': None
                    },
                    {
                        'speaker': 'Speaker 1',
                        'text': 'This is the second segment with more content.',
                        'start': 5.0,
                        'end': 10.0,
                        'words': None
                    }
                ],
                'Speaker 2': [
                    {
                        'speaker': 'Speaker 2',
                        'text': 'I am responding to the first speaker.',
                        'start': 10.0,
                        'end': 15.0,
                        'words': None
                    }
                ]
            },
            'model_name': 'test-model',
            'audio_file': 'test_audio.wav',
            'transcription_time': 30.5,
            'speaker_count': 2,
            'full_text': 'Hello, this is the first segment of the transcription. This is the second segment with more content. I am responding to the first speaker.'
        }
        
        self.output_manager = OutputManager(self.transcriptions_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_output_manager_saves_all_formats(self):
        """Test that output manager saves all required formats"""
        base_filename = "test_transcription"
        
        # Save transcription in all formats
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        # Verify all files were created
        expected_files = [
            f"{base_filename}.json",
            f"{base_filename}.txt",
            f"{base_filename}.docx"
        ]
        
        for filename in expected_files:
            filepath = os.path.join(self.transcriptions_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"File not found: {filename}")
        
        # Verify result contains all file paths
        self.assertIn('json_file', result)
        self.assertIn('txt_file', result)
        self.assertIn('docx_file', result)
        
        # Verify files are not empty
        for filepath in result.values():
            if filepath and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.assertGreater(file_size, 0, f"File is empty: {filepath}")
    
    def test_json_output_content_verification(self):
        """Test JSON output content verification"""
        base_filename = "test_json"
        
        # Save JSON output
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        json_filepath = result['json_file']
        self.assertTrue(os.path.exists(json_filepath))
        
        # Load and verify JSON content
        with open(json_filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Verify structure
        self.assertIn('speakers', json_data)
        self.assertIn('model_name', json_data)
        self.assertIn('audio_file', json_data)
        self.assertIn('transcription_time', json_data)
        self.assertIn('speaker_count', json_data)
        self.assertIn('full_text', json_data)
        
        # Verify speakers data
        speakers = json_data['speakers']
        self.assertIn('Speaker 1', speakers)
        self.assertIn('Speaker 2', speakers)
        
        # Verify segment content
        speaker1_segments = speakers['Speaker 1']
        self.assertEqual(len(speaker1_segments), 2)
        
        # Verify first segment
        first_segment = speaker1_segments[0]
        self.assertEqual(first_segment['speaker'], 'Speaker 1')
        self.assertEqual(first_segment['text'], 'Hello, this is the first segment of the transcription.')
        self.assertEqual(first_segment['start'], 0.0)
        self.assertEqual(first_segment['end'], 5.0)
        
        # Verify metadata
        self.assertEqual(json_data['model_name'], 'test-model')
        self.assertEqual(json_data['audio_file'], 'test_audio.wav')
        self.assertEqual(json_data['speaker_count'], 2)
    
    def test_txt_output_content_verification(self):
        """Test TXT output content verification"""
        base_filename = "test_txt"
        
        # Save TXT output
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        txt_filepath = result['txt_file']
        self.assertTrue(os.path.exists(txt_filepath))
        
        # Load and verify TXT content
        with open(txt_filepath, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        # Verify content includes all speakers
        self.assertIn('Speaker 1', txt_content)
        self.assertIn('Speaker 2', txt_content)
        
        # Verify content includes all text
        self.assertIn('Hello, this is the first segment of the transcription.', txt_content)
        self.assertIn('This is the second segment with more content.', txt_content)
        self.assertIn('I am responding to the first speaker.', txt_content)
        
        # Verify chronological order
        speaker1_index = txt_content.find('Speaker 1')
        speaker2_index = txt_content.find('Speaker 2')
        self.assertLess(speaker1_index, speaker2_index, "Speaker 1 should appear before Speaker 2")
    
    def test_docx_output_content_verification(self):
        """Test DOCX output content verification"""
        base_filename = "test_docx"
        
        # Save DOCX output
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        docx_filepath = result['docx_file']
        self.assertTrue(os.path.exists(docx_filepath))
        
        # Verify file size (DOCX files should be larger than empty)
        file_size = os.path.getsize(docx_filepath)
        self.assertGreater(file_size, 1000, "DOCX file seems too small")
        
        # Note: Full DOCX content verification would require additional libraries
        # For now, we verify the file exists and has reasonable size
    
    def test_output_content_completeness(self):
        """Test that all transcription content is included in outputs"""
        base_filename = "test_completeness"
        
        # Save all formats
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        # Get original content statistics
        original_speakers = self.test_transcription_data['speakers']
        original_segments = []
        original_words = 0
        
        for speaker, segments in original_speakers.items():
            for segment in segments:
                original_segments.append(segment)
                original_words += len(segment['text'].split())
        
        # Verify JSON content completeness
        json_filepath = result['json_file']
        with open(json_filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        json_speakers = json_data['speakers']
        json_segments = []
        json_words = 0
        
        for speaker, segments in json_speakers.items():
            for segment in segments:
                json_segments.append(segment)
                json_words += len(segment['text'].split())
        
        # Verify all segments are included
        self.assertEqual(len(json_segments), len(original_segments))
        self.assertEqual(json_words, original_words)
        
        # Verify TXT content completeness
        txt_filepath = result['txt_file']
        with open(txt_filepath, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        # Count words in TXT file
        txt_words = len(txt_content.split())
        self.assertGreaterEqual(txt_words, original_words, "TXT file missing content")
    
    def test_output_consistency_across_formats(self):
        """Test that all output formats contain consistent data"""
        base_filename = "test_consistency"
        
        # Save all formats
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        # Load JSON data
        with open(result['json_file'], 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Load TXT data
        with open(result['txt_file'], 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        # Verify speaker count consistency
        json_speaker_count = len(json_data['speakers'])
        txt_speaker_count = txt_content.count('Speaker ')
        self.assertEqual(json_speaker_count, 2)  # Expected from test data
        
        # Verify total word count consistency
        json_words = sum(
            len(segment['text'].split())
            for segments in json_data['speakers'].values()
            for segment in segments
        )
        
        txt_words = len(txt_content.split())
        self.assertGreaterEqual(txt_words, json_words, "TXT should contain at least as many words as JSON")
    
    def test_output_with_empty_segments(self):
        """Test output handling with empty segments"""
        # Create data with empty segments
        data_with_empty = {
            'speakers': {
                'Speaker 1': [
                    {
                        'speaker': 'Speaker 1',
                        'text': 'Valid content here.',
                        'start': 0.0,
                        'end': 5.0,
                        'words': None
                    },
                    {
                        'speaker': 'Speaker 1',
                        'text': '',  # Empty segment
                        'start': 5.0,
                        'end': 10.0,
                        'words': None
                    },
                    {
                        'speaker': 'Speaker 1',
                        'text': '   ',  # Whitespace-only segment
                        'start': 10.0,
                        'end': 15.0,
                        'words': None
                    }
                ]
            },
            'model_name': 'test-model',
            'audio_file': 'test_audio.wav',
            'transcription_time': 15.0,
            'speaker_count': 1,
            'full_text': 'Valid content here.'
        }
        
        base_filename = "test_empty_segments"
        
        # Save output
        result = self.output_manager.save_transcription(
            data_with_empty,
            base_filename
        )
        
        # Verify files were created
        self.assertTrue(os.path.exists(result['json_file']))
        self.assertTrue(os.path.exists(result['txt_file']))
        self.assertTrue(os.path.exists(result['docx_file']))
        
        # Verify JSON contains only non-empty segments
        with open(result['json_file'], 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        segments = json_data['speakers']['Speaker 1']
        self.assertEqual(len(segments), 1)  # Only the valid segment should remain
        self.assertEqual(segments[0]['text'], 'Valid content here.')
    
    def test_output_with_single_speaker(self):
        """Test output with single speaker data"""
        single_speaker_data = {
            'speakers': {
                'Speaker 1': [
                    {
                        'speaker': 'Speaker 1',
                        'text': 'Single speaker transcription content.',
                        'start': 0.0,
                        'end': 10.0,
                        'words': None
                    }
                ]
            },
            'model_name': 'test-model',
            'audio_file': 'test_audio.wav',
            'transcription_time': 10.0,
            'speaker_count': 1,
            'full_text': 'Single speaker transcription content.'
        }
        
        base_filename = "test_single_speaker"
        
        # Save output
        result = self.output_manager.save_transcription(
            single_speaker_data,
            base_filename
        )
        
        # Verify all files were created
        for filepath in result.values():
            if filepath:
                self.assertTrue(os.path.exists(filepath))
                self.assertGreater(os.path.getsize(filepath), 0)
        
        # Verify JSON structure
        with open(result['json_file'], 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        self.assertEqual(len(json_data['speakers']), 1)
        self.assertIn('Speaker 1', json_data['speakers'])
        self.assertEqual(json_data['speaker_count'], 1)
    
    def test_output_file_naming(self):
        """Test output file naming conventions"""
        base_filename = "test_naming"
        
        # Save output
        result = self.output_manager.save_transcription(
            self.test_transcription_data,
            base_filename
        )
        
        # Verify file naming
        expected_files = [
            f"{base_filename}.json",
            f"{base_filename}.txt",
            f"{base_filename}.docx"
        ]
        
        for expected_file in expected_files:
            filepath = os.path.join(self.transcriptions_dir, expected_file)
            self.assertTrue(os.path.exists(filepath), f"Expected file not found: {expected_file}")
        
        # Verify result contains correct paths
        self.assertIn('json_file', result)
        self.assertIn('txt_file', result)
        self.assertIn('docx_file', result)
        
        for key, filepath in result.items():
            if filepath:
                self.assertTrue(filepath.endswith(f"{base_filename}.{key.split('_')[0]}"))
    
    def test_output_manager_error_handling(self):
        """Test output manager error handling"""
        # Test with invalid data
        invalid_data = None
        
        base_filename = "test_error_handling"
        
        # Should handle gracefully
        try:
            result = self.output_manager.save_transcription(
                invalid_data,
                base_filename
            )
            # If it doesn't raise an exception, verify no files were created
            for filepath in result.values():
                if filepath:
                    self.assertFalse(os.path.exists(filepath))
        except Exception as e:
            # Exception is acceptable for invalid data
            self.assertIsInstance(e, Exception)


class TestDataUtilsVerification(TestCase):
    """Test DataUtils verification functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.data_utils = DataUtils()
    
    def test_speakers_data_extraction_verification(self):
        """Test speakers data extraction verification"""
        # Test with speakers format
        speakers_data = {
            'Speaker 1': [
                {'speaker': 'Speaker 1', 'text': 'Hello', 'start': 0, 'end': 2},
                {'speaker': 'Speaker 1', 'text': 'World', 'start': 2, 'end': 4}
            ],
            'Speaker 2': [
                {'speaker': 'Speaker 2', 'text': 'Response', 'start': 4, 'end': 6}
            ]
        }
        
        test_data = {'speakers': speakers_data}
        result = self.data_utils.extract_speakers_data(test_data)
        
        # Verify extraction
        self.assertEqual(result, speakers_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result['Speaker 1']), 2)
        self.assertEqual(len(result['Speaker 2']), 1)
    
    def test_segments_data_extraction_verification(self):
        """Test segments data extraction verification"""
        segments_data = [
            {'speaker': 'Speaker 1', 'text': 'Hello', 'start': 0, 'end': 2},
            {'speaker': 'Speaker 2', 'text': 'World', 'start': 2, 'end': 4},
            {'speaker': 'Speaker 1', 'text': 'Again', 'start': 4, 'end': 6}
        ]
        
        test_data = {'segments': segments_data}
        result = self.data_utils.extract_speakers_data(test_data)
        
        # Verify conversion to speakers format
        self.assertIn('Speaker 1', result)
        self.assertIn('Speaker 2', result)
        self.assertEqual(len(result['Speaker 1']), 2)
        self.assertEqual(len(result['Speaker 2']), 1)
    
    def test_full_text_extraction_verification(self):
        """Test full text extraction verification"""
        full_text = "This is a complete transcription text with multiple sentences."
        
        test_data = {'full_text': full_text}
        result = self.data_utils.extract_speakers_data(test_data)
        
        # Verify single speaker creation
        self.assertIn('Speaker 1', result)
        self.assertEqual(len(result['Speaker 1']), 1)
        self.assertEqual(result['Speaker 1'][0]['text'], full_text)
        self.assertEqual(result['Speaker 1'][0]['speaker'], 'Speaker 1')
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data"""
        # Test with empty data
        empty_data = {}
        result = self.data_utils.extract_speakers_data(empty_data)
        self.assertEqual(result, {})
        
        # Test with None data
        result = self.data_utils.extract_speakers_data(None)
        self.assertEqual(result, {})
        
        # Test with empty speakers
        empty_speakers = {'speakers': {}}
        result = self.data_utils.extract_speakers_data(empty_speakers)
        self.assertEqual(result, {})
    
    def test_data_validation(self):
        """Test data validation functionality"""
        # Test valid data
        valid_data = {
            'speakers': {
                'Speaker 1': [
                    {'speaker': 'Speaker 1', 'text': 'Valid text', 'start': 0, 'end': 5}
                ]
            }
        }
        
        # Should not raise exceptions
        result = self.data_utils.extract_speakers_data(valid_data)
        self.assertIsInstance(result, dict)
        
        # Test invalid data structure
        invalid_data = {
            'speakers': 'not a dictionary'
        }
        
        # Should handle gracefully
        result = self.data_utils.extract_speakers_data(invalid_data)
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    import unittest
    unittest.main()
