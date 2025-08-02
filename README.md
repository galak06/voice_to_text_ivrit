# Voice-to-Text Transcription Service

A comprehensive voice-to-text transcription service with support for Hebrew audio processing, speaker diarization, and multiple output formats. This project provides both local and cloud-based transcription capabilities using state-of-the-art AI models.

## 🎯 Features

- **Multi-Engine Support**: Faster-Whisper and Stable-Whisper engines
- **Speaker Diarization**: Automatic speaker identification and separation
- **Multiple Output Formats**: JSON, TXT, and Word Document outputs
- **Batch Processing**: Process multiple audio files efficiently
- **Local & Cloud Deployment**: Run locally or deploy to RunPod
- **Configurable Settings**: Environment-based configuration management
- **Hebrew Language Support**: Optimized for Hebrew audio transcription

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

**Local Transcription:**
```bash
# Transcribe a single audio file
python main.py --local examples/audio/voice/audio.wav

# With speaker diarization
python main.py --local examples/audio/voice/audio.wav --speaker-config conversation

# With specific model
python main.py --local examples/audio/voice/audio.wav --model ivrit-ai/whisper-large-v3-turbo-ct2
```

**Batch Processing:**
```bash
# Process all audio files in the voice directory
python main.py --batch-local

# Process with specific settings
python main.py --batch-local --model ivrit-ai/whisper-large-v3-turbo-ct2 --speaker-config conversation
```

## 📁 Project Structure

```
voice_to_text_ivrit/
├── main.py                           # 🎯 Unified entry point
├── infer.py                          # RunPod serverless handler
├── src/                              # 📦 Source code
│   ├── core/                         # Core transcription functionality
│   │   ├── transcription_service.py  # Main transcription service
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
│   │   ├── send_audio.py             # RunPod client
│   │   └── infer_client.py           # Inference client
│   └── tests/                        # Testing
│       └── test_setup.py             # Setup tests
├── scripts/                          # 🛠️ Scripts
│   ├── manage_outputs.py             # Output management
│   ├── setup.sh                      # Setup script
│   └── verify_batch_processing.py    # Batch processing verification
├── config/                           # ⚙️ Configuration directory
│   ├── environments/                 # Environment configurations
│   │   ├── base.json                # Base configuration
│   │   ├── development.json         # Development overrides
│   │   └── production.json          # Production overrides
│   ├── templates/                    # Configuration templates
│   │   ├── env_template.txt         # Environment variables template
│   │   ├── environment-macos.yml    # macOS conda environment
│   │   └── environment.yml          # Linux conda environment
│   └── README.md                     # Configuration documentation
├── docs/                             # 📚 Documentation
│   ├── MODULAR_STRUCTURE.md          # Modular structure guide
│   ├── DEPRECATED.md                 # Migration guide
│   └── DEVELOPMENT.md                # Development guide
├── tests/                            # 🧪 Test suite
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   ├── e2e/                          # End-to-end tests
│   └── run_tests.py                  # Test runner
├── examples/                         # 📁 Examples
│   ├── audio/                        # Audio files
│   │   └── voice/                    # Voice samples
│   └── output/                       # Output examples
├── output/                           # 📄 Generated outputs
│   ├── transcriptions/               # Transcription results
│   ├── logs/                         # Application logs
│   └── temp/                         # Temporary files
├── Dockerfile                        # 🐳 Docker configuration
├── Dockerfile.dev                    # Development Docker configuration
└── requirements.txt                  # 📦 Python dependencies
```

## 🎤 Usage Modes

### Local Transcription
Run transcription locally on your machine:
```bash
# Basic transcription
python main.py --local examples/audio/voice/audio.wav

# With speaker diarization
python main.py --local examples/audio/voice/audio.wav --speaker-config conversation

# With specific model and engine
python main.py --local examples/audio/voice/audio.wav --model ivrit-ai/whisper-large-v3-turbo-ct2 --engine faster-whisper
```

### Cloud Transcription (RunPod)
Run transcription via RunPod endpoint:
```bash
# Basic RunPod transcription
python main.py --runpod examples/audio/voice/audio.wav

# With specific settings
python main.py --runpod examples/audio/voice/audio.wav --model ivrit-ai/whisper-large-v3-turbo-ct2
```

### Batch Processing
Process all voice files in a directory:
```bash
# Process all files locally
python main.py --batch-local

# Process all files via RunPod
python main.py --batch-runpod

# With custom settings
python main.py --batch-local --model ivrit-ai/whisper-large-v3-turbo-ct2 --speaker-config conversation

# Custom voice directory
python main.py --batch-local --voice-dir /path/to/voice/files
```

### Serverless Handler
Run as RunPod serverless handler:
```bash
python main.py --serverless
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
python main.py --local audio.wav --speaker-config conversation

# Use interview preset
python main.py --local audio.wav --speaker-config interview
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
DEFAULT_MODEL=ivrit-ai/whisper-large-v3-turbo-ct2
FALLBACK_MODEL=ivrit-ai/whisper-large-v3-ct2

# Transcription Settings
DEFAULT_ENGINE=faster-whisper
MAX_PAYLOAD_SIZE=250000000
STREAMING_ENABLED=true

# System Settings
DEBUG=false
DEV_MODE=false
LOG_LEVEL=INFO
```

### Show Configuration
```bash
python main.py --config
```

## 🐳 Docker Deployment

### Build Docker Image
```bash
docker build -t voice-to-text-service .
```

### Run with Docker
```bash
# Run transcription in container
docker run --rm -v $(pwd)/examples/audio/voice:/app/voice -v $(pwd)/output:/app/output voice-to-text-service python main.py --local /app/voice/audio.wav

# Run serverless handler
docker run --rm -p 8000:8000 voice-to-text-service python main.py --serverless
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
python main.py --test
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
