#!/usr/bin/env python3
"""
Unified main entry point for ivrit-ai voice transcription service
Supports both local and RunPod execution modes
"""

import sys
import argparse
import os
from pathlib import Path
from typing import Optional, Dict, Any, Generator, List
from src.utils.config_manager import config_manager, config

def get_voice_files(voice_dir: str = "examples/audio/voice") -> List[str]:
    """
    Get all supported audio files from the voice directory
    
    Args:
        voice_dir: Path to voice directory
        
    Returns:
        List of audio file paths
    """
    voice_path = Path(voice_dir)
    if not voice_path.exists():
        print(f"❌ Voice directory not found: {voice_dir}")
        return []
    
    # Supported audio formats
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
    
    voice_files = []
    for ext in audio_extensions:
        voice_files.extend(voice_path.glob(f"*{ext}"))
        voice_files.extend(voice_path.glob(f"*{ext.upper()}"))
    
    # Convert to strings and sort
    voice_files = [str(f) for f in voice_files]
    voice_files.sort()
    
    return voice_files

def run_batch_transcription(voice_dir: str = "examples/audio/voice", model: str = None, 
                          engine: str = None, save_output: bool = True, 
                          speaker_config: str = None, mode: str = "local") -> bool:
    """
    Run transcription on all voice files in the directory
    
    Args:
        voice_dir: Path to voice directory
        model: Model to use (optional)
        engine: Engine to use (optional)
        save_output: Whether to save outputs
        speaker_config: Speaker configuration preset
        mode: Transcription mode ('local' or 'runpod')
        
    Returns:
        True if all successful, False if any failed
    """
    voice_files = get_voice_files(voice_dir)
    
    if not voice_files:
        print(f"❌ No audio files found in {voice_dir}")
        return False
    
    # Generate a shared run session ID for this batch
    from datetime import datetime
    run_session_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"🎤 Batch Processing {len(voice_files)} voice files...")
    print(f"📁 Directory: {voice_dir}")
    print(f"🤖 Model: {model or 'default'}")
    print(f"⚙️  Engine: {engine or 'default'}")
    print(f"🌐 Mode: {mode}")
    print(f"🆔 Run Session: {run_session_id}")
    if speaker_config:
        print(f"👥 Speaker config: {speaker_config}")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    failed_files = []
    
    for i, audio_file in enumerate(voice_files, 1):
        print(f"\n📝 Processing {i}/{len(voice_files)}: {Path(audio_file).name}")
        print("-" * 40)
        
        try:
            if mode == "local":
                success = run_local_transcription(audio_file, model, engine, save_output, speaker_config, run_session_id)
            else:  # runpod
                success = run_runpod_transcription(audio_file, model, engine, save_output, run_session_id)
            
            if success:
                success_count += 1
                print(f"✅ Success: {Path(audio_file).name}")
            else:
                failed_count += 1
                failed_files.append(audio_file)
                print(f"❌ Failed: {Path(audio_file).name}")
                
        except Exception as e:
            failed_count += 1
            failed_files.append(audio_file)
            print(f"❌ Error processing {Path(audio_file).name}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Batch Processing Summary")
    print("=" * 60)
    print(f"✅ Successful: {success_count}/{len(voice_files)}")
    print(f"❌ Failed: {failed_count}/{len(voice_files)}")
    
    if failed_files:
        print(f"\n❌ Failed files:")
        for file in failed_files:
            print(f"   • {Path(file).name}")
    
    if success_count == len(voice_files):
        print(f"\n🎉 All files processed successfully!")
        print(f"📁 Results saved in: output/transcriptions/{run_session_id}/")
        return True
    else:
        print(f"\n⚠️  {failed_count} files failed to process")
        return False

