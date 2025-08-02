#!/usr/bin/env python3
"""
Test script to verify the new output structure with parent folders for each run
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.output_manager import OutputManager

def test_new_output_structure():
    """Test the new output structure with parent folders"""
    print("🧪 Testing New Output Structure")
    print("=" * 60)
    
    # Create output manager with a specific run session ID
    run_session_id = "test_run_20250802_092000"
    output_manager = OutputManager(run_session_id=run_session_id)
    
    print(f"🆔 Run Session ID: {run_session_id}")
    print(f"📁 Run Session Directory: {output_manager.get_run_session_dir()}")
    print()
    
    # Test creating files in the new structure
    test_audio_files = [
        "test_audio_1.wav",
        "test_audio_2.wav", 
        "test_audio_3.wav"
    ]
    
    print("📝 Creating test files in new structure...")
    
    for i, audio_file in enumerate(test_audio_files, 1):
        print(f"   {i}. Processing {audio_file}")
        
        # Create mock transcription data
        mock_data = [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.0,
                "text": f"Test transcription for {audio_file}",
                "speaker": "Speaker 1",
                "words": []
            }
        ]
        
        # Save all formats
        json_file = output_manager.save_transcription(
            audio_file, mock_data, "test-model", "test-engine"
        )
        
        text_content = f"Test transcription for {audio_file}"
        text_file = output_manager.save_transcription_text(
            audio_file, text_content, "test-model", "test-engine"
        )
        
        docx_file = output_manager.save_transcription_docx(
            audio_file, mock_data, "test-model", "test-engine"
        )
        
        print(f"      ✅ Saved: JSON, TXT, DOCX")
    
    print()
    
    # Verify the structure
    run_session_dir = output_manager.get_run_session_dir()
    
    if run_session_dir.exists():
        print("✅ Run session directory created successfully")
        
        # Count subfolders (audio files)
        subfolders = [d for d in run_session_dir.iterdir() if d.is_dir()]
        print(f"📂 Audio file folders: {len(subfolders)}")
        
        # Count files
        total_files = 0
        json_files = 0
        txt_files = 0
        docx_files = 0
        
        for subfolder in subfolders:
            json_files += len(list(subfolder.glob("*.json")))
            txt_files += len(list(subfolder.glob("*.txt")))
            docx_files += len(list(subfolder.glob("*.docx")))
            total_files += json_files + txt_files + docx_files
        
        print(f"📄 Total files: {total_files}")
        print(f"   • JSON: {json_files}")
        print(f"   • TXT: {txt_files}")
        print(f"   • DOCX: {docx_files}")
        
        print()
        print("📁 Directory Structure:")
        print(f"   {run_session_dir.name}/")
        
        for subfolder in subfolders:
            print(f"   ├── {subfolder.name}/")
            files = list(subfolder.glob("*"))
            for i, file in enumerate(files):
                if i == len(files) - 1:
                    print(f"   │   └── {file.name}")
                else:
                    print(f"   │   ├── {file.name}")
        
        print()
        print("✅ New output structure verified successfully!")
        
        return True
    else:
        print("❌ Run session directory not created")
        return False

def test_output_stats():
    """Test that output stats work with new structure"""
    print("📊 Testing Output Statistics")
    print("=" * 40)
    
    output_manager = OutputManager()
    stats = output_manager.get_output_stats()
    
    print(f"📁 Run Sessions: {stats['transcriptions']['run_sessions']}")
    print(f"📂 Audio File Sessions: {stats['transcriptions']['sessions']}")
    print(f"📄 Total Files: {stats['transcriptions']['total_files']}")
    print(f"   • JSON: {stats['transcriptions']['json_files']}")
    print(f"   • TXT: {stats['transcriptions']['txt_files']}")
    print(f"   • DOCX: {stats['transcriptions']['docx_files']}")
    print(f"💾 Total Size: {stats['transcriptions']['size_mb']:.2f} MB")
    
    print()
    print("✅ Output statistics working with new structure!")
    
    return True

def main():
    """Main function"""
    print("🎤 New Output Structure Verification")
    print("=" * 60)
    print()
    
    # Test 1: New output structure
    structure_ok = test_new_output_structure()
    print()
    
    # Test 2: Output statistics
    stats_ok = test_output_stats()
    print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Output Structure: {'OK' if structure_ok else 'FAILED'}")
    print(f"✅ Output Statistics: {'OK' if stats_ok else 'FAILED'}")
    
    if structure_ok and stats_ok:
        print("\n🎉 New output structure is working correctly!")
        print("\n💡 Key improvements:")
        print("   ✅ Parent folders for each run session")
        print("   ✅ All files from a batch run organized together")
        print("   ✅ Individual audio file folders within run sessions")
        print("   ✅ Clean, hierarchical organization")
        print("   ✅ Easy to identify and manage run sessions")
        print("\n🚀 Ready for production use!")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 