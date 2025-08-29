# Input Validation with Pydantic Models

This guide explains how to use the new Pydantic input validation models to validate inputs before processing in your transcription application.

## Overview

The new input validation system provides:
- **Structured validation** using Pydantic models
- **Type safety** with automatic validation and conversion
- **Business logic validation** for complex input requirements
- **Integration** with existing validation infrastructure
- **SOLID principles** following clean code practices

## Available Models

### Core Validation Models

#### `InputType` Enum
```python
from src.models import InputType

# Valid input types
InputType.FILE      # "file"
InputType.BLOB      # "blob" 
InputType.URL       # "url"
```

#### `TranscriptionEngine` Enum
```python
from src.models import TranscriptionEngine

# Valid engines
TranscriptionEngine.STABLE_WHISPER        # "stable-whisper"
TranscriptionEngine.CUSTOM_WHISPER        # "custom-whisper"
TranscriptionEngine.OPTIMIZED_WHISPER     # "optimized-whisper"
TranscriptionEngine.SPEAKER_DIARIZATION   # "speaker-diarization"
TranscriptionEngine.CTTRANSLATE2_WHISPER  # "ctranslate2-whisper"
```

#### `JobInputValidation`
Validates individual job input parameters:
```python
from src.models import JobInputValidation, InputType, TranscriptionEngine

# File-based input
job_input = JobInputValidation(
    datatype=InputType.FILE,
    engine=TranscriptionEngine.CUSTOM_WHISPER,
    model="whisper-large-v3",
    audio_file="/path/to/audio.wav"
)

# URL-based input
job_input = JobInputValidation(
    datatype=InputType.URL,
    engine=TranscriptionEngine.SPEAKER_DIARIZATION,
    url="https://example.com/audio.wav"
)

# Blob-based input
job_input = JobInputValidation(
    datatype=InputType.BLOB,
    engine=TranscriptionEngine.CUSTOM_WHISPER,
    blob_data=b"audio_data_here"
)
```

#### `AudioFileValidation`
Validates audio file inputs:
```python
from src.models import AudioFileValidation

audio_validation = AudioFileValidation(
    file_path="/path/to/audio.wav",
    file_name="audio.wav",
    file_size=1024,
    file_format=".wav",
    valid=True
)
```

#### `InputValidationRequest`
Complete input validation request with validation:
```python
from src.models import InputValidationRequest

request = InputValidationRequest(
    job_input=job_input,
    priority=5,
    config_overrides={"language": "he"}
)

# Check if ready for processing
if request.is_ready_for_processing():
    # Process the request
    pass

# Get validation errors
errors = request.get_validation_errors()
```

#### `BatchInputValidation`
Validates batch processing inputs:
```python
from src.models import BatchInputValidation

batch_input = BatchInputValidation(
    input_directory="examples/audio/voice",
    file_patterns=["*.wav", "*.mp3"],
    recursive=True,
    max_files=100,
    engine=TranscriptionEngine.OPTIMIZED_WHISPER,
    model="whisper-medium"
)
```

## Integration Examples

### 1. Replace Existing Validation in JobValidator

**Before (existing code):**
```python
def validate_job_input(self, job: Dict[str, Any]) -> Optional[str]:
    input_data = job.get('input', {}) if isinstance(job, dict) else {}
    datatype = input_data.get('type', None)
    engine = input_data.get('engine', 'custom-whisper')
    
    if not datatype:
        return "datatype field not provided. Should be 'blob', 'url', or 'file'."
    
    if datatype not in ['blob', 'url', 'file']:
        return f"datatype should be 'blob', 'url', or 'file', but is {datatype} instead."
    
    if engine not in ['stable-whisper', 'custom-whisper', 'optimized-whisper', 'speaker-diarization']:
        return f"engine should be 'stable-whisper', 'custom-whisper', or 'optimized-whisper', but is {engine} instead."
    
    return None
```

