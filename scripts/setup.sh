#!/bin/bash

# Setup script for ivrit-ai runpod serverless project
# This script creates a conda environment and builds the Docker image locally

set -e

echo "🚀 Setting up ivrit-ai runpod serverless development environment..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed. Please install conda first."
    echo "   Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "📦 Creating conda environment..."

# Detect macOS and use appropriate environment file
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS, using CPU-only environment..."
    conda env create -f config/templates/environment-macos.yml
else
    echo "🐧 Using full environment with CUDA support..."
    conda env create -f config/templates/environment.yml
fi

# Update success message based on environment created
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ Conda environment 'ivrit-ai-runpod-macos' created successfully!"
else
    echo "✅ Conda environment 'ivrit-ai-runpod' created successfully!"
fi

echo "🐳 Building Docker image..."
docker build -t whisper-runpod-serverless .

echo "✅ Docker image 'whisper-runpod-serverless' built successfully!"

echo ""
echo "🎉 Setup complete! Here's what you can do next:"
echo ""
echo "1. Activate the conda environment:"
echo "   conda activate ivrit-ai-runpod"
echo ""
echo "2. Quick start (interactive):"
echo "   python scripts/quick_start.py"
echo ""
echo "3. Test the setup:"
echo "   python main.py --test"
echo ""
echo "4. Run local transcription:"
echo "   python main.py --local examples/audio/voice/your_audio.wav"
echo ""
echo "5. Test the Docker image locally:"
echo "   docker run --rm -it whisper-runpod-serverless"
echo ""
echo "6. Push to Docker Hub (optional):"
echo "   docker tag whisper-runpod-serverless yourusername/whisper-runpod-serverless:latest"
echo "   docker push yourusername/whisper-runpod-serverless:latest"
echo ""
echo "7. Use RunPod transcription (after setting up endpoint):"
echo "   python main.py --runpod examples/audio/voice/your_audio.wav" 