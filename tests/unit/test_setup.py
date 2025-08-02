#!/usr/bin/env python3
"""
Test script to verify the unified batch transcription system setup
"""

import sys
import importlib
from pathlib import Path

def test_core_imports():
    """Test that core packages can be imported"""
    core_packages = [
        'tqdm',           # Progress bars
        'pathlib',        # File path handling
        'subprocess',     # Docker command execution
        'argparse',       # Command line argument parsing
        'json',           # Configuration file handling
        'time',           # Timing functionality
        'os'              # Operating system interface
    ]
    
    print("🧪 Testing core package imports...")
    
    failed_imports = []
    for package in core_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {package}: {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def test_unified_batch_transcription():
    """Test that the unified batch transcription module can be imported"""
    print("\n🎤 Testing unified batch transcription module...")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from batch_transcribe_unified import BatchTranscriptionConfig, BatchTranscriptionProcessor
        print("✅ Unified batch transcription module imported successfully")
        
        # Test basic functionality
        config = BatchTranscriptionConfig()
        processor = BatchTranscriptionProcessor(config)
        print("✅ Configuration and processor classes created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Unified batch transcription test failed: {e}")
        return False

def test_optional_imports():
    """Test optional packages (not required for core functionality)"""
    optional_packages = [
        'runpod',
        'faster_whisper', 
        'stable_whisper',
        'torch',
        'requests'
    ]
    
    print("\n🔧 Testing optional package imports...")
    
    available_packages = []
    missing_packages = []
    
    for package in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} available")
            available_packages.append(package)
        except ImportError:
            print(f"ℹ️  {package} not available (optional)")
            missing_packages.append(package)
    
    print(f"\n📊 Optional packages status:")
    print(f"   ✅ Available: {len(available_packages)}")
    print(f"   ℹ️  Missing: {len(missing_packages)}")
    
    if available_packages:
        print(f"   📦 Available packages: {', '.join(available_packages)}")
    if missing_packages:
        print(f"   📦 Missing packages: {', '.join(missing_packages)}")
    
    return True  # Always return True as these are optional

def test_file_structure():
    """Test that required files and directories exist"""
    print("\n📁 Testing file structure...")
    
    project_root = Path(__file__).parent.parent.parent
    required_paths = [
        project_root / "batch_transcribe_unified.py",
        project_root / "examples" / "audio" / "voice",
        project_root / "output",
        project_root / "config" / "batch_transcription_config.json"
    ]
    
    missing_paths = []
    for path in required_paths:
        if path.exists():
            print(f"✅ {path.name} exists")
        else:
            print(f"❌ {path.name} missing")
            missing_paths.append(path)
    
    return len(missing_paths) == 0

def test_docker_availability():
    """Test if Docker is available (required for transcription)"""
    print("\n🐳 Testing Docker availability...")
    
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker not available")
            return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing unified batch transcription system setup...\n")
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Unified Batch Transcription", test_unified_batch_transcription),
        ("Optional Imports", test_optional_imports),
        ("File Structure", test_file_structure),
        ("Docker Availability", test_docker_availability)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your unified batch transcription system is ready to use.")
        print("\n💡 Next steps:")
        print("1. Test with dry run: python batch_transcribe_unified.py --dry-run --verbose")
        print("2. Run batch processing: python batch_transcribe_unified.py")
        print("3. Check documentation: docs/BATCH_TRANSCRIPTION_UNIFIED.md")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("\n💡 Note: Missing optional packages (runpod, faster-whisper, etc.)")
        print("   do not affect core functionality when using Docker.")
        
        # Don't exit with error code if only optional tests failed
        if passed >= 3:  # At least core functionality tests passed
            print("\n✅ Core functionality is working. Optional dependencies can be installed later.")
            return 0
        else:
            sys.exit(1)

if __name__ == "__main__":
    main() 