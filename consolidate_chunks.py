#!/usr/bin/env python3
"""
Script to consolidate chunk results into final transcription output
"""
import json
import os
from datetime import datetime

def consolidate_chunks():
    chunk_dir = "output/chunk_results"
    output_dir = "output/transcriptions"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all chunk files
    chunk_files = []
    for i in range(1, 233):  # chunks 1-232
        chunk_file = f"chunk_{i:03d}_*s_*s.json"
        matching_files = [f for f in os.listdir(chunk_dir) if f.startswith(f"chunk_{i:03d}_")]
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
    
    # Create timestamp for output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as text file
    text_output = f"{output_dir}/transcription_{timestamp}.txt"
    with open(text_output, 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    # Save as JSON with metadata
    json_output = f"{output_dir}/transcription_{timestamp}.json"
    output_data = {
        'metadata': {
            'timestamp': timestamp,
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
    print(f"📄 Text output: {text_output}")
    print(f"📊 JSON output: {json_output}")
    print(f"📈 Statistics:")
    print(f"   - Total chunks: {len(chunk_data)}")
    print(f"   - Total duration: {chunk_data[-1]['end_time']:.1f} seconds" if chunk_data else "   - No data")
    print(f"   - Total words: {sum(c['word_count'] for c in chunk_data)}")
    print(f"   - Total characters: {len(final_text)}")
    
    return text_output, json_output

if __name__ == "__main__":
    consolidate_chunks()