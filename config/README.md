# Configuration Directory

This directory contains all configuration files for the ivrit-ai voice transcription service.

## 📁 Directory Structure

```
config/
├── README.md                    # This file
├── environments/                # Environment-specific configurations
│   ├── base.json               # Base configuration (defaults)
│   ├── development.json        # Development environment overrides
│   └── production.json         # Production environment overrides
└── templates/                   # Configuration templates
    ├── env_template.txt        # Environment variables template
    ├── environment-macos.yml   # Conda environment for macOS
    └── environment.yml         # Conda environment for Linux
```

## 🌍 Environment Configurations

### Base Configuration (`environments/base.json`)
Contains the default configuration values used by all environments. This includes:
- Transcription engine settings
- Speaker diarization parameters
- RunPod service configuration
- Output and logging settings
- System performance parameters

### Development Configuration (`environments/development.json`)
Overrides base configuration for development environment:
- Debug mode enabled
- Lower beam size for faster processing
- Higher timeout values
- DEBUG log level

### Production Configuration (`environments/production.json`)
Overrides base configuration for production environment:
- Debug mode disabled
- Higher beam size for better accuracy
- Optimized worker settings
- WARNING log level

## ⚙️ Configuration Loading

The configuration system loads configurations in this order:
1. **Base Configuration** - Loaded first as foundation
2. **Environment Configuration** - Merged with base (overrides)
3. **Environment Variables** - Final overrides for runtime

### Environment Variable Overrides

You can override any configuration value using environment variables:

```bash
# Set environment
export ENVIRONMENT=development

# Override specific values
export DEFAULT_MODEL=ivrit-ai/whisper-large-v3-ct2
export DEBUG=true
export LOG_LEVEL=DEBUG
export RUNPOD_API_KEY=your-api-key
export RUNPOD_ENDPOINT_ID=your-endpoint-id
```

## 🔧 Configuration Sections

### Transcription Configuration
- `default_model`: Default Whisper model to use
- `fallback_model`: Fallback model if default fails
- `default_engine`: Transcription engine (faster-whisper/stable-whisper)
- `beam_size`: Beam search size for accuracy/speed trade-off
- `language`: Default language for transcription
- `word_timestamps`: Enable word-level timestamps
- `vad_enabled`: Enable Voice Activity Detection
- `vad_min_silence_duration_ms`: Minimum silence duration

### Speaker Configuration
- `min_speakers`: Minimum number of speakers to detect
- `max_speakers`: Maximum number of speakers to detect
- `silence_threshold`: Silence threshold for speaker separation
- `beam_size`: Beam size for speaker diarization

### RunPod Configuration
- `api_key`: RunPod API key (from environment)
- `endpoint_id`: RunPod endpoint ID (from environment)
- `max_payload_size`: Maximum file size for upload
- `streaming_enabled`: Enable streaming responses
- `in_queue_timeout`: Timeout for queue operations
- `max_stream_timeouts`: Maximum stream timeouts
- `max_payload_len`: Maximum payload length

### Output Configuration
- `output_dir`: Base output directory
- `logs_dir`: Log files directory
- `transcriptions_dir`: Transcription output directory
- `temp_dir`: Temporary files directory
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `save_json`: Save transcriptions as JSON
- `save_txt`: Save transcriptions as text
- `save_docx`: Save transcriptions as Word documents
- `cleanup_temp_files`: Automatically clean up temp files
- `temp_file_retention_hours`: How long to keep temp files

### System Configuration
- `debug`: Enable debug mode
- `dev_mode`: Enable development mode
- `docker_image_name`: Docker image name
- `docker_tag`: Docker image tag
- `hugging_face_token`: Hugging Face token (from environment)
- `max_workers`: Maximum number of workers
- `timeout_seconds`: Request timeout
- `retry_attempts`: Number of retry attempts

## 📝 Usage Examples

### Python Usage
```python
from src.utils.config_manager import config_manager, config

# Get configuration
config_manager.print_config()

# Access specific settings
model = config.transcription.default_model
debug = config.system.debug
log_level = config.output.log_level
```

### Command Line Usage
```bash
# Show current configuration
python src/utils/config_manager.py

# Test configuration system
python scripts/test_config_system.py

# Create default configurations
python -c "from src.utils.config_manager import config_manager; config_manager.create_default_configs()"
```

## 🔄 Configuration Updates

To update configurations:

1. **Modify JSON files** in `environments/` directory
2. **Set environment variables** for runtime overrides
3. **Restart the application** to load new configurations

### Adding New Environments

1. Create a new JSON file in `environments/` (e.g., `staging.json`)
2. Add environment-specific overrides
3. Set `ENVIRONMENT=staging` to use the new configuration

### Adding New Configuration Sections

1. Add new dataclass in `src/utils/config_manager.py`
2. Update the `AppConfig` dataclass
3. Update the `_dict_to_config` method
4. Add configuration values to JSON files

## 🛡️ Security Notes

- **Never commit sensitive data** like API keys to version control
- **Use environment variables** for secrets and API keys
- **Template files** in `templates/` are safe to commit
- **Configuration files** may contain non-sensitive defaults

## 📚 Related Files

- `src/utils/config_manager.py` - Configuration management system
- `scripts/test_config_system.py` - Configuration testing
- `main.py` - Main application entry point
- `.env` - Local environment variables (not in version control) 