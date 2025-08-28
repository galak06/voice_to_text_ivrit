# 🎵 Voice-to-Text Transcription Quick Reference

## Quick Start

### Basic Usage
```bash
# Transcribe a single file with default settings
python run_single_transcription.py <audio_file>

# Example:
python run_single_transcription.py examples/audio/test/test_1min.wav
```

### Advanced Options
```bash
# Use specific model
python run_single_transcription.py <audio_file> --model <model_name>

# Use specific engine
python run_single_transcription.py <audio_file> --engine <engine_name>

# Use custom configuration
python run_single_transcription.py <audio_file> --config <config_file>

# Combine options
python run_single_transcription.py <audio_file> --model ivrit-ai/whisper-large-v3-ct2 --engine custom-whisper
```

## Available Models

- **Default**: Uses system default model
- **`ivrit-ai/whisper-large-v3-ct2`**: Hebrew-optimized Whisper model
- **`base`**: Standard Whisper base model
- **`small`**: Standard Whisper small model
- **`medium`**: Standard Whisper medium model
- **`large`**: Standard Whisper large model

## Available Engines

- **Default**: Uses system default engine
- **`custom-whisper`**: Custom Whisper implementation
- **`stable-whisper`**: Stable Whisper engine
- **`speaker-diarization`**: Speaker identification and diarization

## Example Commands

### Test Files
```bash
# Quick test (1 minute file)
python run_single_transcription.py examples/audio/test/test_1min.wav

# Meeting recording with Hebrew model
python run_single_transcription.py examples/audio/voice/meeting_extracted.wav --model ivrit-ai/whisper-large-v3-ct2

# Meeting recording with stable-whisper
python run_single_transcription.py examples/audio/voice/meeting_extracted.wav --engine stable-whisper
```

### Custom Audio Files
```bash
# Your own audio file
python run_single_transcription.py /path/to/your/audio.wav

# With specific model and engine
python run_single_transcription.py /path/to/your/audio.wav --model large --engine stable-whisper
```

## Run All Tests
```bash
# Execute comprehensive test suite
./test_transcription.sh
```

## Output

The script will display:
- ✅ Transcription progress
- 📝 Complete transcription text
- 📁 Generated output files
- ⏱️ Processing time
- 🎯 Performance metrics

## Troubleshooting

### Common Issues
1. **File not found**: Ensure audio file path is correct
2. **Model not found**: Check if model is properly installed
3. **Permission errors**: Ensure script is executable (`chmod +x run_single_transcription.py`)

### Verbose Logging
For detailed error information, check the application logs in `output/logs/`

## File Formats Supported
- WAV (recommended)
- MP3
- M4A
- FLAC
- OGG

## Performance Tips
- Use smaller audio files for quick testing
- Larger models provide better accuracy but slower processing
- Speaker diarization works best with clear audio and multiple speakers
