#!/usr/bin/env python3
"""
Simple test script to send transcription request to local Docker server
"""
import requests
import json
import sys
from pathlib import Path

def send_transcription_request(audio_file, endpoint="http://localhost:8000", model="ivrit-ai/whisper-large-v3-turbo-ct2", engine="faster-whisper"):
    """Send transcription request to local server"""
    
    # Check if audio file exists
    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    # Prepare the request payload
    payload = {
        "input": {
            "audio_file": audio_file,
            "model": model,
            "engine": engine,
            "speaker_config": "conversation"
        }
    }
    
    try:
        print(f"🎤 Sending transcription request to {endpoint}")
        print(f"📁 Audio file: {audio_file}")
        print(f"🤖 Model: {model}")
        print(f"⚙️  Engine: {engine}")
        
        # Send POST request to the server
        response = requests.post(f"{endpoint}/run", json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription completed successfully!")
            print(f"📊 Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to server at {endpoint}")
        print("💡 Make sure the Docker container is running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_local_transcription.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    success = send_transcription_request(audio_file)
    
    if not success:
        sys.exit(1) 