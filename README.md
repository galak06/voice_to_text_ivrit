# Voice-to-Text Transcription Application

A comprehensive voice-to-text transcription application with speaker diarization support, designed for Hebrew and other languages.

## Features

- **Multi-Engine Support**: Stable-Whisper engine with speaker diarization
- **Speaker Diarization**: Automatic speaker detection and separation
- **Batch Processing**: Process multiple audio files efficiently
- **Multiple Output Formats**: JSON, TXT, and DOCX output formats
- **Docker Support**: Containerized deployment with GPU acceleration
- **RunPod Integration**: Cloud deployment on RunPod serverless
- **Configuration Management**: Flexible configuration system
- **Progress Tracking**: Real-time processing progress updates

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker (for containerized deployment)
- Audio files in supported formats (WAV, MP3, M4A, FLAC, OGG, AAC)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/galak06/voice_to_text_ivrit.git
cd voice_to_text_ivrit
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up configuration:**
```bash
# Copy environment template
cp config/templates/env_template.txt .env

# Edit .env with your settings
nano .env
```

### Basic Usage

**Single File Processing:**
```bash
# Transcribe a single audio file with default configuration
python main_app.py single examples/audio/voice/audio.wav

# With specific model and engine
python main_app.py single examples/audio/voice/audio.wav --model base --engine speaker-diarization

# With speaker diarization preset
python main_app.py single examples/audio/voice/audio.wav --speaker-preset conversation
```

**Batch Processing:**
```bash
# Process all audio files with default configuration
python main_app.py batch

# With specific model
python main_app.py batch --model base --engine speaker-diarization

# Using voice folder optimized configuration
python main_app.py --config-file config/environments/voice_task.json batch

# Using Docker-enabled batch processing
python main_app.py --config-file config/environments/docker_batch.json batch
```

**Application Status:**
```bash
# Show application status and configuration
python main_app.py status

# Show configuration information
python main_app.py --help-config
```

## 📋 Configuration-Driven Architecture

All functionality is controlled through configuration files in `config/environments/`:

### Available Configurations

| Configuration | Purpose | Use Case |
|---------------|---------|----------|
| `base.json` | Default settings | General use |
| `voice_task.json` | Voice folder processing | Quick voice transcription |
| `docker_batch.json` | Docker-enabled batch | Advanced batch processing |
| `runpod.json` | RunPod cloud processing | Cloud transcription |
| `development.json` | Development settings | Development environment |
| `production.json` | Production settings | Production environment |

### Configuration Examples

**Voice Folder Processing:**
```bash
python main_app.py --config-file config/environments/voice_task.json batch
```

**Docker Batch Processing:**
```bash
python main_app.py --config-file config/environments/docker_batch.json batch
```

**RunPod Cloud Processing:**
```bash
python main_app.py --config-file config/environments/runpod.json batch
```

## 📁 Project Structure

```
voice_to_text_ivrit/
├── main_app.py                       # 🎯 Single entry point for all functionality
├── infer.py                          # RunPod serverless handler
├── src/                              # 📦 Source code
│   ├── core/                         # Core application components
│   │   ├── application.py            # Main application orchestrator
│   │   ├── input_processor.py        # Input file processing
│   │   ├── output_processor.py       # Output formatting and saving
│   │   ├── transcription_orchestrator.py # Transcription coordination
│   │   ├── transcription_service.py  # Core transcription service
│   │   ├── audio_file_processor.py   # Audio file processing
│   │   ├── job_validator.py          # Input validation
│   │   ├── speaker_diarization.py    # Speaker diarization service
│   │   └── speaker_transcription_service.py # Speaker transcription logic
│   ├── engines/                      # Transcription engines
│   │   ├── transcription_engine.py   # Engine protocol & implementations
│   │   └── transcription_engine_factory.py # Engine factory
│   ├── utils/                        # Utilities
│   │   ├── config_manager.py         # Configuration management
│   │   ├── output_manager.py         # Output file management
│   │   └── file_downloader.py        # File download functionality
│   ├── clients/                      # Client implementations
│   │   ├── audio_transcription_client.py  # RunPod client
│   │   └── infer_client.py           # Inference client
│   └── tests/                        # Testing
│       └── test_setup.py             # Setup tests
├── config/                           # ⚙️ Configuration directory
│   ├── environments/                 # Environment configurations
│   │   ├── base.json                # Base configuration
│   │   ├── voice_task.json          # Voice folder processing
│   │   ├── docker_batch.json        # Docker-enabled batch
│   │   ├── runpod.json              # RunPod cloud processing
│   │   ├── development.json         # Development overrides
│   │   └── production.json          # Production overrides
│   └── templates/                    # Configuration templates
│       └── env_template.txt         # Environment variables template
├── examples/                         # 📁 Example files
│   └── audio/                        # Sample audio files
│       └── voice/                    # Voice folder for processing
├── output/                           # 📤 Output directory
│   ├── transcriptions/               # Transcription results
│   ├── logs/                         # Application logs
│   └── temp/                         # Temporary files
├── tests/                            # 🧪 Test suite
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── e2e/                          # End-to-end tests
└── docs/                             # 📚 Documentation
    ├── CONSOLIDATED_ARCHITECTURE.md  # Architecture overview
    ├── MIGRATION_GUIDE.md            # Migration from old architecture
    ├── ENTRY_POINTS.md               # Entry points guide
    └── TEST_SUITE.md                 # Testing documentation
```

