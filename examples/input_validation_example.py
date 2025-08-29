#!/usr/bin/env python3
"""
Example: Using Pydantic Models for Input Validation
Demonstrates how to validate inputs before processing using the new validation models
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    InputType,
    TranscriptionEngine,
    AudioFileValidation,
    JobInputValidation,
    InputValidationRequest,
    BatchInputValidation
)
from src.core.logic.input_validator_service import InputValidatorService
from src.models import AppConfig


def example_basic_validation():
    """Example of basic model validation"""
    print("🔍 Example 1: Basic Model Validation")
    print("=" * 50)
    
    try:
        # Create a valid job input
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.CUSTOM_WHISPER,
            model="whisper-large-v3",
            audio_file="/path/to/audio.wav"
        )
        print(f"✅ Valid job input created: {job_input.datatype} with {job_input.engine}")
        
        # Try to create an invalid job input (missing required field)
        try:
            invalid_job = JobInputValidation(
                datatype=InputType.FILE,
                engine=TranscriptionEngine.CUSTOM_WHISPER
                # Missing audio_file for FILE type
            )
        except ValueError as e:
            print(f"❌ Validation caught error: {e}")
        
        # Try to create an invalid job input (invalid engine)
        try:
            invalid_engine = JobInputValidation(
                datatype=InputType.FILE,
                engine="invalid-engine",  # Invalid engine
                audio_file="/path/to/audio.wav"
            )
        except ValueError as e:
            print(f"❌ Validation caught error: {e}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()


def example_transcription_request():
    """Example of complete transcription request validation"""
    print("🔍 Example 2: Complete Transcription Request Validation")
    print("=" * 50)
    
    try:
        # Create a valid transcription request
        job_input = JobInputValidation(
            datatype=InputType.FILE,
            engine=TranscriptionEngine.SPEAKER_DIARIZATION,
            model="whisper-large-v3",
            audio_file="/path/to/audio.wav"
        )
        
        request = InputValidationRequest(
            job_input=job_input,
            priority=5,
            config_overrides={"language": "he"}
        )
        
        print(f"✅ Valid request created with priority {request.priority}")
        print(f"   Input type: {request.job_input.datatype}")
        print(f"   Engine: {request.job_input.engine}")
        print(f"   Ready for processing: {request.is_ready_for_processing()}")
        
        # Check validation errors
        errors = request.get_validation_errors()
        if errors:
            print(f"❌ Validation errors: {errors}")
        else:
            print("✅ No validation errors")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


def example_batch_validation():
    """Example of batch input validation"""
    print("🔍 Example 3: Batch Input Validation")
    print("=" * 50)
    
    try:
        # Create a valid batch input
        batch_input = BatchInputValidation(
            input_directory="examples/audio/voice",
            file_patterns=["*.wav", "*.mp3"],
            recursive=True,
            max_files=100,
            engine=TranscriptionEngine.OPTIMIZED_WHISPER,
            model="whisper-medium"
        )
        
        print(f"✅ Valid batch input created")
        print(f"   Directory: {batch_input.input_directory}")
        print(f"   Patterns: {batch_input.file_patterns}")
        print(f"   Engine: {batch_input.engine}")
        print(f"   Max files: {batch_input.max_files}")
        
        # Try to create invalid batch input (non-existent directory)
        try:
            invalid_batch = BatchInputValidation(
                input_directory="/non/existent/path",
                engine=TranscriptionEngine.CUSTOM_WHISPER
            )
        except ValueError as e:
            print(f"❌ Validation caught error: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


def example_validation_service():
    """Example of using the InputValidatorService"""
    print("🔍 Example 4: Using InputValidatorService")
    print("=" * 50)
    
    try:
        # Create a mock config (in real usage, this would come from ConfigManager)
        config = AppConfig(environment="development")
        
        # Create the validator service
        validator = InputValidatorService(config)
        
        # Example job data
        job_data = {
            'input': {
                'type': 'file',
                'engine': 'speaker-diarization',
                'model': 'whisper-large-v3',
                'audio_file': '/path/to/audio.wav'
            },
            'priority': 3,
            'config_overrides': {'language': 'he'}
        }
        
        print("📋 Job data to validate:")
        print(f"   Type: {job_data['input']['type']}")
        print(f"   Engine: {job_data['input']['engine']}")
        print(f"   Model: {job_data['input']['model']}")
        print(f"   Priority: {job_data['priority']}")
        
        # Validate the job input
        try:
            validated_request = validator.validate_job_input(job_data)
            print("✅ Job input validation successful!")
            
            # Get validation summary
            summary = validator.get_validation_summary(validated_request)
            print(f"   Valid: {summary['valid']}")
            print(f"   Ready for processing: {summary['ready_for_processing']}")
            print(f"   Input type: {summary['input_type']}")
            print(f"   Engine: {summary['engine']}")
            
        except ValueError as e:
            print(f"❌ Validation failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


def example_field_validators():
    """Example of field-level validation"""
    print("🔍 Example 5: Field-Level Validation")
    print("=" * 50)
    
    try:
        # Test URL validation
        try:
            job_with_url = JobInputValidation(
                datatype=InputType.URL,
                engine=TranscriptionEngine.CUSTOM_WHISPER,
                url="https://example.com/audio.wav"
            )
            print(f"✅ Valid URL: {job_with_url.url}")
        except ValueError as e:
            print(f"❌ URL validation error: {e}")
        
        # Test invalid URL
        try:
            invalid_url_job = JobInputValidation(
                datatype=InputType.URL,
                engine=TranscriptionEngine.CUSTOM_WHISPER,
                url="invalid-url"
            )
        except ValueError as e:
            print(f"❌ Invalid URL caught: {e}")
        
        # Test model name validation
        try:
            job_with_model = JobInputValidation(
                datatype=InputType.FILE,
                engine=TranscriptionEngine.CUSTOM_WHISPER,
                model="whisper-large-v3",
                audio_file="/path/to/audio.wav"
            )
            print(f"✅ Valid model name: {job_with_model.model}")
        except ValueError as e:
            print(f"❌ Model validation error: {e}")
        
        # Test invalid model name
        try:
            invalid_model_job = JobInputValidation(
                datatype=InputType.FILE,
                engine=TranscriptionEngine.CUSTOM_WHISPER,
                model="invalid@model#name",
                audio_file="/path/to/audio.wav"
            )
        except ValueError as e:
            print(f"❌ Invalid model name caught: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


def main():
    """Run all examples"""
    print("🚀 Pydantic Input Validation Examples")
    print("=" * 60)
    print()
    
    example_basic_validation()
    example_transcription_request()
    example_batch_validation()
    example_validation_service()
    example_field_validators()
    
    print("✨ All examples completed!")
    print("\n💡 Key Benefits of Using Pydantic Models:")
    print("   • Automatic type validation and conversion")
    print("   • Built-in field validation with custom rules")
    print("   • Model-level validation for complex business logic")
    print("   • Clear error messages for validation failures")
    print("   • Integration with existing validation infrastructure")
    print("   • Follows SOLID principles and clean code practices")


if __name__ == "__main__":
    main()
