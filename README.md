# runpod-serverless

[![RunPod](https://api.runpod.io/badge/ivrit-ai/runpod-serverless)](https://www.runpod.io/console/hub/ivrit-ai/runpod-serverless)

A template for quickly deploying an ivrit.ai Speech-to-text API.

Note: if you register at [runpod.io](https://runpod.io), we'd like to ask you to consider using our [referral link](https://runpod.io/?ref=06octndf).
It provides us with credits, which we can then use to provide better services.

## Description

This project provides a serverless solution for transcribing Hebrew audio files. It leverages runpod.io's infrastructure to process audio files efficiently and return transcriptions.
It is part of the [ivrit.ai](https://ivrit.ai) non-profit project.

## API: easy deployment through the Runpod hub

If you simply want to use our models via an API, quick deploy is avaialble via the RunPod hub.

1. Open this template on the hub by clicking [here](https://www.runpod.io/console/hub/ivrit-ai/runpod-serverless).
2. Click the "Deploy" button and create the endpoint.
3. Follow the instructions under the [Usage](#usage) section.

## Project Structure

```
voic_to_text_docker/
├── main.py                           # 🎯 Unified entry point
├── infer.py                          # RunPod serverless handler
├── src/                              # 📦 Source code
│   ├── core/                         # Core transcription functionality
│   │   ├── transcription_service.py  # Main transcription service
│   │   ├── audio_file_processor.py   # Audio file processing
│   │   ├── job_validator.py          # Input validation
│   │   └── speaker_diarization.py # Local transcription with speaker diarization
│   ├── engines/                      # Transcription engines
│   │   ├── transcription_engine.py   # Engine protocol & implementations
│   │   └── transcription_engine_factory.py # Engine factory
│   ├── utils/                        # Utilities
│   │   ├── config.py                 # Configuration management
│   │   └── file_downloader.py        # File download functionality
│   ├── clients/                      # Client implementations
│   │   ├── send_audio.py             # RunPod client
│   │   └── infer_client.py           # Inference client
│   └── tests/                        # Testing
│       ├── test_setup.py             # Setup tests
│       └── test_input.json           # Test data
├── scripts/                          # 🛠️ Scripts
│   ├── quick_start.py                # Interactive quick start
│   ├── setup.sh                      # Setup script
│   └── setup_env.sh                  # Environment setup
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
├── examples/                         # 📁 Examples
│   ├── audio/                        # Audio files
│   │   └── voice/                    # Voice samples
│   └── output/                       # Output examples
│       └── rachel_1_transcription.txt
├── Dockerfile                        # 🐳 Docker configuration
└── requirements.txt                  # 📦 Python dependencies
```

## Setting up your inference endpoint

1. Log in to [runpod.io]
2. Choose Menu->Serverless
3. Choose New Endpoint
4. Select the desired worker configuration.
   - You can choose the cheapest worker (16GB GPU, $0.00016/second as of August 1st, 2024).
   - Active workers can be 0, max workers is 1 or more.
   - GPUs/worker should be set to 1.
   - Container image should be set to **yairlifshitz/whisper-runpod-serverless:latest**, or your own Docker image (instruction later on how to build this).
   - Container disk should have at least 20 GB.
5. Click Deploy.

## Building your own Docker image

1. Clone this repository:

```
git clone https://github.com/ivrit-ai/runpod-serverless.git
cd runpod-serverless
```

2. Build the Docker image:

```
docker build -t whisper-runpod-serverless .
```

3. Push the image to a public Docker repository:

a. If you haven't already, create an account on [Docker Hub](https://hub.docker.com/).

b. Log in to Docker Hub from your command line:
   ```
   docker login
   ```

c. Tag your image with your Docker Hub username:
   ```
   docker tag whisper-runpod-serverless yourusername/whisper-runpod-serverless:latest
   ```

d. Push the image to Docker Hub:
   ```
   docker push yourusername/whisper-runpod-serverless:latest
   ```

4. Set up a serverless function on runpod.io using the pushed image.

## Quick Start

For an interactive experience, run the quick start script:
```bash
python quick_start.py
```

This will guide you through the available options and help you get started quickly.

## Usage

The service supports multiple execution modes through a unified `main.py` interface:

### 🎤 Local Transcription
Run transcription locally on your machine (creates JSON, TXT, DOCX):
```bash
# Basic local transcription
python main.py --local examples/audio/voice/audio.wav

# With specific model and engine
python main.py --local examples/audio/voice/audio.wav --model ivrit-ai/whisper-large-v3-turbo-ct2 --engine faster-whisper

# With speaker diarization configuration
python main.py --local examples/audio/voice/audio.wav --speaker-config conversation
python main.py --local examples/audio/voice/audio.wav --speaker-config interview
python main.py --local examples/audio/voice/audio.wav --speaker-config custom
```

### ☁️ RunPod Transcription
Run transcription via RunPod endpoint (creates JSON, TXT, DOCX):
```bash
# Basic RunPod transcription
python main.py --runpod examples/audio/voice/audio.wav

# With specific model and engine
python main.py --runpod examples/audio/voice/audio.wav --model ivrit-ai/whisper-large-v3-turbo-ct2 --engine stable-whisper
```

### 📦 Batch Processing
Process all voice files in the `examples/audio/voice/` directory:

```bash
# Process all files locally
python main.py --batch-local

# Process all files via RunPod
python main.py --batch-runpod

# With specific model and engine
python main.py --batch-local --model ivrit-ai/whisper-large-v3-turbo-ct2 --engine faster-whisper

# With speaker diarization
python main.py --batch-local --speaker-config conversation

# Custom voice directory
python main.py --batch-local --voice-dir /path/to/voice/files

# Without saving outputs (for testing)
python main.py --batch-local --no-save
```

**Batch Processing Features:**
- ✅ **Automatic file discovery** - Finds all supported audio formats (.wav, .mp3, .m4a, .flac, .ogg, .aac)
- ✅ **Individual processing** - Each file is processed separately with its own output folder
- ✅ **Progress tracking** - Shows current file and overall progress
- ✅ **Error handling** - Continues processing other files if one fails
- ✅ **Summary report** - Shows success/failure counts and lists failed files
- ✅ **All output formats** - Creates JSON, TXT, and DOCX for each file

### 🚀 Serverless Handler (Docker)
Run as RunPod serverless handler:
```bash
python main.py --serverless
```

### 🧪 Test Setup
Test your installation and configuration:
```bash
python main.py --test
```

### ⚙️ Show Configuration
Display current configuration:
```bash
python main.py --config
```

### 👥 Speaker Configuration Presets
View available speaker diarization configurations:
```bash
python main.py --speaker-presets
```

### 📁 Output Management
Manage transcription outputs and logs:
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

### 💾 Output Options
Control output saving:
```bash
# Save outputs (default)
python main.py --local examples/audio/voice/audio.wav

# Don't save outputs
python main.py --local examples/audio/voice/audio.wav --no-save
```

### 📄 Output Formats
**Every voice-to-text transcription automatically creates all three formats:**

1. **JSON** (`.json`) - Complete transcription data with metadata
2. **Text** (`.txt`) - Plain text transcription for easy reading
3. **Word Document** (`.docx`) - Formatted document organized by speakers with detailed segment information

**Output Structure:**
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
└── run_YYYYMMDD_HHMMSS_2/                  # Another run session
    └── ...
```

**Batch Processing:** All files from a single batch run are organized under one parent folder (`run_YYYYMMDD_HHMMSS/`).

**Word Document Structure:**
- **Metadata Section**: Audio file, model, engine, and timestamp information
- **Conversation Transcript**: Clean, readable conversation format
- **Speaker Format**: "Speaker: text" with bold speaker names
- **Combined Text**: All segments from each speaker combined for natural flow
- **No Technical Details**: Removed segment timestamps and word-level tables for clean reading

**Supported Transcription Methods:**
- ✅ **Local transcription** (`--local`) - Creates all formats
- ✅ **RunPod transcription** (`--runpod`) - Creates all formats
- ✅ **Batch local processing** (`--batch-local`) - Processes all voice files locally
- ✅ **Batch RunPod processing** (`--batch-runpod`) - Processes all voice files via RunPod  
- ✅ **Speaker diarization** - Creates all formats with speaker labels
- ✅ **Serverless handler** - Creates all formats

**Note**: Word document generation requires `python-docx` package, which is included in the requirements.

### 👥 Speaker Diarization Service

The system includes a configurable speaker diarization service with preset configurations:

#### **Available Presets:**
- **`default`** - Balanced configuration for most scenarios
- **`conversation`** - Sensitive to quick speaker changes, good for casual conversations
- **`interview`** - Allows for thinking pauses, optimized for formal interviews
- **`custom`** - Fast processing with moderate accuracy

#### **Configuration Parameters:**
- **`silence_threshold`** - Time gap to detect speaker change (1.0-2.5s)
- **`beam_size`** - Higher = more accurate but slower (3-7)
- **`min_speakers/max_speakers`** - Speaker count constraints
- **`vad_min_silence_duration_ms`** - Voice activity detection sensitivity

#### **Usage Examples:**
```python
from src.core.speaker_transcription_service import SpeakerTranscriptionService
from src.core.speaker_config_factory import SpeakerConfigFactory

# Use default configuration
service = SpeakerTranscriptionService()

# Use conversation configuration
conversation_config = SpeakerConfigFactory.get_config("conversation")
service = SpeakerTranscriptionService(conversation_config)

# Transcribe with speaker detection
result = service.speaker_diarization("audio.wav", "model-name")
```

### Using the RunPod endpoint programmatically

Once deployed on runpod.io, you can transcribe Hebrew audio either by providing a URL to transcribe (easily supports >1GB payloads, depending on Docker image's free disk space and timeout settings) or by uploading a file (up to ~5-10MB).

```python
from src.clients import infer_client
import os

os.environ["RUNPOD_API_KEY"] = "<your API key>"
os.environ["RUNPOD_ENDPOINT_ID"] = "<your endpoint ID>"

# Local file transcription (up to ~5MB)
local_segments = infer_client.transcribe("ivrit-ai/whisper-large-v3-turbo-ct2", "blob", "<your file>")

# URL-based transcription
url_segments = infer_client.transcribe("ivrit-ai/whisper-large-v3-turbo-ct2", "url", "<your URL>")
```

**Supported models**: `ivrit-ai/whisper-large-v3-ct2` and `ivrit-ai/whisper-large-v3-turbo-ct2`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
Patreon link: [here](https://www.patreon.com/ivrit_ai).

## License

Our code and model are released under the MIT license.

## Acknowledgements

- [Our long list of data contributors](https://www.ivrit.ai/en/credits)
- Our data annotation volunteers!
