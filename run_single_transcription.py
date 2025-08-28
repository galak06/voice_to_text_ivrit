#!/usr/bin/env python3
"""
Single File Transcription Script
Run the transcription model on one voice file and display the output
"""

import sys
import os
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import TranscriptionApplication
from src.utils.config_manager import ConfigManager
from src.utils.ui_manager import ApplicationUI
from src.models.environment import Environment
from src.core.engines.utilities.cleanup_manager import CleanupManager


def run_single_transcription(audio_file_path: str, model: Optional[str] = None, engine: Optional[str] = None, config_file: Optional[str] = None):
    """
    Run transcription on a single audio file
    
    Args:
        audio_file_path: Path to the audio file to transcribe
        model: Optional model to use (e.g., 'ivrit-ai/whisper-large-v3-ct2')
        engine: Optional engine to use (e.g., 'custom-whisper', 'stable-whisper')
        config_file: Optional path to configuration file
    """
    try:
        print(f"🎵 Starting transcription of: {audio_file_path}")
        print(f"📁 File size: {Path(audio_file_path).stat().st_size / (1024*1024):.2f} MB")
        print("-" * 60)
        
        # Initialize configuration
        if config_file:
            print(f"⚙️  Using config: {config_file}")
            # Extract environment from filename (e.g., "production.json" -> "production")
            env_name = Path(config_file).stem
            environment = Environment(env_name) if hasattr(Environment, env_name.upper()) else Environment.PRODUCTION
            config_manager = ConfigManager(str(Path(config_file).parent), environment=environment)
        else:
            print("⚙️  Using default configuration")
            config_manager = ConfigManager()
        
        # Create cleanup manager and inject it
        cleanup_manager = CleanupManager(config_manager)
        
        # Initialize application with injected dependencies
        app = TranscriptionApplication(
            config_manager=config_manager,
            cleanup_manager=cleanup_manager
        )
        
        # Create UI manager
        ui = ApplicationUI()
        
        # Set default values from production config if not specified
        default_model = model or "ivrit-ai/whisper-large-v3-ct2"
        default_engine = engine or "ctranslate2-whisper"
        
        print(f"🚀 Processing with model: {default_model}")
        print(f"🔧 Engine: {default_engine}")
        print("-" * 60)
        
        # Run transcription
        with app:
            result = app.process_single_file(audio_file_path, model=default_model, engine=default_engine)
            
            if result and result.get('success'):
                print("✅ Transcription completed successfully!")
                print("-" * 60)
                print("📝 TRANSCRIPTION RESULT:")
                print("=" * 60)
                
                # Display transcription text from the result structure
                transcription_result = result.get('transcription', {})
                if transcription_result.get('success'):
                    # Try to get text from different possible locations
                    text = None
                    
                    # First try to get from segments
                    segments = transcription_result.get('segments', [])
                    if segments and len(segments) > 0:
                        if isinstance(segments[0], dict):
                            text = segments[0].get('text', segments[0].get('transcription', ''))
                        else:
                            text = str(segments[0])
                    
                    # If no segments, try to get from transcription field directly
                    if not text:
                        text = transcription_result.get('text', transcription_result.get('transcription', ''))
                    
                    # If still no text, try to get from full_text
                    if not text:
                        text = transcription_result.get('full_text', '')
                    
                    if text:
                        print(f"📝 Transcription: {text}")
                    else:
                        print("No transcription text found in result structure")
                        print(f"Available keys: {list(transcription_result.keys())}")
                else:
                    print("Transcription processing failed")
                    if 'error' in transcription_result:
                        print(f"Error: {transcription_result['error']}")
                
                print("=" * 60)
                
                # Show output files
                output_result = result.get('output', {})
                if output_result.get('success'):
                    print("\n📁 Output processing completed successfully")
                    # You can add more output file details here if needed
                
                # Show performance metrics if available
                if 'processing_time' in result:
                    print(f"\n⏱️  Processing time: {result['processing_time']:.2f} seconds")
                
            else:
                print("❌ Transcription failed!")
                if result and 'error' in result:
                    print(f"Error: {result['error']}")
                elif result and 'transcription' in result:
                    trans_error = result['transcription'].get('error', 'Unknown error')
                    print(f"Transcription error: {trans_error}")
        
    except Exception as e:
        print(f"❌ Error during transcription: {str(e)}")
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main function to handle command line arguments"""
    
    config_file = "config/environments/production.json"  # Default to production config
    
    audio_file = "/Users/gilcohen/voic_to_text_docker/examples/audio/audio_chunk_001_0s_30s.wav"
    
    # Run transcription
    success = run_single_transcription(audio_file, config_file=config_file)
    
    if success:
        print("\n🎉 Script completed successfully!")
    else:
        print("\n💥 Script failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
