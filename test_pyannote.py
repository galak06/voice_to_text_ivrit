#!/usr/bin/env python3
"""
Test script to verify pyannote.audio is working correctly
"""

import os
import sys

def test_pyannote_import():
    """Test if pyannote.audio can be imported"""
    try:
        from pyannote.audio import Pipeline
        print("✅ pyannote.audio imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import pyannote.audio: {e}")
        return False

def test_hf_token():
    """Test if HuggingFace token is available"""
    hf_token = os.getenv('HF_TOKEN')
    if hf_token and hf_token != 'YOUR_TOKEN_HERE':
        print(f"✅ HuggingFace token found: {hf_token[:10]}...")
        return True
    else:
        print("❌ HuggingFace token not found or not set properly")
        print("Please set HF_TOKEN environment variable with your HuggingFace token")
        return False

def test_pipeline_creation():
    """Test if pipeline can be created"""
    try:
        from pyannote.audio import Pipeline
        hf_token = os.getenv('HF_TOKEN')
        
        if not hf_token or hf_token == 'YOUR_TOKEN_HERE':
            print("⚠️ Skipping pipeline creation test - no valid token")
            return False
            
        print("🎯 Creating pyannote.audio pipeline...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization@2.1",
            use_auth_token=hf_token
        )
        print("✅ Pipeline created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create pipeline: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing pyannote.audio setup...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_pyannote_import),
        ("Token Test", test_hf_token),
        ("Pipeline Test", test_pipeline_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! pyannote.audio is ready to use.")
    else:
        print("⚠️ Some tests failed. Please check the setup.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
