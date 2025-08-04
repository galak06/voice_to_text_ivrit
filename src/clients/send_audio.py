#!/usr/bin/env python3
"""
Script to send audio files to RunPod endpoint for transcription
"""

import os
import sys
import time
import base64
from pathlib import Path
from src.utils.config_manager import config_manager, config
import runpod

def send_audio_file(audio_file_path: str, model: str = None, engine: str = None, save_output: bool = True):
    """
    Send an audio file to RunPod endpoint for transcription
    
    Args:
        audio_file_path (str): Path to the audio file
        model (str): Model to use for transcription
        engine (str): Engine to use (faster-whisper or stable-whisper)
        save_output (bool): Whether to save outputs in all formats
    """
    
    # Validate configuration
    if not config_manager.validate():
        print("❌ Configuration validation failed!")
        print("Please set up your environment variables first.")
        return False
    
    # Check if file exists
    if not Path(audio_file_path).exists():
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    # Get file size
    file_size = Path(audio_file_path).stat().st_size
    print(f"📁 Audio file: {audio_file_path}")
    print(f"📊 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    
    # Check file size limit
    if file_size > config.runpod.max_payload_size:
        print(f"❌ File too large! Max size: {config.runpod.max_payload_size:,} bytes")
        return False
    
    # Use default values if not provided
    model = model or config.transcription.default_model
    engine = engine or config.transcription.default_engine
    
    print(f"🤖 Model: {model}")
    print(f"⚙️  Engine: {engine}")
    print(f"☁️  Endpoint: {config.runpod.endpoint_id}")
    
    try:
        # Configure RunPod
        runpod.api_key = config.runpod.api_key
        endpoint = runpod.Endpoint(config.runpod.endpoint_id)
        
        # Prepare payload
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        # Encode audio data as base64
        audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        payload = {
            "input": {
                "type": "blob",
                "data": audio_data_b64,
                "model": model,
                "engine": engine,
                "streaming": config.runpod.streaming_enabled
            }
        }
        
        print("🚀 Sending to RunPod endpoint...")
        
        # Send request
        run_request = endpoint.run(payload)
        
        # Wait for task to be queued
        print("⏳ Waiting for task to be queued...")
        for i in range(300):  # 5 minutes timeout
            status = run_request.status()
            if status == "IN_QUEUE":
                time.sleep(1)
                continue
            break
        
        print(f"📊 Task status: {status}")
        
        # Collect results
        print("🎧 Collecting transcription results...")
        segments = []
        
        timeouts = 0
        max_timeouts = 5
        
        while True:
            try:
                for segment in run_request.stream():
                    if "error" in segment:
                        print(f"❌ Error: {segment['error']}")
                        return False
                    
                    segments.append(segment)
                    print(f"📝 Segment: {segment}")
                
                break  # Successfully completed
                
            except Exception as e:
                timeouts += 1
                if timeouts > max_timeouts:
                    print(f"❌ Too many timeouts ({max_timeouts})")
                    return False
                print(f"⚠️  Timeout {timeouts}/{max_timeouts}, retrying...")
                time.sleep(1)
        
        # Display results
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
        
        # Save outputs in all formats if requested
        if save_output and segments:
            try:
                from src.output_data import OutputManager
                
                output_manager = OutputManager()
                
                # Save as JSON
                json_file = output_manager.save_transcription(
                    audio_file_path, segments, model, engine
                )
                
                # Save as text
                text_content = "\n".join([seg.get('text', '') for seg in segments if 'text' in seg])
                if text_content.strip():
                    text_file = output_manager.save_transcription_text(
                        audio_file_path, text_content, model, engine
                    )
                
                # Save as Word document
                docx_file = output_manager.save_transcription_docx(
                    audio_file_path, segments, model, engine
                )
                
                print(f"💾 All formats saved:")
                print(f"   📄 JSON: {json_file}")
                print(f"   📄 Text: {text_file}")
                if docx_file:
                    print(f"   📄 Word: {docx_file}")
                else:
                    print(f"   📄 Word: Skipped (python-docx not available)")
                    
            except Exception as e:
                print(f"⚠️  Warning: Failed to save outputs: {e}")
        elif not save_output:
            print("💾 Output saving disabled")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending audio file: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python send_audio.py <audio_file_path> [model] [engine]")
        print("Example: python send_audio.py voice/rachel_1.wav")
        print("Example: python send_audio.py voice/rachel_1.wav ivrit-ai/whisper-large-v3-turbo-ct2 faster-whisper")
        return
    
    audio_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None
    engine = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("🎤 ivrit-ai RunPod Audio Transcription")
    print("=" * 40)
    
    success = send_audio_file(audio_file, model, engine, save_output=True)
    
    if success:
        print("✅ Transcription completed successfully!")
    else:
        print("❌ Transcription failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 