def run_local_transcription(audio_file: str, model: str = None, engine: str = None, save_output: bool = True, speaker_config: str = None, run_session_id: str = None) -> bool:
    """
    Run transcription locally using faster-whisper or stable-whisper
    
    Args:
        audio_file: Path to audio file
        model: Model to use (optional)
        engine: Engine to use (optional)
        save_output: Whether to save outputs
        speaker_config: Speaker configuration preset (default, conversation, interview, custom)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from src.core.speaker_diarization import speaker_diarization
        
        print("🎤 Running local transcription...")
        print(f"📁 Audio file: {audio_file}")
        print(f"🤖 Model: {model or 'default'}")
        print(f"⚙️  Engine: {engine or 'default'}")
        if speaker_config:
            print(f"👥 Speaker config: {speaker_config}")
        
        success = speaker_diarization(audio_file, model, save_output, speaker_config, run_session_id)
        
        if success:
            print("✅ Local transcription completed successfully!")
        else:
            print("❌ Local transcription failed!")
            
        return success
        
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have installed the required packages:")
        print("   pip install faster-whisper stable-whisper")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_runpod_transcription(audio_file: str, model: str = None, engine: str = None, save_output: bool = True, run_session_id: str = None) -> bool:
    """
    Run transcription via RunPod endpoint
    
    Args:
        audio_file: Path to audio file
        model: Model to use (optional)
        engine: Engine to use (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from src.clients.send_audio import send_audio_file
        
        print("☁️  Running RunPod transcription...")
        print(f"📁 Audio file: {audio_file}")
        print(f"🤖 Model: {model or 'default'}")
        print(f"⚙️  Engine: {engine or 'default'}")
        
        success = send_audio_file(audio_file, model, engine)
        
        if success:
            print("✅ RunPod transcription completed successfully!")
        else:
            print("❌ RunPod transcription failed!")
            
        return success
        
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have installed the required packages:")
        print("   pip install runpod")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_serverless_handler() -> None:
    """
    Run as RunPod serverless handler (for Docker container)
    """
    try:
        from infer import transcribe
        import runpod
        
        print("🚀 Starting RunPod serverless handler...")
        runpod.serverless.start({"handler": transcribe, "return_aggregate_stream": True})
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have installed the required packages:")
        print("   pip install runpod")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def print_usage_examples():
    """Print usage examples"""
    print("💡 Usage Examples:")
    print("  python main.py --local voice/audio.wav                    # Local transcription")
    print("  python main.py --local voice/audio.wav --speaker-config conversation  # Conversation mode")
    print("  python main.py --local voice/audio.wav --speaker-config interview     # Interview mode")
    print("  python main.py --runpod voice/audio.wav                   # RunPod transcription")
    print("  python main.py --batch-local                              # Process all voice files locally")
    print("  python main.py --batch-runpod                             # Process all voice files via RunPod")
    print("  python main.py --serverless                               # Run as serverless handler")
    print("  python main.py --test                                     # Test setup")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ivrit-ai Voice Transcription Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --local voice/audio.wav                    # Local transcription
  python main.py --local voice/audio.wav --speaker-config conversation  # Conversation mode
  python main.py --local voice/audio.wav --speaker-config interview     # Interview mode
  python main.py --runpod voice/audio.wav                   # RunPod transcription
  python main.py --batch-local                              # Process all voice files locally
  python main.py --batch-runpod                             # Process all voice files via RunPod
  python main.py --serverless                               # Run as serverless handler
  python main.py --test                                     # Test setup
        """
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument(
        '--local',
        metavar='AUDIO_FILE',
        help='Run local transcription on audio file'
    )
    mode_group.add_argument(
        '--runpod',
        metavar='AUDIO_FILE',
        help='Run transcription via RunPod endpoint'
    )
    mode_group.add_argument(
        '--batch-local',
        action='store_true',
        help='Process all voice files locally'
    )
    mode_group.add_argument(
        '--batch-runpod',
        action='store_true',
        help='Process all voice files via RunPod'
    )
    mode_group.add_argument(
        '--serverless',
        action='store_true',
        help='Run as RunPod serverless handler (for Docker)'
    )
    mode_group.add_argument(
        '--test',
        action='store_true',
        help='Test the setup and configuration'
    )
    
    # Optional arguments
    parser.add_argument(
        '--model',
        help='Model to use for transcription (default: from config)'
    )
    parser.add_argument(
        '--engine',
        choices=['faster-whisper', 'stable-whisper'],
        help='Transcription engine to use (default: from config)'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration'
    )
    
    parser.add_argument(
        '--speaker-presets',
        action='store_true',
        help='Show available speaker configuration presets'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save transcription outputs'
    )
    
    parser.add_argument(
        '--speaker-config',
        choices=['default', 'conversation', 'interview', 'custom'],
        default='default',
        help='Speaker diarization configuration preset (default: default)'
    )
    
    parser.add_argument(
        '--voice-dir',
        default='examples/audio/voice',
        help='Voice directory path (default: examples/audio/voice)'
    )
    
    args = parser.parse_args()
    
    print("🎤 ivrit-ai Voice Transcription Service")
    print("=" * 50)
    
    # Show configuration if requested
    if args.config:
        config_manager.print_config()
        print()
    
    # Show speaker presets if requested
    if args.speaker_presets:
        from src.core.speaker_config_factory import SpeakerConfigFactory
        SpeakerConfigFactory.print_all_presets()
        return
    
    # Handle different modes
    if args.test:
        print("🧪 Running setup tests...")
        try:
            from src.tests.test_setup import main as test_main
            test_main()
        except ImportError:
            print("❌ Test module not found")
            sys.exit(1)
        return
    
    if args.serverless:
        run_serverless_handler()
        return
    
    # Handle batch processing modes
    if args.batch_local:
        success = run_batch_transcription(
            args.voice_dir, args.model, args.engine, 
            not args.no_save, args.speaker_config, "local"
        )
        if not success:
            sys.exit(1)
        return
    
    if args.batch_runpod:
        success = run_batch_transcription(
            args.voice_dir, args.model, args.engine, 
            not args.no_save, args.speaker_config, "runpod"
        )
        if not success:
            sys.exit(1)
        return
    
    # Check if a mode is required
    if not any([args.local, args.runpod, args.batch_local, args.batch_runpod, args.serverless, args.test, args.speaker_presets]):
        parser.print_help()
        return
    
    # For local and runpod modes, we need an audio file
    audio_file = args.local or args.runpod
    
    from src.core.job_validator import JobValidator
    validator = JobValidator()
    if not validator.validate_audio_file(audio_file):
        sys.exit(1)
    
    # Run the appropriate transcription mode
    success = False
    if args.local:
        success = run_local_transcription(audio_file, args.model, args.engine, not args.no_save, args.speaker_config)
    elif args.runpod:
        success = run_runpod_transcription(audio_file, args.model, args.engine, not args.no_save)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 