#!/usr/bin/env python3
"""
Unit tests for output cleaner functionality
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, mock
from datetime import datetime, timedelta

# Import the cleaner (assuming it's in the root directory)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clean_output import OutputCleaner


class TestOutputCleaner(TestCase):
    """Test output cleaner functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.cleaner = OutputCleaner(self.output_dir)
        
        # Create test directory structure
        self.create_test_structure()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_structure(self):
        """Create test output directory structure"""
        # Create directories
        transcriptions_dir = os.path.join(self.output_dir, "transcriptions")
        temp_chunks_dir = os.path.join(self.output_dir, "temp_chunks")
        logs_dir = os.path.join(self.output_dir, "logs")
        
        os.makedirs(transcriptions_dir, exist_ok=True)
        os.makedirs(temp_chunks_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create test transcription files
        self.create_test_transcriptions(transcriptions_dir)
        
        # Create test chunk files
        self.create_test_chunks(temp_chunks_dir)
        
        # Create test log files
        self.create_test_logs(logs_dir)
    
    def create_test_transcriptions(self, transcriptions_dir):
        """Create test transcription files"""
        # Recent transcription
        recent_file = os.path.join(transcriptions_dir, "recent_transcription.txt")
        with open(recent_file, 'w') as f:
            f.write("Recent transcription content")
        
        # Old transcription (more than 7 days)
        old_file = os.path.join(transcriptions_dir, "old_transcription.txt")
        with open(old_file, 'w') as f:
            f.write("Old transcription content")
        
        # Set old file modification time
        old_time = datetime.now() - timedelta(days=10)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        # DOCX file
        docx_file = os.path.join(transcriptions_dir, "test_transcription.docx")
        with open(docx_file, 'w') as f:
            f.write("DOCX content placeholder")
    
    def create_test_chunks(self, temp_chunks_dir):
        """Create test chunk files"""
        chunk_files = [
            "chunk_001_0s_120s.json",
            "chunk_002_120s_240s.json",
            "chunk_003_240s_360s.json"
        ]
        
        for chunk_file in chunk_files:
            filepath = os.path.join(temp_chunks_dir, chunk_file)
            chunk_data = {
                'chunk_number': int(chunk_file.split('_')[1]),
                'start_time': 0.0,
                'end_time': 120.0,
                'text': 'Test chunk content',
                'word_count': 3,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
    
    def create_test_logs(self, logs_dir):
        """Create test log files"""
        # Recent log
        recent_log = os.path.join(logs_dir, "recent.log")
        with open(recent_log, 'w') as f:
            f.write("Recent log content")
        
        # Old log (more than 30 days)
        old_log = os.path.join(logs_dir, "old.log")
        with open(old_log, 'w') as f:
            f.write("Old log content")
        
        # Set old file modification time
        old_time = datetime.now() - timedelta(days=35)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
    
    def test_scan_output_structure(self):
        """Test scanning output directory structure"""
        result = self.cleaner.scan_output_structure()
        
        # Verify scan result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['output_dir'], self.output_dir)
        self.assertGreater(result['total_files'], 0)
        self.assertGreater(result['total_size'], 0)
        
        # Verify structure contains expected directories
        structure = result['structure']
        self.assertIn('transcriptions', structure)
        self.assertIn('temp_chunks', structure)
        self.assertIn('logs', structure)
        self.assertIn('other', structure)
        
        # Verify file counts
        self.assertGreater(structure['transcriptions']['file_count'], 0)
        self.assertGreater(structure['temp_chunks']['file_count'], 0)
        self.assertGreater(structure['logs']['file_count'], 0)
    
    def test_scan_nonexistent_directory(self):
        """Test scanning non-existent directory"""
        cleaner = OutputCleaner("nonexistent_directory")
        result = cleaner.scan_output_structure()
        
        self.assertEqual(result['status'], 'not_found')
        self.assertIn('message', result)
        self.assertIn('structure', result)
    
    def test_clean_temp_chunks(self):
        """Test cleaning temporary chunk files"""
        # Verify chunks exist before cleaning
        temp_chunks_dir = os.path.join(self.output_dir, "temp_chunks")
        chunk_files_before = [f for f in os.listdir(temp_chunks_dir) if f.startswith("chunk_")]
        self.assertGreater(len(chunk_files_before), 0)
        
        # Clean temp chunks
        result = self.cleaner.clean_temp_chunks()
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['cleaned_files'], 0)
        self.assertGreater(result['cleaned_size'], 0)
        
        # Verify chunks were removed (directory might be deleted if empty)
        if os.path.exists(temp_chunks_dir):
            chunk_files_after = [f for f in os.listdir(temp_chunks_dir) if f.startswith("chunk_")]
            self.assertEqual(len(chunk_files_after), 0)
        else:
            # Directory was deleted because it became empty
            pass
        
        # Verify summary
        summary = self.cleaner.get_cleanup_summary()
        self.assertGreater(summary['cleaned_files'], 0)
        # Size might be 0 if files are very small (less than 1 MB total)
        self.assertGreaterEqual(summary['total_size_cleaned_mb'], 0)
    
    def test_clean_temp_chunks_dry_run(self):
        """Test cleaning temp chunks in dry run mode"""
        # Count chunks before
        temp_chunks_dir = os.path.join(self.output_dir, "temp_chunks")
        chunk_files_before = [f for f in os.listdir(temp_chunks_dir) if f.startswith("chunk_")]
        initial_count = len(chunk_files_before)
        
        # Clean temp chunks in dry run mode
        result = self.cleaner.clean_temp_chunks(dry_run=True)
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['cleaned_files'], 0)  # In dry run, no files are actually cleaned
        
        # Verify chunks were NOT removed (dry run)
        chunk_files_after = [f for f in os.listdir(temp_chunks_dir) if f.startswith("chunk_")]
        self.assertEqual(len(chunk_files_after), initial_count)
    
    def test_clean_old_transcriptions(self):
        """Test cleaning old transcription files"""
        # Clean transcriptions older than 7 days
        result = self.cleaner.clean_old_transcriptions(days_old=7)
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['cleaned_files'], 0)
        self.assertIn('cutoff_date', result)
        
        # Verify old files were removed
        transcriptions_dir = os.path.join(self.output_dir, "transcriptions")
        remaining_files = os.listdir(transcriptions_dir)
        
        # Should still have recent files
        self.assertIn("recent_transcription.txt", remaining_files)
        self.assertIn("test_transcription.docx", remaining_files)
        
        # Old file should be removed
        self.assertNotIn("old_transcription.txt", remaining_files)
    
    def test_clean_old_logs(self):
        """Test cleaning old log files"""
        # Clean logs older than 30 days
        result = self.cleaner.clean_logs(days_old=30)
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['cleaned_files'], 0)
        self.assertIn('cutoff_date', result)
        
        # Verify old files were removed
        logs_dir = os.path.join(self.output_dir, "logs")
        remaining_files = os.listdir(logs_dir)
        
        # Should still have recent files
        self.assertIn("recent.log", remaining_files)
        
        # Old file should be removed
        self.assertNotIn("old.log", remaining_files)
    
    def test_clean_all_dry_run(self):
        """Test cleaning all files in dry run mode"""
        # Count files before
        file_count_before = sum(1 for _ in Path(self.output_dir).rglob("*") if _.is_file())
        
        # Clean all in dry run mode
        result = self.cleaner.clean_all(dry_run=True)
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertIn('message', result)
        
        # Verify files were NOT removed (dry run)
        file_count_after = sum(1 for _ in Path(self.output_dir).rglob("*") if _.is_file())
        self.assertEqual(file_count_after, file_count_before)
    
    def test_clean_nonexistent_directories(self):
        """Test cleaning non-existent directories"""
        cleaner = OutputCleaner("nonexistent_directory")
        
        # Test cleaning temp chunks
        result = cleaner.clean_temp_chunks()
        self.assertEqual(result['status'], 'not_found')
        
        # Test cleaning old transcriptions
        result = cleaner.clean_old_transcriptions(days_old=7)
        self.assertEqual(result['status'], 'not_found')
        
        # Test cleaning old logs
        result = cleaner.clean_logs(days_old=30)
        self.assertEqual(result['status'], 'not_found')
    
    def test_get_cleanup_summary(self):
        """Test getting cleanup summary"""
        # Perform some cleanup
        self.cleaner.clean_temp_chunks()
        
        # Get summary
        summary = self.cleaner.get_cleanup_summary()
        
        # Verify summary structure
        self.assertIn('cleaned_files', summary)
        self.assertIn('cleaned_directories', summary)
        self.assertIn('total_size_cleaned_mb', summary)
        self.assertIn('cleaned_files_list', summary)
        self.assertIn('cleaned_directories_list', summary)
        
        # Verify values
        self.assertGreaterEqual(summary['cleaned_files'], 0)
        self.assertGreaterEqual(summary['cleaned_directories'], 0)
        self.assertGreaterEqual(summary['total_size_cleaned_mb'], 0)
        self.assertIsInstance(summary['cleaned_files_list'], list)
        self.assertIsInstance(summary['cleaned_directories_list'], list)
    
    def test_cleanup_empty_directories(self):
        """Test cleanup of empty directories"""
        # Create a nested directory structure with some empty dirs
        nested_dir = os.path.join(self.output_dir, "nested", "empty", "deep")
        os.makedirs(nested_dir, exist_ok=True)
        
        # Create a file in the deepest directory
        test_file = os.path.join(nested_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Remove the file
        os.remove(test_file)
        
        # Clean up empty directories
        self.cleaner._cleanup_empty_directories(Path(self.output_dir))
        
        # Verify empty directories were removed
        self.assertFalse(os.path.exists(nested_dir))
        self.assertFalse(os.path.exists(os.path.dirname(nested_dir)))
        self.assertFalse(os.path.exists(os.path.dirname(os.path.dirname(nested_dir))))
    
    def test_file_permissions(self):
        """Test file permission handling"""
        # Create a file with specific permissions
        test_file = os.path.join(self.output_dir, "test_permissions.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Verify file is accessible
        self.assertTrue(os.access(test_file, os.R_OK))
        self.assertTrue(os.access(test_file, os.W_OK))
        
        # Test reading the file
        with open(test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "test content")


class TestOutputCleanerIntegration(TestCase):
    """Integration tests for output cleaner"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.cleaner = OutputCleaner(self.output_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_multiple_cleanup_operations(self):
        """Test multiple cleanup operations in sequence"""
        # Create test structure
        self.create_complex_test_structure()
        
        # Perform multiple cleanup operations
        results = {}
        
        # Clean temp chunks
        results['temp_chunks'] = self.cleaner.clean_temp_chunks()
        
        # Clean old transcriptions
        results['old_transcriptions'] = self.cleaner.clean_old_transcriptions(days_old=7)
        
        # Clean old logs
        results['old_logs'] = self.cleaner.clean_logs(days_old=30)
        
        # Verify all operations succeeded
        for operation, result in results.items():
            self.assertEqual(result['status'], 'success', f"Operation {operation} failed")
        
        # Get final summary
        summary = self.cleaner.get_cleanup_summary()
        self.assertGreaterEqual(summary['cleaned_files'], 0)
        self.assertGreaterEqual(summary['total_size_cleaned_mb'], 0)
    
    def create_complex_test_structure(self):
        """Create a complex test directory structure"""
        # Create directories
        transcriptions_dir = os.path.join(self.output_dir, "transcriptions")
        temp_chunks_dir = os.path.join(self.output_dir, "temp_chunks")
        logs_dir = os.path.join(self.output_dir, "logs")
        
        os.makedirs(transcriptions_dir, exist_ok=True)
        os.makedirs(temp_chunks_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create various test files with different ages
        self.create_files_with_ages(transcriptions_dir, "transcription", 5, 15)
        self.create_files_with_ages(temp_chunks_dir, "chunk", 1, 1)
        self.create_files_with_ages(logs_dir, "log", 10, 40)
    
    def create_files_with_ages(self, directory, prefix, recent_days, old_days):
        """Create files with different ages"""
        # Recent file
        recent_file = os.path.join(directory, f"{prefix}_recent.txt")
        with open(recent_file, 'w') as f:
            f.write(f"Recent {prefix} content")
        
        # Old file
        old_file = os.path.join(directory, f"{prefix}_old.txt")
        with open(old_file, 'w') as f:
            f.write(f"Old {prefix} content")
        
        # Set old file modification time
        old_time = datetime.now() - timedelta(days=old_days)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))


if __name__ == '__main__':
    import unittest
    unittest.main()
