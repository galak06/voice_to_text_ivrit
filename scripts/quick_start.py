#!/usr/bin/env python3
"""
Quick start script for ivrit-ai voice transcription service
Provides an interactive way to get started quickly
"""

import sys
import os
from pathlib import Path

def print_banner():
    """Print the service banner"""
    print("🎤 ivrit-ai Voice Transcription Service")
    print("=" * 50)
    print("Quick Start Guide")
    print("=" * 50)

def check_audio_files():
    """Check for available audio files in the voice directory"""
    voice_dir = Path("examples/audio/voice")
    if voice_dir.exists():
        audio_files = list(voice_dir.glob("*.wav")) + list(voice_dir.glob("*.mp3")) + list(voice_dir.glob("*.m4a"))
        if audio_files:
            print("📁 Found audio files:")
            for i, file in enumerate(audio_files, 1):
                size = file.stat().st_size
                print(f"  {i}. {file.name} ({size:,} bytes)")
            return audio_files
        else:
            print("📁 No audio files found in voice/ directory")
            return []
    else:
        print("📁 voice/ directory not found")
        return []

def get_user_choice():
    """Get user choice for transcription mode"""
    print("\n🎯 Choose transcription mode:")
    print("1. Local transcription (runs on your machine)")
    print("2. RunPod transcription (requires setup)")
    print("3. Test setup")
    print("4. Show configuration")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            else:
                print("❌ Please enter a number between 1 and 5")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

def get_audio_file_choice(audio_files):
    """Get user choice for audio file"""
    if not audio_files:
        print("❌ No audio files available")
        return None
    
    print(f"\n📁 Choose audio file (1-{len(audio_files)}):")
    for i, file in enumerate(audio_files, 1):
        size = file.stat().st_size
        print(f"  {i}. {file.name} ({size:,} bytes)")
    
    while True:
        try:
            choice = input(f"\nEnter your choice (1-{len(audio_files)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(audio_files):
                return str(audio_files[choice_num - 1])
            else:
                print(f"❌ Please enter a number between 1 and {len(audio_files)}")
        except (ValueError, KeyboardInterrupt):
            if KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
            print("❌ Please enter a valid number")

def run_local_transcription(audio_file):
    """Run local transcription"""
    print(f"\n🎤 Running local transcription on {audio_file}...")
    os.system(f"python main.py --local {audio_file}")

def run_runpod_transcription(audio_file):
    """Run RunPod transcription"""
    print(f"\n☁️  Running RunPod transcription on {audio_file}...")
    os.system(f"python main.py --runpod {audio_file}")

def run_test():
    """Run setup test"""
    print("\n🧪 Running setup tests...")
    os.system("python main.py --test")

def show_config():
    """Show configuration"""
    print("\n⚙️  Showing configuration...")
    os.system("python main.py --config")

def main():
    """Main interactive function"""
    print_banner()
    
    # Check for audio files
    audio_files = check_audio_files()
    
    while True:
        choice = get_user_choice()
        
        if choice == '1':  # Local transcription
            if not audio_files:
                print("❌ No audio files available for transcription")
                print("💡 Please add audio files to the examples/audio/voice/ directory")
                continue
            
            audio_file = get_audio_file_choice(audio_files)
            if audio_file:
                run_local_transcription(audio_file)
        
        elif choice == '2':  # RunPod transcription
            if not audio_files:
                print("❌ No audio files available for transcription")
                print("💡 Please add audio files to the examples/audio/voice/ directory")
                continue
            
            audio_file = get_audio_file_choice(audio_files)
            if audio_file:
                run_runpod_transcription(audio_file)
        
        elif choice == '3':  # Test setup
            run_test()
        
        elif choice == '4':  # Show config
            show_config()
        
        elif choice == '5':  # Exit
            print("👋 Goodbye!")
            break
        
        # Ask if user wants to continue
        try:
            continue_choice = input("\n🤔 Would you like to try another option? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("👋 Goodbye!")
                break
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main() 