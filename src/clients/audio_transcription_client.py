#!/usr/bin/env python3
"""
Audio transcription client for RunPod endpoint
"""

import os
import time
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.utils.config_manager import ConfigManager
from src.models import AppConfig

# Optional import for RunPod
try:
    import runpod
    RUNPOD_AVAILABLE = True
except ImportError:
    runpod = None
    RUNPOD_AVAILABLE = False


class AudioTranscriptionClient:
    """
    Client for sending audio files to RunPod endpoint for transcription
    
    This class follows the Single Responsibility Principle by handling
    audio file transcription through RunPod, with clear separation of
    concerns for validation, configuration, and processing.
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the audio transcription client
        
        Args:
            config: Optional application configuration
        """
        self.config = config or self._load_default_config()
        self.config_manager = ConfigManager()
        self.endpoint = None
        self._validate_configuration()
    
    def _load_default_config(self) -> AppConfig:
        """Load default configuration"""
        config_manager = ConfigManager()
        return config_manager.config
    
    def _validate_configuration(self) -> None:
        """Validate configuration and setup RunPod endpoint"""
        if not self.config_manager.validate():
            raise ValueError("Configuration validation failed! Please set up your environment variables first.")
        
        if not RUNPOD_AVAILABLE:
            raise ImportError("RunPod module not available. Please install it with: pip install runpod")
        
        if not self.config.runpod:
            raise ValueError("RunPod configuration not found!")
        
        # Configure RunPod
        if runpod is not None:  # Type check for linter
            runpod.api_key = self.config.runpod.api_key
            endpoint_id = self.config.runpod.endpoint_id
            if endpoint_id is None:
                raise ValueError("RunPod endpoint ID not configured!")
            self.endpoint = runpod.Endpoint(endpoint_id)
    
    def _validate_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Validate audio file and return file information
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary containing file information
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large
        """
        file_path = Path(audio_file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        file_size = file_path.stat().st_size
        
        if self.config.runpod and self.config.runpod.max_payload_size:
            max_size = self.config.runpod.max_payload_size
            if file_size > max_size:
                raise ValueError(
                    f"File too large! Max size: {max_size:,} bytes, "
                    f"actual size: {file_size:,} bytes"
                )
        
        return {
            'path': str(file_path),
            'size': file_size,
            'size_mb': file_size / 1024 / 1024
        }
    
    def _get_transcription_parameters(self, model: Optional[str] = None, engine: Optional[str] = None) -> Dict[str, str]:
        """
        Get transcription parameters with defaults
        
        Args:
            model: Optional model name
            engine: Optional engine name
            
        Returns:
            Dictionary with model and engine parameters
        """
        if self.config.transcription:
            default_model = self.config.transcription.default_model
            default_engine = self.config.transcription.default_engine
        else:
            default_model = "ivrit-ai/whisper-large-v3-ct2"
            default_engine = "faster-whisper"
        
        return {
            'model': model or default_model,
            'engine': engine or default_engine
        }
    
    def _prepare_audio_payload(self, audio_file_path: str, model: str, engine: str) -> Dict[str, Any]:
        """
        Prepare audio payload for RunPod
        
        Args:
            audio_file_path: Path to audio file
            model: Model to use
            engine: Engine to use
            
        Returns:
            Prepared payload dictionary
        """
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "input": {
                "type": "blob",
                "data": audio_data_b64,
                "model": model,
                "engine": engine,
                "streaming": self.config.runpod.streaming_enabled if self.config.runpod else False
            }
        }
    
    def _wait_for_queue(self, run_request, timeout_seconds: int = 300) -> str:
        """
        Wait for task to be queued and return status
        
        Args:
            run_request: RunPod request object
            timeout_seconds: Maximum time to wait
            
        Returns:
            Final status string
        """
        status = "UNKNOWN"
        for i in range(timeout_seconds):
            status = run_request.status()
            if status == "IN_QUEUE":
                time.sleep(1)
                continue
            break
        
        return status
    
    def _collect_transcription_results(self, run_request, max_timeouts: int = 5) -> List[Dict[str, Any]]:
        """
        Collect transcription results from RunPod
        
        Args:
            run_request: RunPod request object
            max_timeouts: Maximum number of timeouts allowed
            
        Returns:
            List of transcription segments
            
        Raises:
            RuntimeError: If too many timeouts occur
        """
        segments = []
        timeouts = 0
        
        while True:
            try:
                for segment in run_request.stream():
                    if "error" in segment:
                        raise RuntimeError(f"Transcription error: {segment['error']}")
                    
                    segments.append(segment)
                
                break  # Successfully completed
                
            except Exception as e:
                timeouts += 1
                if timeouts > max_timeouts:
                    raise RuntimeError(f"Too many timeouts ({max_timeouts})")
                
                time.sleep(1)
        
        return segments
    
    def _display_results(self, segments: List[Dict[str, Any]]) -> None:
        """
        Display transcription results
        
        Args:
            segments: List of transcription segments
        """
        print("\n🎉 Transcription completed!")
        print("=" * 50)
        
        if segments:
            for i, segment in enumerate(segments, 1):
                if 'text' in segment:
                    print(f"{i}. {segment['text']}")
                if 'start' in segment and 'end' in segment:
                    print(f"   Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
                print()
        else:
            print("No transcription segments received")
    
    def _save_outputs(self, audio_file_path: str, segments: List[Dict[str, Any]], 
                     model: str, engine: str) -> None:
        """
        Save transcription outputs in multiple formats
        
        Args:
            audio_file_path: Path to original audio file
            segments: Transcription segments
            model: Model used for transcription
            engine: Engine used for transcription
        """
        try:
            from src.output_data import OutputManager
            
            output_manager = OutputManager()
            
            # Save all formats using the unified method
            saved_files = output_manager.save_transcription(
                transcription_data=segments,
                audio_file=audio_file_path,
                model=model,
                engine=engine
            )
            
            print(f"💾 All formats saved:")
            for format_type, file_path in saved_files.items():
                print(f"   📄 {format_type.upper()}: {file_path}")
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to save outputs: {e}")
    
    def transcribe_audio(self, audio_file_path: str, model: Optional[str] = None, 
                        engine: Optional[str] = None, save_output: bool = True) -> bool:
        """
        Transcribe an audio file using RunPod
        
        Args:
            audio_file_path: Path to the audio file
            model: Optional model to use for transcription
            engine: Optional engine to use for transcription
            save_output: Whether to save outputs in all formats
            
        Returns:
            True if transcription was successful, False otherwise
        """
        try:
            # Validate audio file
            file_info = self._validate_audio_file(audio_file_path)
            print(f"📁 Audio file: {file_info['path']}")
            print(f"📊 File size: {file_info['size']:,} bytes ({file_info['size_mb']:.1f} MB)")
            
            # Get transcription parameters
            params = self._get_transcription_parameters(model, engine)
            print(f"🤖 Model: {params['model']}")
            print(f"⚙️  Engine: {params['engine']}")
            if self.config.runpod and self.config.runpod.endpoint_id:
                print(f"☁️  Endpoint: {self.config.runpod.endpoint_id}")
            
            # Prepare and send payload
            payload = self._prepare_audio_payload(audio_file_path, params['model'], params['engine'])
            print("🚀 Sending to RunPod endpoint...")
            
            if self.endpoint is None:
                raise RuntimeError("RunPod endpoint not initialized!")
            run_request = self.endpoint.run(payload)
            
            # Wait for task to be queued
            print("⏳ Waiting for task to be queued...")
            status = self._wait_for_queue(run_request)
            print(f"📊 Task status: {status}")
            
            # Collect results
            print("🎧 Collecting transcription results...")
            segments = self._collect_transcription_results(run_request)
            
            # Display results
            self._display_results(segments)
            
            # Save outputs if requested
            if save_output and segments:
                self._save_outputs(audio_file_path, segments, params['model'], params['engine'])
            elif not save_output:
                print("💾 Output saving disabled")
            
            return True
            
        except Exception as e:
            print(f"❌ Error transcribing audio file: {e}")
            return False





 