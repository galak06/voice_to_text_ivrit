#!/usr/bin/env python3
"""
Test script to verify the ivrit-ai runpod serverless setup
"""

import sys
import importlib

def test_imports():
    """Test that all required packages can be imported"""
    required_packages = [
        'runpod',
        'faster_whisper', 
        'stable_whisper',
        'torch',
        'requests'
    ]
    
    print("🧪 Testing package imports...")
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {package}: {e}")
            return False
    
    return True

def test_torch():
    """Test PyTorch installation and device availability"""
    print("\n🔥 Testing PyTorch...")
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ️  CUDA not available, using CPU")
        
        return True
    except Exception as e:
        print(f"❌ PyTorch test failed: {e}")
        return False

def test_faster_whisper():
    """Test faster-whisper installation"""
    print("\n🎤 Testing faster-whisper...")
    
    try:
        from faster_whisper import WhisperModel
        print("✅ faster-whisper imported successfully")
        
        # Test model loading (this will download models if not cached)
        print("📥 Testing model loading (this may take a while on first run)...")
        model = WhisperModel("ivrit-ai/whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8")
        print("✅ Model loaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ faster-whisper test failed: {e}")
        return False

def test_runpod():
    """Test RunPod client"""
    print("\n☁️  Testing RunPod client...")
    
    try:
        import runpod
        print("✅ RunPod client imported successfully")
        return True
    except Exception as e:
        print(f"❌ RunPod test failed: {e}")
        return False

def test_config():
    """Test configuration utility"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from src.utils.config_manager import config_manager, config
        print("✅ Configuration utility imported successfully")
        
        # Test configuration loading
        config_manager.print_config()
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing ivrit-ai runpod serverless setup...\n")
    
    tests = [
        test_imports,
        test_torch,
        test_faster_whisper,
        test_runpod,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready to use.")
        print("\nNext steps:")
        print("1. Activate the environment: conda activate ivrit-ai-runpod-macos")
        print("2. Test the inference script: python infer.py")
        print("3. Build Docker image: docker build -t whisper-runpod-serverless .")
    else:
        print("⚠️  Some tests failed. Please check your installation.")
        sys.exit(1)

if __name__ == "__main__":
    main() 