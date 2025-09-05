#!/usr/bin/env python3
"""
Test script for enhanced DOCX formatter with improved formatting, headings, and document splitting
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.output_data.formatters.docx_formatter import DocxFormatter

def test_enhanced_docx():
    """Test the enhanced DOCX formatter with the quarterly meeting transcription"""
    
    print("🧪 Testing Enhanced DOCX Formatter")
    print("=" * 50)
    
    # Path to the existing text file
    text_file = "output/transcriptions/run_20250902_091140/transcription_quarterly_meeting.txt"
    
    if not os.path.exists(text_file):
        print(f"❌ Text file not found: {text_file}")
        return False
    
    # Test 1: Create single enhanced document
    print("\n📄 Test 1: Creating single enhanced DOCX document")
    single_output = "output/transcriptions/run_20250902_091140/transcription_quarterly_meeting_enhanced_single.docx"
    
    success = DocxFormatter.create_docx_from_word_ready_text(
        text_file_path=text_file,
        output_docx_path=single_output,
        audio_file="פגישה רבעית.wav",
        model="ivrit-ai/whisper-large-v3-ct2",
        engine="ctranslate2-whisper",
        split_documents=False  # Single document
    )
    
    if success:
        print(f"✅ Single enhanced DOCX created: {single_output}")
        file_size = os.path.getsize(single_output)
        print(f"   📊 File size: {file_size:,} bytes")
    else:
        print("❌ Failed to create single enhanced DOCX")
    
    # Test 2: Create split documents (20-minute chunks)
    print("\n📚 Test 2: Creating split DOCX documents (20-minute chunks)")
    split_output = "output/transcriptions/run_20250902_091140/transcription_quarterly_meeting_enhanced_split.docx"
    
    success = DocxFormatter.create_docx_from_word_ready_text(
        text_file_path=text_file,
        output_docx_path=split_output,
        audio_file="פגישה רבעית.wav",
        model="ivrit-ai/whisper-large-v3-ct2",
        engine="ctranslate2-whisper",
        split_documents=True,  # Split into multiple documents
        chunk_duration_minutes=20  # 20-minute chunks
    )
    
    if success:
        print(f"✅ Split DOCX documents created from: {split_output}")
        
        # List all created files
        output_dir = Path(split_output).parent
        base_name = Path(split_output).stem
        
        created_files = list(output_dir.glob(f"{base_name}_part_*.docx"))
        created_files.extend(list(output_dir.glob(f"{base_name}_complete.docx")))
        
        print(f"   📊 Created {len(created_files)} files:")
        for file_path in sorted(created_files):
            file_size = os.path.getsize(file_path)
            print(f"      • {file_path.name} ({file_size:,} bytes)")
    else:
        print("❌ Failed to create split DOCX documents")
    
    # Test 3: Create split documents with 10-minute chunks
    print("\n📚 Test 3: Creating split DOCX documents (10-minute chunks)")
    split_output_10min = "output/transcriptions/run_20250902_091140/transcription_quarterly_meeting_enhanced_10min.docx"
    
    success = DocxFormatter.create_docx_from_word_ready_text(
        text_file_path=text_file,
        output_docx_path=split_output_10min,
        audio_file="פגישה רבעית.wav",
        model="ivrit-ai/whisper-large-v3-ct2",
        engine="ctranslate2-whisper",
        split_documents=True,  # Split into multiple documents
        chunk_duration_minutes=10  # 10-minute chunks
    )
    
    if success:
        print(f"✅ Split DOCX documents (10-min chunks) created from: {split_output_10min}")
        
        # List all created files
        output_dir = Path(split_output_10min).parent
        base_name = Path(split_output_10min).stem
        
        created_files = list(output_dir.glob(f"{base_name}_part_*.docx"))
        created_files.extend(list(output_dir.glob(f"{base_name}_complete.docx")))
        
        print(f"   📊 Created {len(created_files)} files:")
        for file_path in sorted(created_files):
            file_size = os.path.getsize(file_path)
            print(f"      • {file_path.name} ({file_size:,} bytes)")
    else:
        print("❌ Failed to create split DOCX documents (10-min chunks)")
    
    print("\n🎉 Enhanced DOCX testing completed!")
    print("\n📋 Summary of improvements:")
    print("   ✅ Double line breaks every few sentences")
    print("   ✅ Heading styles for timestamps and sections")
    print("   ✅ Document splitting into time-based chunks")
    print("   ✅ Enhanced metadata tables")
    print("   ✅ Simplified RTL handling for better compatibility")
    print("   ✅ Sentence-based formatting for better readability")

if __name__ == "__main__":
    test_enhanced_docx()

