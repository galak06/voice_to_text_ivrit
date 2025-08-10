#!/usr/bin/env python3
"""
Test script to verify chunk writing with a smaller audio file
"""

import os
import subprocess
import time

def test_small_chunk():
    """Test chunk writing with a smaller audio file"""
    
    # Check if we have a smaller audio file
    small_audio = "examples/audio/voice/meeting_2.wav"  # We'll use a shorter duration
    
    if not os.path.exists(small_audio):
        print(f"❌ Audio file not found: {small_audio}")
        return
    
    print("🧪 Testing chunk writing with small audio file...")
    print(f"📁 Audio file: {small_audio}")
    print()
    
    # Clear temp chunks
    temp_dir = "output/temp_chunks"
    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            if filename.startswith("chunk_") and filename.endswith(".json"):
                os.remove(os.path.join(temp_dir, filename))
    
    # Start transcription in background
    print("🚀 Starting transcription...")
    process = subprocess.Popen([
        "python3", "main_app.py", "single", small_audio,
        "--model", "ivrit-ai/whisper-large-v3",
        "--engine", "custom-whisper"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Monitor for chunk files
    print("🔍 Monitoring for chunk files...")
    start_time = time.time()
    chunk_found = False
    
    try:
        while time.time() - start_time < 300:  # Wait up to 5 minutes
            # Check for chunk files
            if os.path.exists(temp_dir):
                chunk_files = [f for f in os.listdir(temp_dir) if f.startswith("chunk_") and f.endswith(".json")]
                if chunk_files:
                    print(f"✅ Found {len(chunk_files)} chunk files!")
                    for chunk_file in sorted(chunk_files):
                        chunk_path = os.path.join(temp_dir, chunk_file)
                        file_size = os.path.getsize(chunk_path)
                        print(f"   📄 {chunk_file} ({file_size} bytes)")
                    chunk_found = True
                    break
            
            # Check if process is still running
            if process.poll() is not None:
                print("❌ Process ended unexpectedly")
                break
            
            time.sleep(5)  # Check every 5 seconds
            print(f"⏱️  Waiting... ({int(time.time() - start_time)}s elapsed)")
        
        if not chunk_found:
            print("❌ No chunk files found within 5 minutes")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        process.terminate()
    
    # Clean up
    if process.poll() is None:
        process.terminate()
    
    print("\n🧹 Cleaning up...")
    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            if filename.startswith("chunk_") and filename.endswith(".json"):
                os.remove(os.path.join(temp_dir, filename))

if __name__ == "__main__":
    test_small_chunk() 