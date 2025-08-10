#!/usr/bin/env python3
"""
Real-time progress monitoring for transcription chunks
"""

import os
import json
import time
import glob
from pathlib import Path

def monitor_progress():
    """Monitor transcription progress in real-time"""
    
    temp_dir = "output/temp_chunks"
    last_status = {}
    
    print("🔍 Real-time Transcription Progress Monitor")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        while True:
            # Clear screen (optional)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"⏰ {time.strftime('%H:%M:%S')} - Transcription Progress Monitor")
            print("=" * 60)
            
            if not os.path.exists(temp_dir):
                print("📁 No temp chunks directory found")
                time.sleep(5)
                continue
            
            # Find all chunk files
            chunk_files = glob.glob(os.path.join(temp_dir, "chunk_*.json"))
            
            if not chunk_files:
                print("📁 No chunk files found yet...")
                print("⏳ Waiting for transcription to start...")
                time.sleep(5)
                continue
            
            print(f"📁 Found {len(chunk_files)} chunk files:")
            print()
            
            completed_chunks = []
            processing_chunks = []
            total_words = 0
            total_chars = 0
            last_chunk_time = 0
            
            for chunk_file in sorted(chunk_files):
                try:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    chunk_num = data.get('chunk_number', '?')
                    start_time = data.get('start_time', 0)
                    end_time = data.get('end_time', 0)
                    text = data.get('text', '')
                    word_count = data.get('word_count', 0)
                    status = data.get('status', 'unknown')
                    timestamp = data.get('timestamp', 0)
                    
                    # Track last chunk time
                    if timestamp > last_chunk_time:
                        last_chunk_time = timestamp
                    
                    if status == 'completed' and text != "PROCESSING_IN_PROGRESS":
                        completed_chunks.append(chunk_num)
                        total_words += word_count
                        total_chars += len(text)
                        status_icon = "✅"
                        status_text = "COMPLETED"
                        print(f"{status_icon} Chunk {chunk_num:2d}: {start_time:6.0f}s - {end_time:6.0f}s ({status_text})")
                        print(f"    Words: {word_count:3d}, Chars: {len(text):4d}")
                        print(f"    Preview: {text[:50]}...")
                    elif status == 'processing' or text == "PROCESSING_IN_PROGRESS":
                        processing_chunks.append(chunk_num)
                        status_icon = "🔄"
                        status_text = "PROCESSING"
                        print(f"{status_icon} Chunk {chunk_num:2d}: {start_time:6.0f}s - {end_time:6.0f}s ({status_text})")
                        print(f"    Status: {status}")
                        print(f"    Started: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
                    else:
                        status_icon = "❓"
                        status_text = "UNKNOWN"
                        print(f"{status_icon} Chunk {chunk_num:2d}: {start_time:6.0f}s - {end_time:6.0f}s ({status_text})")
                        print(f"    Status: {status}, Text: {text[:30]}...")
                    
                    print()
                    
                except Exception as e:
                    print(f"❌ Error reading {chunk_file}: {e}")
            
            # Progress summary
            print("📊 PROGRESS SUMMARY:")
            print("=" * 60)
            
            if chunk_files:
                last_chunk_file = sorted(chunk_files)[-1]
                with open(last_chunk_file, 'r', encoding='utf-8') as f:
                    last_data = json.load(f)
                
                end_time = last_data.get('end_time', 0)
                total_duration = 6289  # From logs
                progress = (end_time / total_duration) * 100
                
                print(f"   Overall Progress: {progress:.1f}% ({end_time:.0f}s / {total_duration:.0f}s)")
                print(f"   Total chunks: {len(chunk_files)}")
                print(f"   Completed: {len(completed_chunks)} chunks")
                print(f"   Processing: {len(processing_chunks)} chunks")
                print(f"   Total words: {total_words}")
                print(f"   Total characters: {total_chars}")
                
                if completed_chunks:
                    print(f"   ✅ Completed chunks: {completed_chunks}")
                if processing_chunks:
                    print(f"   🔄 Processing chunks: {processing_chunks}")
                
                # Time since last activity
                if last_chunk_time > 0:
                    time_since_last = time.time() - last_chunk_time
                    print(f"   ⏰ Last activity: {time_since_last:.0f} seconds ago")
            
            print("=" * 60)
            print("🔄 Refreshing in 5 seconds... (Press Ctrl+C to stop)")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")
        
        # Final summary
        if chunk_files:
            print(f"\n📊 FINAL SUMMARY: {len(chunk_files)} chunks processed")
            
            if completed_chunks:
                print(f"✅ Successfully completed: {len(completed_chunks)} chunks")
            if processing_chunks:
                print(f"🔄 Still processing: {len(processing_chunks)} chunks")

if __name__ == "__main__":
    monitor_progress() 