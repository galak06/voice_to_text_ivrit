# Unified Batch Transcription Script

## Overview

The `batch_transcribe_unified.py` script is a comprehensive solution that merges all batch transcription functionality from the existing scripts (`batch_transcribe.py`, `batch_transcribe_improved.py`, and `simple_batch_transcribe.py`) into a single, feature-rich application with parameter injection capabilities.

## Key Features

### 🎯 **Unified Functionality**
- Combines all features from existing batch transcription scripts
- Single entry point for all batch processing needs
- Consistent interface and behavior

### ⚙️ **Parameter Injection**
- Command-line argument support for all parameters
- JSON configuration file support
- Environment variable overrides
- Flexible parameter management

### 📊 **Progress Tracking**
- Real-time progress bars using `tqdm`
- File-specific status updates
- Processing time tracking
- Comprehensive error reporting

### 🔧 **Advanced Configuration**
- Multiple transcription engines support
- Customizable timeouts and delays
- Flexible input/output directory configuration
- Docker image customization

## Usage Examples

### Basic Usage
```bash
# Use default settings
python batch_transcribe_unified.py

# With verbose output
python batch_transcribe_unified.py --verbose
```

### Custom Parameters
```bash
# Custom model and engine
python batch_transcribe_unified.py \
  --model "openai/whisper-large-v3" \
  --engine "stable-ts" \
  --speaker-config "conversation"

# Custom directories
python batch_transcribe_unified.py \
  --input-dir "my_audio_files" \
  --output-dir "my_results"

# Custom timing
python batch_transcribe_unified.py \
  --timeout 7200 \
  --delay 30
```

### Configuration File
```bash
# Load from JSON configuration file
python batch_transcribe_unified.py --config config/batch_transcription_config.json

# Override config file with command line arguments
python batch_transcribe_unified.py \
  --config config/batch_transcription_config.json \
  --verbose \
  --timeout 1800
```

### Testing Mode
```bash
# Dry run to test configuration without actual transcription
python batch_transcribe_unified.py --dry-run --verbose
```

## Configuration Parameters

### Basic Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model` | `ivrit-ai/whisper-large-v3-turbo-ct2` | Whisper model to use |
| `--engine` | `faster-whisper` | Transcription engine |
| `--speaker-config` | `conversation` | Speaker diarization configuration |

### Timing Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--timeout` | `3600` | Timeout in seconds for each file |
| `--delay` | `10` | Delay between processing files |

### Directory Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--input-dir` | `examples/audio/voice` | Directory containing audio files |
| `--output-dir` | `output` | Directory for output files |

### Docker Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--docker-image` | `whisper-runpod-serverless:latest` | Docker image to use |

### Control Parameters
| Parameter | Description |
|-----------|-------------|
| `--verbose, -v` | Enable verbose output |
| `--dry-run` | Run without actual transcription |
| `--config` | Load configuration from JSON file |

## Configuration File Format

Create a JSON file with the following structure:

```json
{
  "model": "ivrit-ai/whisper-large-v3-turbo-ct2",
  "engine": "faster-whisper",
  "speaker_config": "conversation",
  "timeout": 3600,
  "delay_between_files": 10,
  "input_dir": "examples/audio/voice",
  "output_dir": "output",
  "docker_image": "whisper-runpod-serverless:latest",
  "verbose": true,
  "dry_run": false
}
```

## Design Patterns Implemented

### 🏗️ **Factory Pattern**
The `BatchTranscriptionConfig` class acts as a factory for creating configuration objects with different parameter combinations.

### 📋 **Strategy Pattern**
Different transcription engines and models can be injected as strategies, allowing for flexible processing approaches.

### 👁️ **Observer Pattern**
The progress bar observes the transcription process and updates its state accordingly.

### 🔧 **Builder Pattern**
The command-line argument parser builds complex configurations from simple parameter inputs.

## SOLID Principles Compliance

### ✅ **Single Responsibility Principle (SRP)**
- `BatchTranscriptionConfig`: Manages configuration only
- `BatchTranscriptionProcessor`: Handles processing logic only
- `parse_arguments()`: Handles argument parsing only

### ✅ **Open/Closed Principle (OCP)**
- Easy to extend with new engines, models, or output formats
- Configuration system allows adding new parameters without modifying core logic

### ✅ **Liskov Substitution Principle (LSP)**
- All configuration objects can be used interchangeably
- Progress bar interface is consistent across different implementations

### ✅ **Interface Segregation Principle (ISP)**
- Clean separation between configuration, processing, and output interfaces
- Optional parameters don't force unnecessary dependencies

### ✅ **Dependency Inversion Principle (DIP)**
- High-level modules depend on abstractions (configuration interface)
- Low-level modules (Docker commands) depend on high-level abstractions

## Type Annotations

The script uses comprehensive type annotations for better code clarity and IDE support:

```python
def run_docker_transcription(self, audio_file: str, pbar: Optional[tqdm] = None) -> Dict:
    """
    Run transcription for a single audio file using Docker
    
    Args:
        audio_file: Path to the audio file
        pbar: Optional progress bar for status updates
        
    Returns:
        Dictionary containing processing results
    """
```

## Error Handling

The script provides comprehensive error handling:

- **File Not Found**: Graceful handling of missing input directories
- **Docker Errors**: Detailed error messages for Docker execution failures
- **Timeout Handling**: Configurable timeouts with clear error reporting
- **Validation**: Input validation for all parameters

## Exit Codes

The script uses meaningful exit codes:

- `0`: All files processed successfully
- `1`: Critical error (missing files, configuration issues)
- `2`: Some files failed to process

## Migration from Old Scripts

### From `simple_batch_transcribe.py`
```bash
# Old
python simple_batch_transcribe.py

# New
python batch_transcribe_unified.py
```

### From `batch_transcribe.py`
```bash
# Old
python batch_transcribe.py

# New
python batch_transcribe_unified.py --verbose
```

### From `batch_transcribe_improved.py`
```bash
# Old
python batch_transcribe_improved.py

# New
python batch_transcribe_unified.py --verbose --timeout 3600
```

## Performance Considerations

- **Memory Efficiency**: Processes files one at a time to minimize memory usage
- **Progress Tracking**: Real-time updates without performance impact
- **Error Recovery**: Continues processing even if individual files fail
- **Resource Management**: Proper cleanup of Docker containers

## Future Enhancements

- Parallel processing support
- Cloud storage integration
- Advanced error recovery mechanisms
- Web interface for configuration
- Integration with CI/CD pipelines 