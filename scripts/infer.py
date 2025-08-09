#!/usr/bin/env python3
"""
RunPod serverless handler for ivrit-ai voice transcription
Main entry point for RunPod serverless execution
"""

import runpod
from src.core.orchestrator.transcription_service import TranscriptionService

# Create global transcription service instance
transcription_service = TranscriptionService()

def transcribe(job):
    """
    RunPod serverless handler function
    Delegates to the transcription service
    """
    return transcription_service.transcribe(job)

# Start the RunPod serverless handler
if __name__ == "__main__":
    runpod.serverless.start({"handler": transcribe, "return_aggregate_stream": True})

