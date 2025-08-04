# Available ivrit-ai Models Summary

## 🎯 **Most Popular Models (By Downloads/Likes)**

### 1. **ivrit-ai/whisper-large-v3-ct2** ⭐⭐⭐
- **Downloads**: 6.4k
- **Likes**: 3
- **Updated**: May 22
- **Type**: CT2 optimized
- **Status**: **DEFAULT MODEL** in configuration

### 2. **ivrit-ai/whisper-large-v3-turbo-ct2** ⭐⭐⭐⭐⭐
- **Downloads**: 5.07k
- **Likes**: 10
- **Updated**: May 22
- **Type**: CT2 optimized, Turbo version
- **Status**: **FALLBACK MODEL** in configuration

### 3. **ivrit-ai/whisper-large-v3** ⭐⭐⭐⭐⭐
- **Downloads**: 2.72k
- **Likes**: 10
- **Category**: Automatic Speech Recognition
- **Size**: 2B parameters
- **Type**: Standard large-v3

### 4. **ivrit-ai/whisper-large-v3-turbo** ⭐⭐⭐⭐
- **Downloads**: 2.1k
- **Likes**: 8
- **Category**: Automatic Speech Recognition
- **Size**: 0.8B parameters
- **Type**: Turbo optimized

## 🆕 **Recent Models (May 2024)**

### 5. **ivrit-ai/whisper-large-v3-ggml** ⭐
- **Likes**: 1
- **Updated**: May 22
- **Type**: GGML optimized for CPU inference

### 6. **ivrit-ai/whisper-large-v3-turbo-ggml** ⭐⭐⭐⭐⭐⭐
- **Likes**: 6
- **Updated**: May 22
- **Type**: GGML optimized, Turbo version

## 📊 **Legacy Models**

### 7. **ivrit-ai/whisper-v2-d4** ⭐⭐
- **Downloads**: 9
- **Likes**: 2
- **Category**: Automatic Speech Recognition
- **Size**: 2B parameters

### 8. **ivrit-ai/faster-whisper-v2-d4** ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
- **Downloads**: 66
- **Likes**: 16
- **Category**: Automatic Speech Recognition
- **Updated**: September 2024

## 🔧 **Specialized Models**

### 9. **ivrit-ai/whisper-large-v3-turbo-onnx**
- **Downloads**: 8
- **Likes**: 1
- **Updated**: Feb 25
- **Type**: ONNX optimized

### 10. **ivrit-ai/whisper-large-v3-turbo-onnx-take2**
- **Downloads**: 3
- **Updated**: Feb 26
- **Type**: ONNX optimized (revised)

### 11. **ivrit-ai/whisper-large-v3-turbo_20250403_...** (truncated)
- **Downloads**: 3
- **Likes**: 1
- **Updated**: Apr 16
- **Type**: Turbo with specific date version

### 12. **ivrit-ai/whisper-v2-d4-ggml** ⭐
- **Likes**: 1
- **Updated**: Sep 11, 2024
- **Type**: GGML optimized v2

## 🎯 **Configuration Priority Order**

Based on popularity and performance, the models are configured in this priority order:

1. **ivrit-ai/whisper-large-v3-ct2** (Default - 6.4k downloads)
2. **ivrit-ai/whisper-large-v3-turbo-ct2** (Fallback - 5.07k downloads)
3. **ivrit-ai/whisper-large-v3** (Standard - 2.72k downloads)
4. **ivrit-ai/whisper-large-v3-turbo** (Turbo - 2.1k downloads)
5. **ivrit-ai/whisper-large-v3-ggml** (CPU optimized)
6. **ivrit-ai/whisper-large-v3-turbo-ggml** (CPU optimized Turbo)
7. **ivrit-ai/whisper-v2-d4** (Legacy v2)
8. **ivrit-ai/faster-whisper-v2-d4** (Faster-whisper optimized)
9. Standard Whisper models (large-v3, large-v2, large, medium, small, base, tiny)

## 📈 **Model Performance Insights**

- **CT2 Models**: Most popular, optimized for speed and memory efficiency
- **Turbo Models**: Faster inference with slightly reduced accuracy
- **GGML Models**: CPU-optimized for environments without GPU
- **ONNX Models**: Cross-platform compatibility
- **V2 Models**: Legacy versions with good community support

## 🔄 **Updated Configuration Files**

All environment configuration files have been updated to include these models:
- `config/environments/base.json`
- `config/environments/runpod.json`
- `config/environments/docker_batch.json`
- `config/environments/voice_task.json`

The default model is set to the most popular `ivrit-ai/whisper-large-v3-ct2` with `ivrit-ai/whisper-large-v3-turbo-ct2` as the fallback option. 