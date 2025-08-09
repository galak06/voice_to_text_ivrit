# Configuration Guide

This guide explains the engine-model mapping and how to configure the transcription system for different use cases.

## Engine-Model Compatibility

### 1. Stable Whisper Engine (`stable-whisper`)

**Compatible Models:**
- Standard Whisper models: `tiny.en`, `tiny`, `base.en`, `base`, `small.en`, `small`, `medium.en`, `medium`, `large-v1`, `large-v2`, `large-v3`, `large`, `large-v3-turbo`, `turbo`

**Best For:**
- Standard English/Hebrew transcription
- General-purpose transcription
- Lower memory usage requirements
- Fast processing with official Whisper models

**Configuration File:** `config/environments/stable_whisper.json`

### 2. Custom Whisper Engine (`custom-whisper`)

**Compatible Models:**
- Hugging Face models: `ivrit-ai/whisper-large-v3`, `ivrit-ai/whisper-large-v3-turbo`, `ivrit-ai/whisper-v2-d4`, `ivrit-ai/whisper-large-v3-ggml`, `ivrit-ai/whisper-large-v3-turbo-ggml`

**Best For:**
- Hebrew-optimized transcription
- Custom fine-tuned models
- High accuracy requirements
- Hugging Face model support

**Configuration File:** `config/environments/custom_whisper.json`

### 3. Optimized Whisper Engine (`optimized-whisper`)

**Compatible Models:**
- CTranslate2 optimized models: `ivrit-ai/whisper-large-v3-turbo-ct2`, `large-v3-ct2`, `large-v2-ct2`, `medium-ct2`, `small-ct2`

**Best For:**
- High-performance transcription
- Lower memory usage
- Faster inference
- CTranslate2 optimized models

**Configuration File:** `config/environments/optimized_whisper.json`

## Model Recommendations by Use Case

### Hebrew Transcription

| Use Case | Model | Engine | Description |
|----------|-------|--------|-------------|
| **Best Accuracy** | `ivrit-ai/whisper-large-v3` | `custom-whisper` | Highest Hebrew accuracy, slower processing |
| **Balanced** | `ivrit-ai/whisper-large-v3-turbo` | `custom-whisper` | Good accuracy, faster processing |
| **Fast** | `ivrit-ai/whisper-large-v3-turbo-ct2` | `optimized-whisper` | Fast processing with CTranslate2 optimization |

### English/Multilingual Transcription

| Use Case | Model | Engine | Description |
|----------|-------|--------|-------------|
| **Fast** | `medium` | `stable-whisper` | Fast processing with good accuracy |
| **Balanced** | `large-v3` | `stable-whisper` | Balanced speed and accuracy |
| **Accurate** | `large-v3` | `stable-whisper` | Highest accuracy, slower processing |

### Performance-Optimized

| Use Case | Model | Engine | Description |
|----------|-------|--------|-------------|
| **Ultra Fast** | `small-ct2` | `optimized-whisper` | Ultra-fast processing, lower accuracy |
| **Fast** | `medium-ct2` | `optimized-whisper` | Fast processing, good accuracy |
| **Balanced** | `large-v3-ct2` | `optimized-whisper` | Balanced speed and accuracy |

## Configuration Files

### Base Configuration (`base.json`)
- Contains the main configuration with engine-model mapping
- Defines available engines and their compatible models
- Provides model recommendations for different use cases

### Engine-Specific Configurations

#### `stable_whisper.json`
- Optimized for standard Whisper models
- Performance settings for different speed/accuracy trade-offs
- Memory optimization settings

#### `custom_whisper.json`
- Optimized for Hebrew transcription
- Hebrew-specific optimization parameters
- Memory management for Hugging Face models

#### `optimized_whisper.json`
- CTranslate2 specific optimizations
- Performance tuning parameters
- Memory and CPU optimization settings

### Use Case Configurations

#### `ivrit.json`
- Optimized for Hebrew transcription
- Multiple model recommendations
- Hebrew-specific speaker diarization settings

## Usage Examples

### 1. Hebrew Transcription with Best Accuracy

```bash
# Use the ivrit configuration
python main_app.py --config config/environments/ivrit.json

# Or specify model and engine directly
python main_app.py --engine custom-whisper --model ivrit-ai/whisper-large-v3
```

### 2. Fast English Transcription

```bash
# Use stable whisper configuration
python main_app.py --config config/environments/stable_whisper.json

# Or specify model and engine directly
python main_app.py --engine stable-whisper --model medium
```

### 3. High-Performance Hebrew Transcription

```bash
# Use optimized whisper configuration
python main_app.py --config config/environments/optimized_whisper.json

# Or specify model and engine directly
python main_app.py --engine optimized-whisper --model ivrit-ai/whisper-large-v3-turbo-ct2
```

## Configuration Structure

Each configuration file follows this structure:

```json
{
  "transcription": {
    "engine": "engine-name",
    "default_model": "model-name",
    "fallback_model": "fallback-model",
    "available_models": ["model1", "model2"],
    "model_recommendations": {
      "use_case": {
        "model": "model-name",
        "engine": "engine-name",
        "description": "Description"
      }
    }
  },
  "speaker": {
    "min_speakers": 2,
    "max_speakers": 4,
    "presets": {
      "conversation": { ... },
      "interview": { ... }
    }
  },
  "output": {
    "formats": ["json", "txt", "docx"],
    "output_directory": "path/to/output"
  },
  "processing": {
    "batch_size": 1,
    "chunk_duration": 120,
    "memory_optimization": true
  }
}
```

## Performance Considerations

### Memory Usage
- **Stable Whisper**: Lowest memory usage
- **Custom Whisper**: Highest memory usage (Hugging Face models)
- **Optimized Whisper**: Moderate memory usage (CTranslate2 optimization)

### Processing Speed
- **Stable Whisper**: Fast for standard models
- **Custom Whisper**: Slower (high accuracy models)
- **Optimized Whisper**: Fastest (CTranslate2 optimization)

### Accuracy
- **Stable Whisper**: Good for general transcription
- **Custom Whisper**: Best for Hebrew and specialized models
- **Optimized Whisper**: Good balance of speed and accuracy

## Troubleshooting

### Model Not Found
- Ensure the model is compatible with the selected engine
- Check if the model is available in the engine's `available_models` list
- Verify model name spelling and format

### Memory Issues
- Use smaller models or the optimized-whisper engine
- Enable memory optimization settings
- Reduce batch size or chunk duration

### Performance Issues
- Choose appropriate engine-model combination for your use case
- Adjust beam size and other performance parameters
- Consider using CTranslate2 optimized models for better performance 