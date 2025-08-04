#!/usr/bin/env python3
"""
Test script to verify the new output structure with parent folders for each run
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.output_data import OutputManager

def test_new_output_structure():
    """Test the new output structure with parent folders"""
    print("🧪 Testing New Output Structure")
    print("=" * 60)
    
    # Create output manager
    output_manager = OutputManager()
    
    print(f"📁 Output Base Path: {output_manager.output_base_path}")
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
        
        # Create mock transcription data in the new format
        mock_data = {
            "speakers": {
                "Speaker 1": [
                    {
                        "start": 0.0,
                        "end": 5.0,
                        "text": f"Test transcription for {audio_file}",
                        "words": []
                    }
                ]
            },
            "full_text": f"Test transcription for {audio_file}",
            "model_name": "test-model",
            "audio_file": audio_file,
            "speaker_count": 1,
            "transcription_time": 2.5,
            "success": True
        }
        
        # Save all formats using the new interface
        saved_files = output_manager.save_transcription(
            transcription_data=mock_data,
            audio_file=audio_file,
            model="test-model",
            engine="test-engine"
        )
        
        print(f"      ✅ Saved: {list(saved_files.keys())}")
        for file_type, file_path in saved_files.items():
            print(f"         • {file_type.upper()}: {file_path}")
    
    print()
    
    # Verify the structure
    output_base_path = Path(output_manager.output_base_path)
    
    if output_base_path.exists():
        print("✅ Output base directory exists")
        
        # Find all run directories
        run_dirs = [d for d in output_base_path.iterdir() if d.is_dir() and d.name.startswith("run_")]
        print(f"📂 Run directories: {len(run_dirs)}")
        
        # Count files
        total_files = 0
        json_files = 0
        txt_files = 0
        docx_files = 0
        
        for run_dir in run_dirs:
            # Find all subdirectories (audio file folders)
            audio_dirs = [d for d in run_dir.iterdir() if d.is_dir()]
            
            for audio_dir in audio_dirs:
                json_files += len(list(audio_dir.glob("*.json")))
                txt_files += len(list(audio_dir.glob("*.txt")))
                docx_files += len(list(audio_dir.glob("*.docx")))
        
        total_files = json_files + txt_files + docx_files
        
        print(f"📄 Total files: {total_files}")
        print(f"   • JSON: {json_files}")
        print(f"   • TXT: {txt_files}")
        print(f"   • DOCX: {docx_files}")
        
        print()
        print("📁 Directory Structure:")
        print(f"   {output_base_path.name}/")
        
        for run_dir in run_dirs:
            print(f"   ├── {run_dir.name}/")
            audio_dirs = [d for d in run_dir.iterdir() if d.is_dir()]
            for i, audio_dir in enumerate(audio_dirs):
                prefix = "   │   └──" if i == len(audio_dirs) - 1 else "   │   ├──"
                print(f"{prefix} {audio_dir.name}/")
                
                # List files in this directory
                files = list(audio_dir.glob("*"))
                for j, file in enumerate(files):
                    file_prefix = "   │       └──" if j == len(files) - 1 else "   │       ├──"
                    print(f"{file_prefix} {file.name}")
        
        print()
        
        # Check if DOCX files were created
        if docx_files > 0:
            print("✅ DOCX files created successfully!")
        else:
            print("❌ No DOCX files found!")
            
    else:
        print("❌ Output base directory not found!")

def test_output_stats():
    """Test output statistics"""
    print("\n📊 Output Statistics")
    print("=" * 60)
    
    output_manager = OutputManager()
    output_base_path = Path(output_manager.output_base_path)
    
    if output_base_path.exists():
        # Count all files by type
        all_json = list(output_base_path.rglob("*.json"))
        all_txt = list(output_base_path.rglob("*.txt"))
        all_docx = list(output_base_path.rglob("*.docx"))
        
        print(f"📄 Total files found:")
        print(f"   • JSON: {len(all_json)}")
        print(f"   • TXT: {len(all_txt)}")
        print(f"   • DOCX: {len(all_docx)}")
        
        if all_docx:
            print(f"\n📋 DOCX files:")
            for docx_file in all_docx:
                print(f"   • {docx_file}")
        else:
            print("\n❌ No DOCX files found!")
    else:
        print("❌ Output directory not found!")

def main():
    """Main test function"""
    test_new_output_structure()
    test_output_stats()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main() 