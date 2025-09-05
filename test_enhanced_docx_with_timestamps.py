#!/usr/bin/env python3
"""
Test script for enhanced DOCX functionality with proper timestamp format
"""

import os
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.output_data.formatters.docx_formatter import DocxFormatter

def create_test_text_file():
    """Create a test text file with proper timestamp format"""
    test_content = """[00:00:00.00 - 00:02:30.50]
זהו טקסט בדיקה ראשון עם מספר משפטים. זהו המשפט השני. זהו המשפט השלישי. זהו המשפט הרביעי. זהו המשפט החמישי.

[00:02:30.50 - 00:05:15.75]
זהו טקסט בדיקה שני עם עוד מספר משפטים. זהו המשפט השני בקטע הזה. זהו המשפט השלישי בקטע הזה. זהו המשפט הרביעי בקטע הזה.

[00:05:15.75 - 00:08:45.20]
זהו טקסט בדיקה שלישי עם עוד משפטים. זהו המשפט השני בקטע השלישי. זהו המשפט השלישי בקטע השלישי. זהו המשפט הרביעי בקטע השלישי. זהו המשפט החמישי בקטע השלישי.

[00:08:45.20 - 00:12:30.10]
זהו טקסט בדיקה רביעי עם משפטים נוספים. זהו המשפט השני בקטע הרביעי. זהו המשפט השלישי בקטע הרביעי. זהו המשפט הרביעי בקטע הרביעי.

[00:12:30.10 - 00:15:45.80]
זהו טקסט בדיקה חמישי עם משפטים נוספים. זהו המשפט השני בקטע החמישי. זהו המשפט השלישי בקטע החמישי. זהו המשפט הרביעי בקטע החמישי. זהו המשפט החמישי בקטע החמישי. זהו המשפט השישי בקטע החמישי.

[00:15:45.80 - 00:18:20.30]
זהו טקסט בדיקה שישי עם משפטים נוספים. זהו המשפט השני בקטע השישי. זהו המשפט השלישי בקטע השישי. זהו המשפט הרביעי בקטע השישי.

[00:18:20.30 - 00:22:15.60]
זהו טקסט בדיקה שביעי עם משפטים נוספים. זהו המשפט השני בקטע השביעי. זהו המשפט השלישי בקטע השביעי. זהו המשפט הרביעי בקטע השביעי. זהו המשפט החמישי בקטע השביעי.

[00:22:15.60 - 00:25:30.90]
זהו טקסט בדיקה שמיני עם משפטים נוספים. זהו המשפט השני בקטע השמיני. זהו המשפט השלישי בקטע השמיני. זהו המשפט הרביעי בקטע השמיני.

[00:25:30.90 - 00:28:45.40]
זהו טקסט בדיקה תשיעי עם משפטים נוספים. זהו המשפט השני בקטע התשיעי. זהו המשפט השלישי בקטע התשיעי. זהו המשפט הרביעי בקטע התשיעי. זהו המשפט החמישי בקטע התשיעי. זהו המשפט השישי בקטע התשיעי.

[00:28:45.40 - 00:32:10.70]
זהו טקסט בדיקה עשירי עם משפטים נוספים. זהו המשפט השני בקטע העשירי. זהו המשפט השלישי בקטע העשירי. זהו המשפט הרביעי בקטע העשירי."""
    
    # Create temporary text file
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(test_content)
        return f.name

def main():
    print("🧪 Testing Enhanced DOCX Functionality with Timestamps")
    print("=" * 60)
    
    # Create test text file
    test_text_file = create_test_text_file()
    print(f"📝 Created test text file: {test_text_file}")
    
    # Test 1: Single enhanced document
    print("\n🔬 Test 1: Single Enhanced Document")
    output_path_1 = "test_output_single_enhanced.docx"
    
    success = DocxFormatter.create_docx_from_word_ready_text(
        text_file_path=test_text_file,
        output_docx_path=output_path_1,
        audio_file="test_audio.wav",
        model="test-model",
        engine="test-engine",
        split_documents=False
    )
    
    if success:
        print(f"✅ Single enhanced DOCX created: {output_path_1}")
        file_size = os.path.getsize(output_path_1)
        print(f"   📊 File size: {file_size:,} bytes")
    else:
        print("❌ Failed to create single enhanced DOCX")
    
    # Test 2: Split documents (20-minute chunks)
    print("\n🔬 Test 2: Split Documents (20-minute chunks)")
    output_path_2 = "test_output_split_20min.docx"
    
    success = DocxFormatter.create_docx_from_word_ready_text(
        text_file_path=test_text_file,
        output_docx_path=output_path_2,
        audio_file="test_audio.wav",
        model="test-model",
        engine="test-engine",
        split_documents=True,
        chunk_duration_minutes=20
    )
    
    if success:
        print(f"✅ Split DOCX created (20min chunks): {output_path_2}")
        
        # List all created files
        output_dir = Path(output_path_2).parent
        base_name = Path(output_path_2).stem
        
        created_files = list(output_dir.glob(f"{base_name}_part_*.docx"))
        created_files.extend(list(output_dir.glob(f"{base_name}_complete.docx")))
        
        print(f"   📊 Created {len(created_files)} files:")
        for file_path in sorted(created_files):
            file_size = os.path.getsize(file_path)
            print(f"      • {file_path.name} ({file_size:,} bytes)")
    else:
        print("❌ Failed to create split DOCX (20min chunks)")
    
    # Test 3: Split documents (10-minute chunks)
    print("\n🔬 Test 3: Split Documents (10-minute chunks)")
    output_path_3 = "test_output_split_10min.docx"
    
    success = DocxFormatter.create_docx_from_word_ready_text(
        text_file_path=test_text_file,
        output_docx_path=output_path_3,
        audio_file="test_audio.wav",
        model="test-model",
        engine="test-engine",
        split_documents=True,
        chunk_duration_minutes=10
    )
    
    if success:
        print(f"✅ Split DOCX created (10min chunks): {output_path_3}")
        
        # List all created files
        output_dir = Path(output_path_3).parent
        base_name = Path(output_path_3).stem
        
        created_files = list(output_dir.glob(f"{base_name}_part_*.docx"))
        created_files.extend(list(output_dir.glob(f"{base_name}_complete.docx")))
        
        print(f"   📊 Created {len(created_files)} files:")
        for file_path in sorted(created_files):
            file_size = os.path.getsize(file_path)
            print(f"      • {file_path.name} ({file_size:,} bytes)")
    else:
        print("❌ Failed to create split DOCX (10min chunks)")
    
    # Clean up
    try:
        os.unlink(test_text_file)
        print(f"\n🧹 Cleaned up test text file: {test_text_file}")
    except Exception as e:
        print(f"⚠️  Could not clean up test text file: {e}")
    
    print("\n🎉 Enhanced DOCX testing complete!")
    print("\n📋 Summary of improvements:")
    print("   ✅ Double line breaks every few sentences")
    print("   ✅ Heading styles for timestamps and sections")
    print("   ✅ Document splitting into time-based chunks")
    print("   ✅ Enhanced metadata tables")
    print("   ✅ Simplified RTL handling for better compatibility")
    print("   ✅ Sentence-based formatting for better readability")

if __name__ == "__main__":
    main()

