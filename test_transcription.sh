#!/bin/bash

# Test Transcription Script
# This script demonstrates how to use the transcription system on different audio files

echo "🎵 Voice-to-Text Transcription Test Script"
echo "=========================================="
echo ""

# Test 1: Simple test file with default settings
echo "🧪 Test 1: Simple test file (default settings)"
echo "File: examples/audio/test/test_1min.wav"
echo "Command: python run_single_transcription.py examples/audio/test/test_1min.wav"
echo ""
python run_single_transcription.py examples/audio/test/test_1min.wav
echo ""
echo "----------------------------------------"
echo ""

# Test 2: Meeting file with Ivrit model
echo "🧪 Test 2: Meeting file with Ivrit model"
echo "File: examples/audio/voice/meeting_extracted.wav"
echo "Command: python run_single_transcription.py examples/audio/voice/meeting_extracted.wav --model ivrit-ai/whisper-large-v3-ct2"
echo ""
python run_single_transcription.py examples/audio/voice/meeting_extracted.wav --model ivrit-ai/whisper-large-v3-ct2
echo ""
echo "----------------------------------------"
echo ""

# Test 3: Meeting file with stable-whisper engine
echo "🧪 Test 3: Meeting file with stable-whisper engine"
echo "File: examples/audio/voice/meeting_extracted.wav"
echo "Command: python run_single_transcription.py examples/audio/voice/meeting_extracted.wav --engine stable-whisper"
echo ""
python run_single_transcription.py examples/audio/voice/meeting_extracted.wav --engine stable-whisper
echo ""
echo "----------------------------------------"
echo ""

echo "🎉 All tests completed!"
echo "Check the output above for transcription results."
