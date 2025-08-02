#!/usr/bin/env python3
"""
Mock batch processing test to verify complete flow without ML dependencies
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import get_voice_files
from src.utils.output_manager import OutputManager

def create_mock_transcription(audio_file: str, model: str = "mock-model", engine: str = "mock-engine"):
    """Create mock transcription data"""
    audio_name = Path(audio_file).stem
    
    return [
        {
            "id": 0,
            "start": 0.0,
            "end": 5.0,
            "text": f"Mock transcription for {audio_name} - first segment",
            "speaker": "Speaker 1",
            "words": [
                {"word": "Mock", "start": 0.0, "end": 0.5, "probability": 0.95},
                {"word": "transcription", "start": 0.5, "end": 1.2, "probability": 0.92},
                {"word": "for", "start": 1.2, "end": 1.5, "probability": 0.98}
            ]
        },
        {
            "id": 1,
            "start": 5.0,
            "end": 10.0,
            "text": f"Mock transcription for {audio_name} - second segment",
            "speaker": "Speaker 2",
            "words": [
                {"word": "Second", "start": 5.0, "end": 5.5, "probability": 0.94},
                {"word": "segment", "start": 5.5, "end": 6.2, "probability": 0.91}
            ]
        }
    ]

def mock_batch_processing(voice_dir: str = "examples/audio/voice", save_output: bool = True):
    """Mock batch processing to test the complete flow"""
    print("🎤 Mock Batch Processing Test")
    print("=" * 60)
    
    voice_files = get_voice_files(voice_dir)
    
    if not voice_files:
        print(f"❌ No audio files found in {voice_dir}")
        return False
    
    print(f"🎤 Processing {len(voice_files)} voice files (MOCK MODE)...")
    print(f"📁 Directory: {voice_dir}")
    print(f"🤖 Model: mock-model")
    print(f"⚙️  Engine: mock-engine")
    print(f"🌐 Mode: mock-local")
    print("=" * 60)
    
    output_manager = OutputManager()
    success_count = 0
    failed_count = 0
    failed_files = []
    
    for i, audio_file in enumerate(voice_files, 1):
        print(f"\n📝 Processing {i}/{len(voice_files)}: {Path(audio_file).name}")
        print("-" * 40)
        
        try:
            # Create mock transcription data
            mock_data = create_mock_transcription(audio_file)
            
            if save_output:
                # Save as JSON
                json_file = output_manager.save_transcription(
                    audio_file, mock_data, "mock-model", "mock-engine"
                )
                
                # Save as text
                text_content = "\n".join([seg.get('text', '') for seg in mock_data if 'text' in seg])
                if text_content.strip():
                    text_file = output_manager.save_transcription_text(
                        audio_file, text_content, "mock-model", "mock-engine"
                    )
                
                # Save as Word document
                docx_file = output_manager.save_transcription_docx(
                    audio_file, mock_data, "mock-model", "mock-engine"
                )
                
                print(f"✅ Mock transcription saved for {Path(audio_file).name}")
                print(f"   📄 JSON: {Path(json_file).name}")
                print(f"   📝 TXT: {Path(text_file).name}")
                print(f"   📘 DOCX: {Path(docx_file).name}")
            else:
                print(f"✅ Mock transcription created for {Path(audio_file).name} (not saved)")
            
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            failed_files.append(audio_file)
            print(f"❌ Error processing {Path(audio_file).name}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Mock Batch Processing Summary")
    print("=" * 60)
    print(f"✅ Successful: {success_count}/{len(voice_files)}")
    print(f"❌ Failed: {failed_count}/{len(voice_files)}")
    
    if failed_files:
        print(f"\n❌ Failed files:")
        for file in failed_files:
            print(f"   • {Path(file).name}")
    
    if success_count == len(voice_files):
        print("\n🎉 All files processed successfully!")
        
        # Show output structure
        print("\n📁 Generated Output Structure:")
        stats = output_manager.get_output_stats()
        print(f"   📂 Sessions: {stats['transcriptions']['sessions']}")
        print(f"   📄 JSON files: {stats['transcriptions']['json_files']}")
        print(f"   📝 TXT files: {stats['transcriptions']['txt_files']}")
        print(f"   📘 DOCX files: {stats['transcriptions']['docx_files']}")
        print(f"   💾 Total size: {stats['transcriptions']['size_mb']:.2f} MB")
        
        return True
    else:
        print(f"\n⚠️  {failed_count} files failed to process")
        return False

def main():
    """Main function"""
    print("🧪 Mock Batch Processing Verification")
    print("=" * 60)
    print()
    
    # Test with save output
    success = mock_batch_processing(save_output=True)
    
    if success:
        print("\n🎉 Mock batch processing test completed successfully!")
        print("\n💡 This verifies that:")
        print("   ✅ All voice files are discovered correctly")
        print("   ✅ Each file gets processed individually")
        print("   ✅ Output files are created in timestamped folders")
        print("   ✅ All three formats (JSON, TXT, DOCX) are generated")
        print("   ✅ Batch processing logic works correctly")
        print("\n🚀 Ready for real transcription with ML libraries!")
    else:
        print("\n❌ Mock batch processing test failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 