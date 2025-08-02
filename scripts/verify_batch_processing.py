#!/usr/bin/env python3
"""
Comprehensive verification script for batch processing functionality
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_voice_files():
    """Verify that voice files exist and are discoverable"""
    print("🔍 Verifying Voice Files")
    print("=" * 50)
    
    voice_dir = Path("examples/audio/voice")
    
    if not voice_dir.exists():
        print(f"❌ Voice directory not found: {voice_dir}")
        return False
    
    # Supported audio formats
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
    
    voice_files = []
    for ext in audio_extensions:
        voice_files.extend(voice_dir.glob(f"*{ext}"))
        voice_files.extend(voice_dir.glob(f"*{ext.upper()}"))
    
    voice_files = [str(f) for f in voice_files]
    voice_files.sort()
    
    if not voice_files:
        print(f"❌ No audio files found in {voice_dir}")
        return False
    
    print(f"✅ Found {len(voice_files)} voice files:")
    for i, file_path in enumerate(voice_files, 1):
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size
        print(f"   {i}. {file_name} ({file_size:,} bytes)")
    
    print()
    return True

def verify_batch_processing_logic():
    """Verify batch processing logic without actual transcription"""
    print("🧪 Verifying Batch Processing Logic")
    print("=" * 50)
    
    try:
        from main import get_voice_files, run_batch_transcription
        
        voice_files = get_voice_files("examples/audio/voice")
        
        if not voice_files:
            print("❌ No voice files found by batch processing logic")
            return False
        
        print(f"✅ Batch processing logic found {len(voice_files)} files")
        print("✅ Batch processing functions are importable")
        print("✅ Voice file discovery works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in batch processing logic: {e}")
        return False

def verify_output_structure():
    """Verify output directory structure"""
    print("📁 Verifying Output Structure")
    print("=" * 50)
    
    try:
        from src.utils.output_manager import OutputManager
        
        output_manager = OutputManager()
        
        # Check required directories
        required_dirs = [
            output_manager.base_output_dir,
            output_manager.transcriptions_dir,
            output_manager.logs_dir,
            output_manager.temp_dir
        ]
        
        for dir_path in required_dirs:
            if dir_path.exists():
                print(f"✅ Directory exists: {dir_path}")
            else:
                print(f"⚠️  Directory missing: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying output structure: {e}")
        return False

def verify_configuration():
    """Verify configuration system"""
    print("⚙️  Verifying Configuration")
    print("=" * 50)
    
    try:
        from src.utils.config_manager import config_manager, config
        
        # Test configuration loading
        if config_manager.validate():
            print("✅ Configuration validation passed")
        else:
            print("⚠️  Configuration validation failed (expected for missing API keys)")
        
        print(f"✅ Environment: {config.environment.value}")
        print(f"✅ Default model: {config.transcription.default_model}")
        print(f"✅ Default engine: {config.transcription.default_engine}")
        print(f"✅ Output directory: {config.output.output_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying configuration: {e}")
        return False

def verify_imports():
    """Verify that all required modules can be imported"""
    print("📦 Verifying Module Imports")
    print("=" * 50)
    
    modules_to_test = [
        ("main", "Main entry point"),
        ("src.utils.config_manager", "Configuration manager"),
        ("src.utils.output_manager", "Output manager"),
        ("src.core.speaker_transcription_service", "Speaker transcription service"),
        ("src.core.speaker_config_factory", "Speaker config factory"),
        ("src.clients.send_audio", "RunPod client"),
        ("src.core.transcription_service", "Transcription service")
    ]
    
    all_imports_ok = True
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {description}: {module_name}")
        except ImportError as e:
            print(f"⚠️  {description}: {module_name} - {e}")
            all_imports_ok = False
        except Exception as e:
            print(f"❌ {description}: {module_name} - {e}")
            all_imports_ok = False
    
    print()
    return all_imports_ok

def verify_ml_dependencies():
    """Verify ML library availability"""
    print("🤖 Verifying ML Dependencies")
    print("=" * 50)
    
    ml_libraries = [
        ("faster_whisper", "Faster Whisper"),
        ("stable_whisper", "Stable Whisper"),
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio")
    ]
    
    available_libs = []
    missing_libs = []
    
    for lib_name, display_name in ml_libraries:
        try:
            __import__(lib_name)
            available_libs.append(display_name)
            print(f"✅ {display_name}: Available")
        except ImportError:
            missing_libs.append(display_name)
            print(f"❌ {display_name}: Not available")
    
    print()
    
    if available_libs:
        print(f"✅ Available ML libraries: {', '.join(available_libs)}")
    
    if missing_libs:
        print(f"⚠️  Missing ML libraries: {', '.join(missing_libs)}")
        print("💡 Install with: pip install faster-whisper stable-whisper torch torchaudio")
    
    return len(available_libs) > 0

def run_mock_batch_test():
    """Run mock batch processing test"""
    print("🎭 Running Mock Batch Processing Test")
    print("=" * 50)
    
    try:
        from scripts.test_batch_mock import mock_batch_processing
        
        success = mock_batch_processing(save_output=True)
        
        if success:
            print("✅ Mock batch processing test passed")
            return True
        else:
            print("❌ Mock batch processing test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running mock batch test: {e}")
        return False

def generate_summary_report(results):
    """Generate a summary report"""
    print("\n" + "=" * 60)
    print("📊 BATCH PROCESSING VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {failed_tests}/{total_tests}")
    
    print("\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print("\n🎯 Recommendations:")
    
    if results["voice_files"] and results["batch_logic"] and results["output_structure"]:
        print("   ✅ Core batch processing infrastructure is ready")
        
        if results["ml_dependencies"]:
            print("   ✅ ML libraries are available - ready for real transcription")
            print("   🚀 You can now run: python main.py --batch-local")
        else:
            print("   ⚠️  ML libraries are missing - install required packages")
            print("   💡 Run: pip install faster-whisper stable-whisper torch torchaudio")
        
        if results["mock_test"]:
            print("   ✅ Mock processing works - output structure is correct")
    else:
        print("   ❌ Core infrastructure issues detected - check failed tests above")
    
    print("\n📁 Expected Output Structure:")
    print("   output/transcriptions/")
    print("   ├── YYYYMMDD_HHMMSS_audiofilename1/")
    print("   │   ├── transcription_model_engine.json")
    print("   │   ├── transcription_model_engine.txt")
    print("   │   └── transcription_model_engine.docx")
    print("   └── YYYYMMDD_HHMMSS_audiofilename2/")
    print("       ├── transcription_model_engine.json")
    print("       ├── transcription_model_engine.txt")
    print("       └── transcription_model_engine.docx")
    
    return passed_tests == total_tests

def main():
    """Main verification function"""
    print("🎤 Batch Processing Verification Suite")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all verification tests
    results = {
        "voice_files": verify_voice_files(),
        "batch_logic": verify_batch_processing_logic(),
        "output_structure": verify_output_structure(),
        "configuration": verify_configuration(),
        "imports": verify_imports(),
        "ml_dependencies": verify_ml_dependencies(),
        "mock_test": run_mock_batch_test()
    }
    
    # Generate summary report
    all_passed = generate_summary_report(results)
    
    if all_passed:
        print("\n🎉 All verifications passed! Batch processing is fully ready.")
        return 0
    else:
        print("\n⚠️  Some verifications failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 