## 🎤 Usage Modes

### Local Transcription
Run transcription locally on your machine:
```bash
# Basic transcription
python main_app.py single examples/audio/voice/audio.wav

# With speaker diarization
python main_app.py single examples/audio/voice/audio.wav --speaker-preset conversation

# With specific model and engine
python main_app.py single examples/audio/voice/audio.wav --model base --engine faster-whisper
```

### Cloud Transcription (RunPod)
Run transcription via RunPod endpoint:
```bash
# Basic RunPod transcription
python main_app.py --config-file config/environments/runpod.json batch
```

### Batch Processing
Process all voice files in a directory:
```bash
# Process all files locally
python main_app.py batch

# Process all files via RunPod
python main_app.py --config-file config/environments/docker_batch.json batch

# With custom settings
python main_app.py --config-file config/environments/voice_task.json batch --speaker-preset conversation

# Custom voice directory
python main_app.py --config-file config/environments/voice_task.json batch --voice-dir /path/to/voice/files
```

### Serverless Handler
Run as RunPod serverless handler:
```bash
python main_app.py infer
```

## 📄 Output Formats

Every transcription automatically generates three output formats:

1. **JSON** (`.json`) - Complete transcription data with metadata, timestamps, and speaker information
2. **Text** (`.txt`) - Plain text transcription for easy reading
3. **Word Document** (`.docx`) - Formatted document organized by speakers

### Output Structure
```
output/transcriptions/
├── run_YYYYMMDD_HHMMSS/                    # Run session folder
│   ├── YYYYMMDD_HHMMSS_audiofile1/         # Individual audio file results
│   │   ├── transcription_model_engine.json
│   │   ├── transcription_model_engine.txt
│   │   └── transcription_model_engine.docx
│   └── YYYYMMDD_HHMMSS_audiofile2/         # Individual audio file results
│       ├── transcription_model_engine.json
│       ├── transcription_model_engine.txt
│       └── transcription_model_engine.docx
```

### Word Document Features
- **Conversation Format**: Clean, readable conversation layout
- **Speaker Organization**: Text grouped by speaker with bold speaker names
- **Combined Text**: All segments from each speaker combined for natural flow
- **No Technical Details**: Removed segment timestamps for clean reading

## 👥 Speaker Diarization

The service includes configurable speaker diarization with preset configurations:

### Available Presets
- **`default`** - Balanced configuration for most scenarios
- **`conversation`** - Sensitive to quick speaker changes, ideal for casual conversations
- **`interview`** - Allows for thinking pauses, optimized for formal interviews
- **`custom`** - Fast processing with moderate accuracy

### Usage
```bash
# Use conversation preset
python main_app.py single examples/audio/voice/audio.wav --speaker-preset conversation

# Use interview preset
python main_app.py single examples/audio/voice/audio.wav --speaker-preset interview
```

## ⚙️ Configuration

The project uses a hierarchical configuration system:

### Environment Configuration
- **Base Configuration**: `config/environments/base.json`
- **Development**: `config/environments/development.json`
- **Production**: `config/environments/production.json`

### Environment Variables
Set these in your `.env` file:
```bash
# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id_here

# Model Configuration
DEFAULT_MODEL=ivrit-ai/whisper-large-v3-ct2
FALLBACK_MODEL=ivrit-ai/whisper-large-v3-ct2

# Transcription Settings
DEFAULT_ENGINE=speaker-diarization
MAX_PAYLOAD_SIZE=250000000
STREAMING_ENABLED=true

# System Settings
DEBUG=false
DEV_MODE=false
LOG_LEVEL=INFO
```

### Show Configuration
```bash
python main_app.py --help-config
```

## 🐳 Docker Deployment

### Build Docker Image
```bash
docker build -t voice-to-text-service .
```

### Run with Docker
```bash
# Run transcription in container
docker run --rm -v $(pwd)/examples/audio/voice:/app/voice -v $(pwd)/output:/app/output voice-to-text-service python main_app.py single /app/voice/audio.wav

# Run serverless handler
docker run --rm -p 8000:8000 voice-to-text-service python main_app.py infer
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python tests/run_tests.py

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/
```

### Test Setup
```bash
# Test configuration and setup
python main_app.py --test
```

## 📊 Output Management

### Manage Outputs
```bash
# Show output statistics
python scripts/manage_outputs.py --stats

# List all transcription files
python scripts/manage_outputs.py --list

# Clean up temporary files
python scripts/manage_outputs.py --cleanup

# Show recent logs
python scripts/manage_outputs.py --logs
```

## 🔧 Development

### Project Architecture
The project follows SOLID principles and uses several design patterns:

- **Single Responsibility Principle**: Each class has a single, well-defined purpose
- **Open/Closed Principle**: New engines can be added without modifying existing code
- **Dependency Inversion**: High-level modules depend on abstractions
- **Factory Pattern**: Engine creation is handled by factories
- **Strategy Pattern**: Different transcription engines can be swapped

### Adding New Features
1. Follow the existing modular structure
2. Add appropriate tests in the `tests/` directory
3. Update configuration if needed
4. Document changes in relevant files

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built on top of state-of-the-art speech recognition models
- Inspired by the need for high-quality Hebrew transcription services
- Thanks to the open-source community for the underlying technologies

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the configuration examples in `config/`

---

**Note**: This project is designed for Hebrew audio transcription but can be adapted for other languages by changing the model configuration.
