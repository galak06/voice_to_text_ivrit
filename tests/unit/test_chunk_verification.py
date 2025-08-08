#!/usr/bin/env python3
"""
Unit tests for chunk verification functionality
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, mock
from datetime import datetime, timedelta

from src.core.speaker_engines import CustomWhisperEngine
from src.output_data.utils.data_utils import DataUtils


class TestChunkVerification(TestCase):
    """Test chunk verification functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_chunks_dir = os.path.join(self.temp_dir, "temp_chunks")
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
        
        # Create test chunk files
        self.create_test_chunks()
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_chunks(self):
        """Create test chunk files"""
        test_chunks = [
            {
                'chunk_number': 1,
                'start_time': 0.0,
                'end_time': 120.0,
                'text': 'This is the first chunk of transcription.',
                'word_count': 8,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            },
            {
                'chunk_number': 2,
                'start_time': 120.0,
                'end_time': 240.0,
                'text': 'This is the second chunk with more content.',
                'word_count': 9,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            },
            {
                'chunk_number': 3,
                'start_time': 240.0,
                'end_time': 360.0,
                'text': 'PROCESSING_IN_PROGRESS',
                'word_count': 0,
                'status': 'processing',
                'timestamp': datetime.now().isoformat()
            },
            {
                'chunk_number': 4,
                'start_time': 360.0,
                'end_time': 480.0,
                'text': '',
                'word_count': 0,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        for chunk in test_chunks:
            filename = f"chunk_{chunk['chunk_number']:03d}_{chunk['start_time']:.0f}s_{chunk['end_time']:.0f}s.json"
            filepath = os.path.join(self.temp_chunks_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)
    
    def test_chunk_merge_sequential_ordering(self):
        """Test that chunks are merged in sequential order"""
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        # Mock the engine to avoid actual model loading
        with mock.patch.object(engine, '_get_or_load_model'):
            with mock.patch.object(engine, 'cleanup_models'):
                result = engine._merge_temp_chunks("test_audio.wav", "test-model")
        
        # Verify chunks are merged in order
        self.assertIn('speakers', result)
        self.assertIn('Speaker 1', result['speakers'])
        
        segments = result['speakers']['Speaker 1']
        self.assertEqual(len(segments), 2)  # Only completed chunks should be merged
        
        # Check chronological order
        self.assertLessEqual(segments[0].start, segments[1].start)
        self.assertLessEqual(segments[0].end, segments[1].end)
    
    def test_chunk_merge_skips_processing_chunks(self):
        """Test that processing chunks are skipped during merge"""
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        with mock.patch.object(engine, '_get_or_load_model'):
            with mock.patch.object(engine, 'cleanup_models'):
                result = engine._merge_temp_chunks("test_audio.wav", "test-model")
        
        # Should only include completed chunks (not processing or empty)
        segments = result['speakers']['Speaker 1']
        self.assertEqual(len(segments), 2)
        
        # Verify no processing chunks are included
        for segment in segments:
            self.assertNotEqual(segment.text, 'PROCESSING_IN_PROGRESS')
            self.assertNotEqual(segment.text, '')
    
    def test_chunk_merge_handles_missing_chunks(self):
        """Test handling of missing chunk files"""
        # Remove one chunk file
        chunk_file = os.path.join(self.temp_chunks_dir, "chunk_002_120s_240s.json")
        os.remove(chunk_file)
        
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        with mock.patch.object(engine, '_get_or_load_model'):
            with mock.patch.object(engine, 'cleanup_models'):
                result = engine._merge_temp_chunks("test_audio.wav", "test-model")
        
        # Should still work with missing chunks
        self.assertIn('speakers', result)
        self.assertIn('Speaker 1', result['speakers'])
        
        segments = result['speakers']['Speaker 1']
        self.assertEqual(len(segments), 1)  # Only one completed chunk remains
    
    def test_chunk_merge_handles_corrupted_files(self):
        """Test handling of corrupted chunk files"""
        # Create a corrupted chunk file
        corrupted_file = os.path.join(self.temp_chunks_dir, "chunk_005_480s_600s.json")
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        with mock.patch.object(engine, '_get_or_load_model'):
            with mock.patch.object(engine, 'cleanup_models'):
                result = engine._merge_temp_chunks("test_audio.wav", "test-model")
        
        # Should still work with corrupted files
        self.assertIn('speakers', result)
        self.assertIn('Speaker 1', result['speakers'])
        
        segments = result['speakers']['Speaker 1']
        self.assertEqual(len(segments), 2)  # Valid chunks should still be processed
    
    def test_chunk_merge_no_valid_chunks(self):
        """Test handling when no valid chunks exist"""
        # Remove all chunk files
        for file in os.listdir(self.temp_chunks_dir):
            os.remove(os.path.join(self.temp_chunks_dir, file))
        
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        with mock.patch.object(engine, '_get_or_load_model'):
            with mock.patch.object(engine, 'cleanup_models'):
                result = engine._merge_temp_chunks("test_audio.wav", "test-model")
        
        # Should return empty result
        self.assertIn('speakers', result)
        self.assertEqual(result['speakers'], {})
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'No chunks were successfully merged')
    
    def test_data_utils_speakers_extraction(self):
        """Test speakers data extraction from various formats"""
        data_utils = DataUtils()
        
        # Test speakers format
        speakers_data = {
            'Speaker 1': [
                {'speaker': 'Speaker 1', 'text': 'Hello world', 'start': 0, 'end': 5},
                {'speaker': 'Speaker 1', 'text': 'How are you?', 'start': 5, 'end': 10}
            ],
            'Speaker 2': [
                {'speaker': 'Speaker 2', 'text': 'I am fine', 'start': 10, 'end': 15}
            ]
        }
        
        test_data = {'speakers': speakers_data}
        result = data_utils.extract_speakers_data(test_data)
        
        self.assertEqual(result, speakers_data)
        
        # Test segments format
        segments_data = [
            {'speaker': 'Speaker 1', 'text': 'Hello world', 'start': 0, 'end': 5},
            {'speaker': 'Speaker 2', 'text': 'I am fine', 'start': 5, 'end': 10}
        ]
        
        test_data = {'segments': segments_data}
        result = data_utils.extract_speakers_data(test_data)
        
        self.assertIn('Speaker 1', result)
        self.assertIn('Speaker 2', result)
        self.assertEqual(len(result['Speaker 1']), 1)
        self.assertEqual(len(result['Speaker 2']), 1)
        
        # Test full_text format
        test_data = {'full_text': 'This is a complete transcription text.'}
        result = data_utils.extract_speakers_data(test_data)
        
        self.assertIn('Speaker 1', result)
        self.assertEqual(len(result['Speaker 1']), 1)
        self.assertEqual(result['Speaker 1'][0]['text'], 'This is a complete transcription text.')
    
    def test_chunk_sequence_validation(self):
        """Test chunk sequence validation"""
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        # Test with sequential chunks
        chunk_files = engine._get_existing_chunks()
        self.assertEqual(len(chunk_files), 4)
        
        # Verify chunk numbers are sequential
        chunk_numbers = []
        for chunk_file in chunk_files:
            try:
                chunk_number = int(chunk_file.split('_')[1])
                chunk_numbers.append(chunk_number)
            except (IndexError, ValueError):
                self.fail(f"Invalid chunk filename format: {chunk_file}")
        
        chunk_numbers.sort()
        expected_sequence = list(range(1, max(chunk_numbers) + 1))
        self.assertEqual(chunk_numbers, expected_sequence)
    
    def test_chunk_content_validation(self):
        """Test chunk content validation"""
        # Create mock config
        mock_config = mock.MagicMock()
        mock_config.chunk_duration = 120
        mock_config.temp_chunks_dir = self.temp_chunks_dir
        
        engine = CustomWhisperEngine(mock_config)
        engine.temp_chunks_dir = self.temp_chunks_dir
        
        # Test reading chunk content
        chunk_files = engine._get_existing_chunks()
        self.assertGreater(len(chunk_files), 0)
        
        for chunk_file in chunk_files:
            chunk_path = os.path.join(self.temp_chunks_dir, chunk_file)
            
            with open(chunk_path, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            # Verify required fields
            required_fields = ['chunk_number', 'start_time', 'end_time', 'text', 'word_count']
            for field in required_fields:
                self.assertIn(field, chunk_data, f"Missing required field: {field}")
            
            # Verify data types
            self.assertIsInstance(chunk_data['chunk_number'], int)
            self.assertIsInstance(chunk_data['start_time'], (int, float))
            self.assertIsInstance(chunk_data['end_time'], (int, float))
            self.assertIsInstance(chunk_data['text'], str)
            self.assertIsInstance(chunk_data['word_count'], int)
            
            # Verify logical consistency
            self.assertLessEqual(chunk_data['start_time'], chunk_data['end_time'])
            self.assertGreaterEqual(chunk_data['word_count'], 0)


class TestChunkFileOperations(TestCase):
    """Test chunk file operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_chunks_dir = os.path.join(self.temp_dir, "temp_chunks")
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_chunk_file(self):
        """Test creating a chunk file"""
        chunk_data = {
            'chunk_number': 1,
            'start_time': 0.0,
            'end_time': 120.0,
            'text': 'Test transcription text.',
            'word_count': 4,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        
        filename = f"chunk_{chunk_data['chunk_number']:03d}_{chunk_data['start_time']:.0f}s_{chunk_data['end_time']:.0f}s.json"
        filepath = os.path.join(self.temp_chunks_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, chunk_data)
    
    def test_chunk_file_naming_convention(self):
        """Test chunk file naming convention"""
        chunk_number = 5
        start_time = 600.0
        end_time = 720.0
        
        filename = f"chunk_{chunk_number:03d}_{start_time:.0f}s_{end_time:.0f}s.json"
        
        # Verify naming pattern
        self.assertRegex(filename, r'^chunk_\d{3}_\d+s_\d+s\.json$')
        
        # Verify components
        parts = filename.split('_')
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], 'chunk')
        self.assertEqual(int(parts[1]), chunk_number)
        self.assertEqual(parts[2], f"{start_time:.0f}s")
        self.assertEqual(parts[3], f"{end_time:.0f}s.json")
    
    def test_chunk_file_cleanup(self):
        """Test chunk file cleanup"""
        # Create some test files
        test_files = [
            "chunk_001_0s_120s.json",
            "chunk_002_120s_240s.json",
            "chunk_003_240s_360s.json",
            "other_file.txt"  # Non-chunk file
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.temp_chunks_dir, filename)
            with open(filepath, 'w') as f:
                f.write("test content")
        
        # Clean up chunk files only
        chunk_files = [f for f in os.listdir(self.temp_chunks_dir) if f.startswith("chunk_") and f.endswith(".json")]
        
        for chunk_file in chunk_files:
            filepath = os.path.join(self.temp_chunks_dir, chunk_file)
            os.remove(filepath)
        
        # Verify only chunk files were removed
        remaining_files = os.listdir(self.temp_chunks_dir)
        self.assertEqual(len(remaining_files), 1)
        self.assertEqual(remaining_files[0], "other_file.txt")
    
    def test_chunk_file_permissions(self):
        """Test chunk file permissions"""
        chunk_data = {
            'chunk_number': 1,
            'start_time': 0.0,
            'end_time': 120.0,
            'text': 'Test text.',
            'word_count': 2,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        
        filename = f"chunk_{chunk_data['chunk_number']:03d}_{chunk_data['start_time']:.0f}s_{chunk_data['end_time']:.0f}s.json"
        filepath = os.path.join(self.temp_chunks_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        # Verify file is readable and writable
        self.assertTrue(os.access(filepath, os.R_OK))
        self.assertTrue(os.access(filepath, os.W_OK))
        
        # Test reading the file
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, chunk_data)


if __name__ == '__main__':
    import unittest
    unittest.main()
