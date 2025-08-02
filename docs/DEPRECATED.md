# Deprecated Scripts

This file documents scripts that have been deprecated in favor of the unified `main.py` approach.

## Deprecated Entry Points

The following scripts are no longer the primary way to run the transcription service:

### `speaker_diarization.py` (formerly `transcribe_with_speakers.py`)
- **Status**: Deprecated as primary entry point
- **Replacement**: `python main.py --local <audio_file>`
- **Reason**: Functionality now integrated into unified main.py
- **Note**: Still used internally by main.py for local transcription

### `send_audio.py`
- **Status**: Deprecated as primary entry point  
- **Replacement**: `python main.py --runpod <audio_file>`
- **Reason**: Functionality now integrated into unified main.py
- **Note**: Still used internally by main.py for RunPod transcription

### `test_setup.py`
- **Status**: Deprecated as primary entry point
- **Replacement**: `python main.py --test`
- **Reason**: Functionality now integrated into unified main.py
- **Note**: Still used internally by main.py for testing

### `infer.py` (as direct entry point)
- **Status**: Deprecated as direct entry point
- **Replacement**: `python main.py --serverless`
- **Reason**: Now called through main.py for better error handling
- **Note**: Core logic still used, just wrapped by main.py

## Migration Guide

### Old Way (Deprecated)
```bash
# Local transcription
python speaker_diarization.py voice/audio.wav

# RunPod transcription  
python send_audio.py voice/audio.wav

# Test setup
python test_setup.py

# Serverless handler
python infer.py
```

### New Way (Recommended)
```bash
# Local transcription
python main.py --local voice/audio.wav

# RunPod transcription
python main.py --runpod voice/audio.wav

# Test setup
python main.py --test

# Serverless handler
python main.py --serverless

# Interactive quick start
python quick_start.py
```

## Benefits of the New Approach

1. **Unified Interface**: Single entry point for all functionality
2. **Better Error Handling**: Consistent error handling across all modes
3. **Configuration Management**: Centralized configuration display
4. **Interactive Mode**: Quick start script for easy onboarding
5. **Extensibility**: Easy to add new modes and options
6. **Documentation**: Built-in help and examples

## Backward Compatibility

The old scripts still work but are not recommended for new usage. They will eventually be removed in a future version. 