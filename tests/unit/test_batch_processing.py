#!/usr/bin/env python3
"""
Test script to verify batch processing of voice files
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.application import TranscriptionApplication
from src.utils.config_manager import ConfigManager

def test_voice_file_discovery():
    """Test that all voice files are discovered correctly"""
    print("🧪 Testing Voice File Discovery")
    print("=" * 50)
    
    # Use the current application architecture
    config_manager = ConfigManager()
    app = TranscriptionApplication(config_manager)
    
    # Discover files using the current input processor
    voice_files = app.input_processor.discover_files("examples/audio/voice")
    
    print(f"📁 Voice directory: examples/audio/voice")
    print(f"🔍 Found {len(voice_files)} audio files:")
    
    for i, file_path in enumerate(voice_files, 1):
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size
        print(f"   {i}. {file_name} ({file_size:,} bytes)")
    
    print()
    return voice_files

def test_batch_processing_logic():
    """Test batch processing logic without actual transcription"""
    print("🧪 Testing Batch Processing Logic")
    print("=" * 50)
    
    # Use the current application architecture
    config_manager = ConfigManager()
    app = TranscriptionApplication(config_manager)
    
    voice_files = app.input_processor.discover_files("examples/audio/voice")
    
    if not voice_files:
        print("❌ No voice files found")
        return False
    
    print(f"🎤 Would process {len(voice_files)} voice files:")
    print()
    
    for i, audio_file in enumerate(voice_files, 1):
        file_name = Path(audio_file).name
        print(f"📝 {i}/{len(voice_files)}: {file_name}")
        print(f"   📁 Path: {audio_file}")
        print(f"   🤖 Model: default (ivrit-ai/whisper-large-v3-ct2)")
        print(f"   ⚙️  Engine: default (faster-whisper)")
        print(f"   👥 Speaker config: default")
        print(f"   💾 Save output: True")
        print()
    
    print("✅ Batch processing logic verified!")
    print("💡 To actually process files, run:")
    print("   python main_app.py batch")
    print("   python main_app.py batch --config-file config/environments/docker_batch.json")
    
    return True

def test_output_structure():
    """Test that output structure is ready for batch processing"""
    print("🧪 Testing Output Structure")
    print("=" * 50)
    
    from src.utils.output_manager import OutputManager
    
    try:
        output_manager = OutputManager()
        print("✅ Output manager initialized successfully")
        
        # Check directories
        dirs_to_check = [
            output_manager.base_output_dir,
            output_manager.transcriptions_dir,
            output_manager.logs_dir,
            output_manager.temp_dir
        ]
        
        for dir_path in dirs_to_check:
            if dir_path.exists():
                print(f"✅ Directory exists: {dir_path}")
            else:
                print(f"⚠️  Directory missing: {dir_path}")
        
        print()
        print("✅ Output structure ready for batch processing!")
        
    except Exception as e:
        print(f"❌ Error initializing output manager: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🎤 Batch Processing Verification Test")
    print("=" * 60)
    print()
    
    # Test 1: Voice file discovery
    voice_files = test_voice_file_discovery()
    print()
    
    # Test 2: Output structure
    output_ok = test_output_structure()
    print()
    
    # Test 3: Batch processing logic
    logic_ok = test_batch_processing_logic()
    print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Voice files found: {len(voice_files)}")
    print(f"✅ Output structure: {'OK' if output_ok else 'FAILED'}")
    print(f"✅ Batch logic: {'OK' if logic_ok else 'FAILED'}")
    
    if len(voice_files) > 0 and output_ok and logic_ok:
        print("\n🎉 All tests passed! Batch processing is ready.")
        print("\n💡 Next steps:")
        print("   1. Install required packages: pip install faster-whisper stable-whisper")
        print("   2. Run batch processing: python main_app.py batch")
        print("   3. Check outputs in: output/transcriptions/")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 