# Development Setup for ivrit-ai RunPod Serverless

This guide helps you set up a local development environment for the ivrit-ai runpod serverless project.

## Prerequisites

- **Conda**: Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)
- **Docker**: Install [Docker Desktop](https://docs.docker.com/get-docker/) or Docker Engine
- **Git**: Install [Git](https://git-scm.com/)

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
./setup.sh
```

This script will:
- Create a conda environment with all dependencies
- Build the Docker image locally
- Provide next steps

### Option 2: Manual Setup

#### 1. Create Conda Environment

```bash
# Create environment from environment.yml
conda env create -f environment.yml

# Activate the environment
conda activate ivrit-ai-runpod
```

#### 2. Build Docker Image

```bash
# Build production image
docker build -t whisper-runpod-serverless .

# Build development image (with better caching)
docker build -f Dockerfile.dev -t whisper-runpod-serverless:dev .
```

## Environment Details

### Conda Environment (`ivrit-ai-runpod`)

The conda environment includes:
- **Python 3.11**: Latest stable Python version
- **PyTorch 2.4.1**: Deep learning framework with CUDA support
- **CUDA 12.1**: GPU acceleration support
- **cuDNN 9**: Deep learning primitives
- **Python packages**:
  - `runpod`: RunPod API client
  - `faster-whisper==1.1.1`: Optimized Whisper implementation
  - `stable-ts==2.18.3`: Stable timestamping for transcripts
  - `requests`: HTTP library

### Docker Images

#### Production Image (`whisper-runpod-serverless`)
- Based on PyTorch CUDA runtime
- Optimized for production deployment
- Pre-downloads models during build

#### Development Image (`whisper-runpod-serverless:dev`)
- Better layer caching for development
- Exposes port 8000 for debugging
- Includes all source code

## Usage

### Local Development

1. **Activate conda environment**:
   ```bash
   conda activate ivrit-ai-runpod
   ```

2. **Test the inference script**:
   ```bash
   python infer.py
   ```

3. **Use the client script** (requires RunPod endpoint):
   ```bash
   # Set environment variables
   export RUNPOD_API_KEY="your_api_key"
   export RUNPOD_ENDPOINT_ID="your_endpoint_id"
   
   # Run transcription
   python infer_client.py
   ```

### Docker Usage

1. **Test the Docker image**:
   ```bash
   docker run --rm -it whisper-runpod-serverless
   ```

2. **Run with GPU support** (if available):
   ```bash
   docker run --rm -it --gpus all whisper-runpod-serverless
   ```

3. **Mount local directory for development**:
   ```bash
   docker run --rm -it -v $(pwd):/app whisper-runpod-serverless:dev
   ```

## Model Information

The project supports two Hebrew transcription models:

1. **`ivrit-ai/whisper-large-v3-turbo-ct2`**: Fast, optimized model
2. **`ivrit-ai/whisper-large-v3-ct2`**: High-accuracy model

Both models are automatically downloaded during the Docker build process.

## Troubleshooting

### Common Issues

1. **CUDA not available**:
   - Ensure you have NVIDIA drivers installed
   - Check GPU availability: `nvidia-smi`
   - Use CPU fallback: The code automatically falls back to CPU

2. **Out of memory**:
   - Reduce batch size in the inference script
   - Use smaller models for testing

3. **Model download fails**:
   - Check internet connection
   - Verify Hugging Face access
   - Models are cached locally after first download

### Environment Management

```bash
# Update conda environment
conda env update -f environment.yml

# Remove environment
conda env remove -n ivrit-ai-runpod

# List environments
conda env list
```

## Next Steps

1. **Deploy to RunPod**: Follow the [main README](README.md) for RunPod deployment
2. **Customize Models**: Modify the model loading in `infer.py`
3. **Add Features**: Extend the transcription pipeline
4. **Optimize Performance**: Profile and optimize the inference code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the local environment
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 