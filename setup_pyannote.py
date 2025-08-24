#!/usr/bin/env python3
"""
Setup script for pyannote.audio - helps with model access
"""

import os
import sys

def check_model_access():
    """Check if we can access the required models"""
    print("🔍 Checking pyannote.audio model access...")
    print("=" * 60)
    
    # Check if HF_TOKEN is set
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        print("❌ HF_TOKEN environment variable not set!")
        print("Please set it with: export HF_TOKEN='your_token_here'")
        return False
    
    print(f"✅ HF_TOKEN found: {hf_token[:10]}...")
    
    # Test the full pipeline directly (this will download all required models)
    try:
        print("\n🎯 Testing full pyannote.audio pipeline...")
        from pyannote.audio import Pipeline
        
        print("📥 Downloading pyannote.audio models (this may take a few minutes)...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization@2.1",
            use_auth_token=hf_token
        )
        print("✅ Successfully created pyannote.audio pipeline!")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if "gated" in error_msg or "accept" in error_msg:
            print("❌ Model access denied - need to accept terms")
            print("\n📋 To fix this:")
            print("1. Go to: https://hf.co/pyannote/speaker-diarization")
            print("2. Click 'Accept and continue'")
            print("3. Run this script again")
            return False
        elif "not found" in error_msg or "unrecognized" in error_msg:
            print("❌ Model not found or access issue")
            print("\n📋 Please check:")
            print("1. You have accepted the model terms on HuggingFace")
            print("2. Your HF_TOKEN is valid and has access")
            print("3. The model name is correct")
            return False
        else:
            print(f"❌ Pipeline creation failed: {e}")
            return False

def main():
    """Main setup function"""
    print("🚀 pyannote.audio Setup Assistant")
    print("=" * 60)
    
    success = check_model_access()
    
    if success:
        print("\n🎉 Setup complete! pyannote.audio is ready to use.")
        print("\n📝 Next steps:")
        print("1. The transcription system will now use pyannote.audio for speaker diarization")
        print("2. Each audio chunk will be processed with multi-speaker detection")
        print("3. Results will show separate speaker segments with timing")
        print("\n🧪 You can now run the transcription with speaker diarization!")
    else:
        print("\n⚠️ Setup incomplete. Please follow the instructions above.")
        print("\n💡 After accepting the model terms, run:")
        print("   python setup_pyannote.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
