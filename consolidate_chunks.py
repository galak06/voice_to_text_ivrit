#!/usr/bin/env python3
"""
Script to consolidate chunk results into final transcription output
"""
import json
import os
import re
from datetime import datetime

def find_original_filename_from_logs():
    """Try to find the original audio filename from recent logs"""
    log_file = "output/logs/transcription.log"

    if not os.path.exists(log_file):
        return None

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Look for recent "Processing input file:" entries (search from end)
        for line in reversed(lines[-1000:]):  # Check last 1000 lines
            if "Processing input file:" in line:
                print(f"📋 Log line found: {line.strip()}")
                # Extract filename from log line - more flexible regex
                match = re.search(r'Processing input file: (.+)', line.strip())
                if match:
                    filepath = match.group(1)
                    # Get just the filename without extension
                    filename = os.path.splitext(os.path.basename(filepath))[0]
                    print(f"🔍 Found filename in logs: {filename}")
                    return filename

    except Exception as e:
        print(f"Warning: Could not read log file: {e}")

    return None

def consolidate_chunks(audio_filename=None):
    chunk_dir = "output/chunk_results"
    base_output_dir = "output/transcriptions"

    # Create timestamped run folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = f"run_{timestamp}"
    output_dir = os.path.join(base_output_dir, run_folder)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Creating output in: {output_dir}")
    
    # Get all chunk files dynamically
    chunk_files = []
    all_files = os.listdir(chunk_dir)
    chunk_numbers = []

    # Extract chunk numbers from all files
    for filename in all_files:
        if filename.startswith('chunk_') and filename.endswith('.json'):
            try:
                chunk_num = int(filename.split('_')[1])
                chunk_numbers.append(chunk_num)
            except (IndexError, ValueError):
                continue

    # Sort chunk numbers and process them
    chunk_numbers = sorted(chunk_numbers)
    print(f"Found {len(chunk_numbers)} chunks (chunk_{min(chunk_numbers):03d} to chunk_{max(chunk_numbers):03d})")

    for i in chunk_numbers:
        matching_files = [f for f in all_files if f.startswith(f"chunk_{i:03d}_")]
        if matching_files:
            chunk_files.append(os.path.join(chunk_dir, matching_files[0]))
        else:
            print(f"Warning: Missing chunk {i}")
    
    # Read and consolidate chunks
    consolidated_text = []
    chunk_data = []
    
    for chunk_file in sorted(chunk_files):
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk = json.load(f)
                
            if chunk.get('status') == 'completed' and chunk.get('text'):
                text = chunk['text'].strip()
                if text:
                    consolidated_text.append(text)
                    chunk_data.append({
                        'chunk_number': chunk['chunk_number'],
                        'start_time': chunk['start_time'],
                        'end_time': chunk['end_time'],
                        'text': text,
                        'word_count': len(text.split())
                    })
                    
        except Exception as e:
            print(f"Error processing {chunk_file}: {e}")
            continue
    
    # Create final consolidated text
    final_text = " ".join(consolidated_text)
    
    # Determine output filename (without additional timestamp since folder is timestamped)
    if audio_filename:
        # Remove extension and use original filename
        base_name = os.path.splitext(os.path.basename(audio_filename))[0]
        text_output = f"{output_dir}/{base_name}_transcription.txt"
        json_output = f"{output_dir}/{base_name}_transcription.json"
        print(f"📁 Using original filename: {base_name}")
    else:
        # Try to find original filename from logs
        base_name = find_original_filename_from_logs()
        if base_name:
            text_output = f"{output_dir}/{base_name}_transcription.txt"
            json_output = f"{output_dir}/{base_name}_transcription.json"
            print(f"📁 Using original filename: {base_name}")
        else:
            # Fallback to generic name
            text_output = f"{output_dir}/transcription.txt"
            json_output = f"{output_dir}/transcription.json"
            print("⚠️ Original filename not found, using generic name")

    # Save as text file
    with open(text_output, 'w', encoding='utf-8') as f:
        f.write(final_text)

    # Save as JSON with metadata
    output_data = {
        'metadata': {
            'timestamp': timestamp,
            'run_folder': run_folder,
            'original_audio_file': audio_filename,
            'total_chunks': len(chunk_data),
            'total_duration': chunk_data[-1]['end_time'] if chunk_data else 0,
            'total_words': sum(c['word_count'] for c in chunk_data),
            'total_characters': len(final_text)
        },
        'chunks': chunk_data,
        'full_text': final_text
    }
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Consolidation complete!")
    print(f"📁 Output folder: {output_dir}")
    print(f"📄 Text output: {os.path.basename(text_output)}")
    print(f"📊 JSON output: {os.path.basename(json_output)}")
    print(f"📈 Statistics:")
    print(f"   - Total chunks: {len(chunk_data)}")
    print(f"   - Total duration: {chunk_data[-1]['end_time']:.1f} seconds" if chunk_data else "   - No data")
    print(f"   - Total words: {sum(c['word_count'] for c in chunk_data)}")
    print(f"   - Total characters: {len(final_text)}")

    return text_output, json_output, output_dir

if __name__ == "__main__":
    consolidate_chunks()