**After (using Pydantic models):**
```python
from src.models import JobInputValidation, InputType, TranscriptionEngine

def validate_job_input(self, job: Dict[str, Any]) -> Optional[str]:
    try:
        input_data = job.get('input', {})
        
        # Use Pydantic model for validation
        job_input = JobInputValidation(
            datatype=input_data.get('type', 'file'),
            engine=input_data.get('engine', 'custom-whisper'),
            model=input_data.get('model'),
            audio_file=input_data.get('audio_file'),
            url=input_data.get('url'),
            blob_data=input_data.get('blob_data')
        )
        
        return None  # Validation passed
        
    except ValueError as e:
        return str(e)  # Return validation error
```

### 2. Use InputValidatorService for Comprehensive Validation

```python
from src.core.logic.input_validator_service import InputValidatorService

class YourService:
    def __init__(self, config: AppConfig):
        self.input_validator = InputValidatorService(config)
    
    def process_job(self, job_data: Dict[str, Any]):
        try:
            # Validate input before processing
            validated_request = self.input_validator.validate_job_input(job_data)
            
            # Check if ready for processing
            if validated_request.is_ready_for_processing():
                # Process the job
                result = self._process_transcription(validated_request)
                return result
            else:
                errors = validated_request.get_validation_errors()
                return {"error": f"Request not ready: {'; '.join(errors)}"}
                
        except ValueError as e:
            return {"error": f"Input validation failed: {e}"}
```

### 3. Validate Audio Files Before Processing

```python
def process_audio_file(self, file_path: str):
    try:
        # Validate audio file using Pydantic model
        audio_validation = self.input_validator.validate_audio_file(file_path)
        
        if audio_validation.valid:
            # File is valid, proceed with processing
            return self._transcribe_audio(audio_validation.file_path)
        else:
            return {"error": f"Audio file validation failed: {audio_validation.error}"}
            
    except ValueError as e:
        return {"error": f"Audio file validation failed: {e}"}
```

### 4. Batch Processing with Validation

```python
def process_batch(self, batch_config: Dict[str, Any]):
    try:
        # Validate batch configuration
        batch_input = self.input_validator.validate_batch_input(batch_config)
        
        # Process files in directory
        audio_files = self._discover_audio_files(
            batch_input.input_directory,
            batch_input.file_patterns,
            batch_input.recursive,
            batch_input.max_files
        )
        
        # Process each file with the specified engine
        results = []
        for file_path in audio_files:
            result = self._process_with_engine(
                file_path, 
                batch_input.engine, 
                batch_input.model
            )
            results.append(result)
            
        return results
        
    except ValueError as e:
        return {"error": f"Batch validation failed: {e}"}
```

## Error Handling

The Pydantic models provide clear error messages:

```python
try:
    job_input = JobInputValidation(
        datatype=InputType.FILE,
        engine="invalid-engine",  # This will fail
        audio_file="/path/to/audio.wav"
    )
except ValueError as e:
    print(f"Validation error: {e}")
    # Output: "Validation error: 1 validation error for JobInputValidation
    #          engine
    #            Input should be 'stable-whisper', 'custom-whisper', 
    #            'optimized-whisper', 'speaker-diarization' or 'ctranslate2-whisper'"
```

## Benefits of Using Pydantic Models

1. **Automatic Validation**: Type checking, range validation, format validation
2. **Clear Error Messages**: Detailed error information for debugging
3. **Type Safety**: IDE support and runtime type checking
4. **Business Logic Validation**: Complex validation rules in model validators
5. **Serialization**: Easy conversion to/from dictionaries and JSON
6. **Integration**: Works with existing validation infrastructure
7. **SOLID Principles**: Follows clean code practices and design patterns

## Migration Strategy

1. **Start Small**: Begin with one validation model (e.g., `JobInputValidation`)
2. **Gradual Replacement**: Replace existing validation logic one method at a time
3. **Test Thoroughly**: Use the provided unit tests to ensure correctness
4. **Update Interfaces**: Modify service interfaces to use validated models
5. **Monitor Performance**: Pydantic validation is fast but monitor for any impact

## Testing

The validation models include comprehensive unit tests:

```bash
# Run all input validation tests
python3 -m pytest tests/unit/test_input_validation_models.py -v

# Run specific test
python3 -m pytest tests/unit/test_input_validation_models.py::TestInputValidationModels::test_job_input_validation_file_type -v
```

## Example Script

Run the example script to see validation in action:

```bash
python3 examples/input_validation_example.py
```

This demonstrates all the validation features and error handling capabilities.
