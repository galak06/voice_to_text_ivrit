#!/usr/bin/env python3
"""
Mock batch processing test to verify the complete flow without actual transcription
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.application import TranscriptionApplication
from src.utils.config_manager import ConfigManager
from src.output_data import OutputManager

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
    
    # Use current application architecture
    config_manager = ConfigManager()
    app = TranscriptionApplication(config_manager)
    
    voice_files = app.input_processor.discover_files(voice_dir)
    
    if not voice_files:
        print(f"❌ No audio files found in {voice_dir}")
        return False
    
    print(f"🎤 Processing {len(voice_files)} voice files (MOCK MODE)...")
    print(f"📁 Directory: {voice_dir}")
    print(f"🤖 Model: mock-model")
    print(f"⚙️  Engine: mock-engine")
    print(f"🌐 Mode: mock-local")
    print("=" * 60)
    
    from src.output_data.managers.output_manager import OutputManager
    from src.output_data.utils.data_utils import DataUtils
    
    data_utils = DataUtils()
    output_manager = OutputManager(data_utils=data_utils)
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
                # Save transcription in all formats
                saved_files = output_manager.save_transcription(
                    transcription_data=mock_data,
                    audio_file=audio_file,
                    model="mock-model",
                    engine="mock-engine"
                )
                
                print(f"✅ Mock transcription saved for {Path(audio_file).name}")
                for format_type, file_path in saved_files.items():
                    print(f"   📄 {format_type.upper()}: {Path(file_path).name}")
            else:
                print(f"✅ Mock transcription created for {Path(audio_file).name} (not saved)")
            
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            failed_files.append(audio_file)
            print(f"❌ Error processing {Path(audio_file).name}: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Mock Batch Processing Summary")
    print("=" * 60)
    print(f"✅ Successfully processed: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📁 Total files: {len(voice_files)}")
    
    if failed_files:
        print(f"\n❌ Failed files:")
        for failed_file in failed_files:
            print(f"   - {Path(failed_file).name}")
    
    if success_count > 0:
        print(f"\n🎉 Mock batch processing completed successfully!")
        print(f"💾 Output files saved to: {output_manager.output_base_path}")
        return True
    else:
        print(f"\n❌ Mock batch processing failed!")
        return False

 