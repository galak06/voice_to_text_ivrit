"""
Protocols for audio transcription components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Protocol
from .models import TranscriptionRequest


class AudioFileValidator(Protocol):
    """Protocol for audio file validation"""
    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file and return file information"""
        ...


class TranscriptionPayloadBuilder(Protocol):
    """Protocol for building transcription payloads"""
    def build(self, request: TranscriptionRequest) -> Dict[str, Any]:
        """Build payload for transcription request"""
        ...


class TranscriptionResultCollector(Protocol):
    """Protocol for collecting transcription results"""
    def collect(self, run_request, max_timeouts: int = 5) -> List[Dict[str, Any]]:
        """Collect transcription results"""
        ...


class OutputSaver(Protocol):
    """Protocol for saving transcription outputs"""
    def save(self, audio_file_path: str, segments: List[Dict[str, Any]], 
             model: str, engine: str) -> Dict[str, str]:
        """Save transcription outputs in multiple formats"""
        ...


class ResultDisplay(Protocol):
    """Protocol for displaying transcription results"""
    def display(self, segments: List[Dict[str, Any]]) -> None:
        """Display transcription results"""
        ...


class RunPodEndpoint(Protocol):
    """Protocol for RunPod endpoint operations"""
    def run(self, request_input: Dict[str, Any]) -> Any:
        """Run transcription request"""
        ...


class RunPodEndpointFactory(ABC):
    """Abstract factory for creating RunPod endpoints"""
    
    @abstractmethod
    def create_endpoint(self, endpoint_id: str) -> RunPodEndpoint:
        """Create a RunPod endpoint"""
        pass 