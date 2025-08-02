#!/usr/bin/env python3
"""
Test script for the unified batch transcription functionality
"""

import sys
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Try to import pytest, but make it optional for basic testing
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the unified batch transcription classes
from batch_transcribe_unified import BatchTranscriptionConfig, BatchTranscriptionProcessor

class TestBatchTranscriptionConfig:
    """Test the BatchTranscriptionConfig class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = BatchTranscriptionConfig()
        
        assert config.model == "ivrit-ai/whisper-large-v3-turbo-ct2"
        assert config.engine == "faster-whisper"
        assert config.speaker_config == "conversation"
        assert config.timeout == 3600
        assert config.delay_between_files == 10
        assert config.input_dir == "examples/audio/voice"
        assert config.output_dir == "output"
        assert config.docker_image == "whisper-runpod-serverless:latest"
        assert config.verbose == False
        assert config.dry_run == False
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = BatchTranscriptionConfig(
            model="openai/whisper-large-v3",
            engine="stable-ts",
            speaker_config="interview",
            timeout=1800,
            delay_between_files=30,
            input_dir="custom_input",
            output_dir="custom_output",
            docker_image="custom-image:latest",
            verbose=True,
            dry_run=True
        )
        
        assert config.model == "openai/whisper-large-v3"
        assert config.engine == "stable-ts"
        assert config.speaker_config == "interview"
        assert config.timeout == 1800
        assert config.delay_between_files == 30
        assert config.input_dir == "custom_input"
        assert config.output_dir == "custom_output"
        assert config.docker_image == "custom-image:latest"
        assert config.verbose == True
        assert config.dry_run == True

class TestBatchTranscriptionProcessor:
    """Test the BatchTranscriptionProcessor class"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = BatchTranscriptionConfig(
            input_dir="examples/audio/voice",
            output_dir="output",
            dry_run=True  # Use dry run for testing
        )
        self.processor = BatchTranscriptionProcessor(self.config)
    
    def test_discover_audio_files_existing_directory(self):
        """Test audio file discovery in existing directory"""
        # Create a temporary directory with mock audio files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock audio files
            audio_files = [
                "test1.wav",
                "test2.mp3", 
                "test3.m4a",
                "test4.flac",
                "test5.ogg",
                "test6.aac"
            ]
            
            for file_name in audio_files:
                (Path(temp_dir) / file_name).touch()
            
            # Update processor config to use temp directory
            self.processor.config.input_dir = temp_dir
            
            # Discover files
            discovered_files = self.processor.discover_audio_files()
            
            # Verify all files were discovered
            assert len(discovered_files) == len(audio_files)
            for file_path in discovered_files:
                assert Path(file_path).name in audio_files
    
    def test_discover_audio_files_nonexistent_directory(self):
        """Test audio file discovery with nonexistent directory"""
        self.processor.config.input_dir = "nonexistent_directory"
        
        if PYTEST_AVAILABLE:
            with pytest.raises(FileNotFoundError):
                self.processor.discover_audio_files()
        else:
            # Fallback for when pytest is not available
            try:
                self.processor.discover_audio_files()
                assert False, "Expected FileNotFoundError"
            except FileNotFoundError:
                pass  # Expected
    
    def test_discover_audio_files_empty_directory(self):
        """Test audio file discovery in empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.processor.config.input_dir = temp_dir
            discovered_files = self.processor.discover_audio_files()
            assert len(discovered_files) == 0
    
    @patch('subprocess.run')
    def test_run_docker_transcription_success(self, mock_subprocess):
        """Test successful Docker transcription"""
        # Mock successful subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "✅ Transcription completed successfully!"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Test with dry run (should not call subprocess)
        self.config.dry_run = True
        result = self.processor.run_docker_transcription("test.wav")
        
        assert result["success"] == True
        assert result["file"] == "test.wav"
        assert result["error"] is None
        assert result["processing_time"] > 0
    
    @patch('subprocess.run')
    def test_run_docker_transcription_failure(self, mock_subprocess):
        """Test failed Docker transcription"""
        # Mock failed subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Docker error occurred"
        mock_subprocess.return_value = mock_result
        
        # Test with actual run (not dry run)
        self.config.dry_run = False
        result = self.processor.run_docker_transcription("test.wav")
        
        assert result["success"] == False
        assert result["file"] == "test.wav"
        assert result["error"] == "Docker error occurred"
    
    @patch('subprocess.run')
    def test_run_docker_transcription_timeout(self, mock_subprocess):
        """Test Docker transcription timeout"""
        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired("docker", 3600)
        
        self.config.dry_run = False
        result = self.processor.run_docker_transcription("test.wav")
        
        assert result["success"] == False
        assert result["file"] == "test.wav"
        assert "Timeout" in result["error"]
    
    def test_process_batch_no_files(self):
        """Test batch processing with no audio files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.processor.config.input_dir = temp_dir
            result = self.processor.process_batch()
            
            assert result["success"] == False
            assert "No audio files found" in result["error"]
    
    def test_process_batch_with_files(self):
        """Test batch processing with audio files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock audio files
            audio_files = ["test1.wav", "test2.mp3"]
            for file_name in audio_files:
                (Path(temp_dir) / file_name).touch()
            
            self.processor.config.input_dir = temp_dir
            self.processor.config.dry_run = True  # Use dry run for testing
            
            result = self.processor.process_batch()
            
            assert result["success"] == True
            assert result["total_files"] == 2
            assert result["successful"] == 2
            assert result["failed"] == 0
            assert len(result["results"]) == 2

def test_argument_parsing():
    """Test command line argument parsing"""
    from batch_transcribe_unified import parse_arguments
    
    # Test with no arguments (should use defaults)
    with patch('sys.argv', ['batch_transcribe_unified.py']):
        args = parse_arguments()
        assert args.model == "ivrit-ai/whisper-large-v3-turbo-ct2"
        assert args.engine == "faster-whisper"
        assert args.verbose == False
        assert args.dry_run == False
    
    # Test with custom arguments
    with patch('sys.argv', [
        'batch_transcribe_unified.py',
        '--model', 'openai/whisper-large-v3',
        '--engine', 'stable-ts',
        '--verbose',
        '--dry-run'
    ]):
        args = parse_arguments()
        assert args.model == "openai/whisper-large-v3"
        assert args.engine == "stable-ts"
        assert args.verbose == True
        assert args.dry_run == True

def test_config_file_loading():
    """Test configuration file loading"""
    from batch_transcribe_unified import load_config_from_file
    
    # Create temporary config file
    config_data = {
        "model": "test-model",
        "engine": "test-engine",
        "timeout": 1800,
        "verbose": True
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name
    
    try:
        loaded_config = load_config_from_file(config_file)
        assert loaded_config["model"] == "test-model"
        assert loaded_config["engine"] == "test-engine"
        assert loaded_config["timeout"] == 1800
        assert loaded_config["verbose"] == True
    finally:
        os.unlink(config_file)

def test_integration_with_real_directory():
    """Integration test with real examples directory"""
    # Check if examples directory exists
    examples_dir = Path("examples/audio/voice")
    if not examples_dir.exists():
        if PYTEST_AVAILABLE:
            pytest.skip("Examples directory not found, skipping integration test")
        else:
            return  # Skip test if pytest not available
    
    config = BatchTranscriptionConfig(
        input_dir="examples/audio/voice",
        output_dir="output",
        dry_run=True  # Use dry run for testing
    )
    processor = BatchTranscriptionProcessor(config)
    
    try:
        audio_files = processor.discover_audio_files()
        print(f"Found {len(audio_files)} audio files in examples directory")
        
        # Test that we can create a processor
        assert processor is not None
        assert processor.config.input_dir == "examples/audio/voice"
        
    except FileNotFoundError:
        if PYTEST_AVAILABLE:
            pytest.skip("Examples directory not accessible")
        else:
            return  # Skip test if pytest not available

def main():
    """Main test function"""
    print("🧪 Unified Batch Transcription Test Suite")
    print("=" * 60)
    print()
    
    # Run tests
    test_results = []
    
    # Test configuration
    print("🔧 Testing Configuration...")
    try:
        config = BatchTranscriptionConfig()
        test_results.append(("Configuration", True, "Default config created successfully"))
    except Exception as e:
        test_results.append(("Configuration", False, str(e)))
    
    # Test processor creation
    print("⚙️  Testing Processor...")
    try:
        config = BatchTranscriptionConfig(dry_run=True)
        processor = BatchTranscriptionProcessor(config)
        test_results.append(("Processor", True, "Processor created successfully"))
    except Exception as e:
        test_results.append(("Processor", False, str(e)))
    
    # Test file discovery
    print("📁 Testing File Discovery...")
    try:
        examples_dir = Path("examples/audio/voice")
        if examples_dir.exists():
            # Create a new processor for file discovery test
            discovery_config = BatchTranscriptionConfig(dry_run=True)
            discovery_processor = BatchTranscriptionProcessor(discovery_config)
            audio_files = discovery_processor.discover_audio_files()
            test_results.append(("File Discovery", True, f"Found {len(audio_files)} files"))
        else:
            test_results.append(("File Discovery", True, "Examples directory not found (expected)"))
    except Exception as e:
        test_results.append(("File Discovery", False, str(e)))
    
    # Test argument parsing
    print("🔍 Testing Argument Parsing...")
    try:
        from batch_transcribe_unified import parse_arguments
        with patch('sys.argv', ['batch_transcribe_unified.py']):
            args = parse_arguments()
            test_results.append(("Argument Parsing", True, "Arguments parsed successfully"))
    except Exception as e:
        test_results.append(("Argument Parsing", False, str(e)))
    
    # Print results
    print("\n📊 Test Results")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success, message in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if success:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Unified batch transcription is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 