#!/usr/bin/env python3
"""
Unit tests for input validation Pydantic models
"""

import unittest
from pathlib import Path
from datetime import datetime

from src.models import (
    InputType,
    TranscriptionEngine,
    AudioFileValidation,
    JobInputValidation,
    InputValidationRequest,
    BatchInputValidation
)


class TestInputValidationModels(unittest.TestCase):
    """Test cases for input validation Pydantic models"""
    
    def test_input_type_enum(self):
        """Test InputType enum values"""
        self.assertEqual(InputType.FILE, "file")
        self.assertEqual(InputType.BLOB, "blob")
        self.assertEqual(InputType.URL, "url")
        
        # Test enum membership
        self.assertIn(InputType.FILE, InputType)
        self.assertIn(InputType.BLOB, InputType)
        self.assertIn(InputType.URL, InputType)
    
    def test_transcription_engine_enum(self):
        """Test TranscriptionEngine enum values"""
        self.assertEqual(TranscriptionEngine.STABLE_WHISPER, "stable-whisper")
        self.assertEqual(TranscriptionEngine.CUSTOM_WHISPER, "custom-whisper")
        self.assertEqual(TranscriptionEngine.OPTIMIZED_WHISPER, "optimized-whisper")
        self.assertEqual(TranscriptionEngine.SPEAKER_DIARIZATION, "speaker-diarization")
        self.assertEqual(TranscriptionEngine.CTTRANSLATE2_WHISPER, "ctranslate2-whisper")
    
    def test_audio_file_validation_creation(self):
        """Test AudioFileValidation model creation"""
        validation = AudioFileValidation(
            file_path="/test/audio.wav",
            file_name="audio.wav",
            file_size=1024,
            file_format=".wav",
            valid=True
        )
        
        self.assertEqual(validation.file_path, "/test/audio.wav")
        self.assertEqual(validation.file_name, "audio.wav")
        self.assertEqual(validation.file_size, 1024)
        self.assertEqual(validation.file_format, ".wav")
        self.assertTrue(validation.valid)
        self.assertIsNone(validation.error)
        self.assertIsInstance(validation.validation_timestamp, datetime)
    
    def test_audio_file_validation_file_format_normalization(self):
        """Test file format normalization in AudioFileValidation"""
        # Test without dot prefix
        validation = AudioFileValidation(
            file_path="/test/audio.wav",
            file_name="audio.wav",
            file_size=1024,
            file_format="wav",
            valid=True
        )
        
        # Should automatically add dot prefix
        self.assertEqual(validation.file_format, ".wav")
    
    def test_audio_file_validation_file_path_normalization(self):
        """Test file path normalization in AudioFileValidation"""
        validation = AudioFileValidation(
            file_path="./test/../audio.wav",
            file_name="audio.wav",
            file_size=1024,
            file_format=".wav",
            valid=True
        )
        
        # Should resolve to absolute path
        self.assertTrue(Path(validation.file_path).is_absolute())
    
    def test_job_input_validation_file_type(self):
        """Test JobInputValidation with file type"""
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            model="whisper-large-v3",
            audio_file="/path/to/audio.wav"
        )
        
        self.assertEqual(job_input.datatype, InputType.FILE)
        self.assertEqual(job_input.engine, TranscriptionEngine.CUSTOM_WHISPER)
        self.assertEqual(job_input.model, "whisper-large-v3")
        self.assertEqual(job_input.audio_file, "/path/to/audio.wav")
        self.assertIsNone(job_input.url)
        self.assertIsNone(job_input.blob_data)
    
    def test_job_input_validation_url_type(self):
        """Test JobInputValidation with URL type"""
        job_input = JobInputValidation(
            datatype=InputType.URL,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            url="https://example.com/audio.wav"
        )
        
        self.assertEqual(job_input.datatype, InputType.URL)
        self.assertEqual(job_input.url, "https://example.com/audio.wav")
        self.assertIsNone(job_input.audio_file)
        self.assertIsNone(job_input.blob_data)
    
    def test_job_input_validation_blob_type(self):
        """Test JobInputValidation with blob type"""
        blob_data = b"fake audio data"
        job_input = JobInputValidation(
            datatype=InputType.BLOB,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            blob_data=blob_data
        )
        
        self.assertEqual(job_input.datatype, InputType.BLOB)
        self.assertEqual(job_input.blob_data, blob_data)
        self.assertIsNone(job_input.audio_file)
        self.assertIsNone(job_input.url)
    
    def test_job_input_validation_missing_required_field(self):
        """Test JobInputValidation validation for missing required fields"""
        # FILE type without audio_file should fail
        with self.assertRaises(ValueError) as context:
            JobInputValidation(
                datatype=InputType.FILE,
                engine=TranscriptionEngine.CUSTOM_WHISPER
                # Missing audio_file
            )
        
        self.assertIn("audio_file is required", str(context.exception))
    
    def test_job_input_validation_url_format(self):
        """Test URL format validation"""
        # Valid URL
        job_input = JobInputValidation(
            datatype=InputType.URL,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            url="https://example.com/audio.wav"
        )
        self.assertEqual(job_input.url, "https://example.com/audio.wav")
        
        # Invalid URL should fail
        with self.assertRaises(ValueError) as context:
            JobInputValidation(
                datatype=InputType.URL,
                engine=TranscriptionEngine.CUSTOM_WHISPER,
                url="invalid-url"
            )
        
        self.assertIn("must start with http:// or https://", str(context.exception))
    
    def test_job_input_validation_model_name(self):
        """Test model name validation"""
        # Valid model name
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            model="whisper-large-v3",
            audio_file="/path/to/audio.wav"
        )
        self.assertEqual(job_input.model, "whisper-large-v3")
        
        # Invalid model name should fail
        with self.assertRaises(ValueError) as context:
            JobInputValidation(
                datatype=InputType.FILE,
                engine=TranscriptionEngine.CUSTOM_WHISPER,
                model="invalid@model#name",
                audio_file="/path/to/audio.wav"
            )
        
        self.assertIn("contains invalid characters", str(context.exception))
    
    def test_transcription_request_creation(self):
        """Test TranscriptionRequest model creation"""
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            model="whisper-large-v3",
            audio_file="/path/to/audio.wav"
        )
        
        request = InputValidationRequest(
            job_input=job_input,
            priority=5,
            config_overrides={"language": "he"}
        )
        
        self.assertEqual(request.job_input, job_input)
        self.assertEqual(request.priority, 5)
        self.assertEqual(request.config_overrides, {"language": "he"})
        self.assertIsInstance(request.request_timestamp, datetime)
    
    def test_transcription_request_priority_validation(self):
        """Test priority field validation"""
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            audio_file="/path/to/audio.wav"
        )
        
        # Valid priority
        request = InputValidationRequest(
            job_input=job_input,
            priority=5
        )
        self.assertEqual(request.priority, 5)
        
        # Invalid priority should fail
        with self.assertRaises(ValueError) as context:
            InputValidationRequest(
                job_input=job_input,
                priority=15  # Out of range
            )
        
        # Pydantic v2 provides different error messages
        error_msg = str(context.exception)
        self.assertTrue(
            "less than or equal to 10" in error_msg or "must be between 1 and 10" in error_msg,
            f"Expected priority validation error, got: {error_msg}"
        )
    
    def test_transcription_request_ready_for_processing(self):
        """Test is_ready_for_processing method"""
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            audio_file="/path/to/audio.wav"
        )
        
        request = InputValidationRequest(job_input=job_input)
        
        # Without audio validation, should not be ready
        self.assertFalse(request.is_ready_for_processing())
        
        # Add valid audio validation
        audio_validation = AudioFileValidation(
            file_path="/path/to/audio.wav",
            file_name="audio.wav",
            file_size=1024,
            file_format=".wav",
            valid=True
        )
        request.audio_validation = audio_validation
        
        # Now should be ready
        self.assertTrue(request.is_ready_for_processing())
    
    def test_transcription_request_validation_errors(self):
        """Test get_validation_errors method"""
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            audio_file="/path/to/audio.wav"
        )
        
        request = InputValidationRequest(job_input=job_input)
        
        # Should have validation errors for missing audio validation
        errors = request.get_validation_errors()
        self.assertIn("Audio file validation is required", errors[0])
    
    def test_batch_input_validation_creation(self):
        """Test BatchInputValidation model creation"""
        batch_input = BatchInputValidation(
            input_directory="examples/audio/voice",
            file_patterns=["*.wav", "*.mp3"],
            recursive=True,
            max_files=100,
            engine=TranscriptionEngine.OPTIMIZED_WHISPER,
            model="whisper-medium"
        )
        
        # The validator normalizes the path to absolute, so we check it contains the expected part
        self.assertIn("examples/audio/voice", batch_input.input_directory)
        self.assertEqual(batch_input.file_patterns, ["*.wav", "*.mp3"])
        self.assertTrue(batch_input.recursive)
        self.assertEqual(batch_input.max_files, 100)
        self.assertEqual(batch_input.engine, TranscriptionEngine.OPTIMIZED_WHISPER)
        self.assertEqual(batch_input.model, "whisper-medium")
    
    def test_batch_input_validation_file_patterns(self):
        """Test file pattern validation"""
        # Valid patterns
        batch_input = BatchInputValidation(
            input_directory="examples/audio/voice",
            file_patterns=["*.wav", "*.mp3", "[abc]*.wav"],
            engine=TranscriptionEngine.CUSTOM_WHISPER
        )
        self.assertEqual(len(batch_input.file_patterns), 3)
        
        # Invalid pattern should fail
        with self.assertRaises(ValueError) as context:
            BatchInputValidation(
                input_directory="examples/audio/voice",
                file_patterns=["*.wav", ""],  # Empty pattern
                engine=TranscriptionEngine.CUSTOM_WHISPER
            )
        
        self.assertIn("cannot be empty", str(context.exception))
    
    def test_model_serialization(self):
        """Test that models can be serialized to dict"""
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            audio_file="/path/to/audio.wav"
        )
        
        # Test serialization
        job_dict = job_input.model_dump()
        self.assertIsInstance(job_dict, dict)
        self.assertEqual(job_dict['datatype'], 'file')
        self.assertEqual(job_dict['engine'], 'custom-whisper')
        self.assertEqual(job_dict['audio_file'], '/path/to/audio.wav')
        
        # Test deserialization
        reconstructed = JobInputValidation.model_validate(job_dict)
        self.assertEqual(reconstructed.datatype, job_input.datatype)
        self.assertEqual(reconstructed.engine, job_input.engine)
        self.assertEqual(reconstructed.audio_file, job_input.audio_file)


if __name__ == "__main__":
    unittest.main()
