#!/usr/bin/env python3
"""
Simple chunk monitoring script
"""

import os
import json
import time
from pathlib import Path

def monitor_chunks():
    """Monitor chunk progress in real-time"""
    # Use definition.py for temp chunks directory
    try:
        from definition import TEMP_DIR
        temp_chunks_dir = TEMP_DIR
    except ImportError:
        temp_chunks_dir = "output/temp_chunks"
    
    if not os.path.exists(temp_chunks_dir):
        print("❌ No temp_chunks directory found")
        return
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🎤 TRANSCRIPTION CHUNK MONITOR")
        print("=" * 50)
        
        chunk_files = sorted([f for f in os.listdir(temp_chunks_dir) if f.endswith('.json')])
        
        if not chunk_files:
            print("⏳ Waiting for chunks to be created...")
            time.sleep(5)
            continue
        
        print(f"📁 Total chunks found: {len(chunk_files)}")
        print()
        
        # Count statuses
        statuses = {}
        for chunk_file in chunk_files:
            try:
                with open(os.path.join(temp_chunks_dir, chunk_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    status = data.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
            except Exception as e:
                print(f"❌ Error reading {chunk_file}: {e}")
        
        # Show summary
        print("📊 STATUS SUMMARY:")
        for status, count in sorted(statuses.items()):
            icon = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'error': '❌'
            }.get(status, '❓')
            print(f"  {icon} {status.capitalize()}: {count}")
        
        print()
        print("📋 DETAILED STATUS:")
        print("-" * 50)
        
        # Show detailed status for each chunk
        for chunk_file in chunk_files:
            try:
                with open(os.path.join(temp_chunks_dir, chunk_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                chunk_num = data.get('chunk_number', '?')
                status = data.get('status', 'unknown')
                start_time = data.get('start_time', 0)
                end_time = data.get('end_time', 0)
                text_length = len(data.get('text', ''))
                
                icon = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'completed': '✅',
                    'error': '❌'
                }.get(status, '❓')
                
                status_display = f"{icon} Chunk {chunk_num:2d} ({start_time:5.0f}s-{end_time:5.0f}s): {status}"
                
                if status == 'completed':
                    status_display += f" ({text_length} chars)"
                elif status == 'processing':
                    status_display += " 🔥"
                elif status == 'error':
                    error = data.get('error', 'Unknown error')
                    status_display += f" - {error}"
                
                print(status_display)
                
            except Exception as e:
                print(f"❌ Error reading {chunk_file}: {e}")
        
        print()
        print("🔄 Refreshing in 5 seconds... (Ctrl+C to stop)")
        time.sleep(5)

if __name__ == "__main__":
    try:
        monitor_chunks()
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
