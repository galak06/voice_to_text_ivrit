#!/usr/bin/env python3
"""
Unified Batch Transcription Script
Combines all batch transcription functionality with parameter injection and progress tracking
"""
import subprocess
import os
import time
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm
import sys

class BatchTranscriptionConfig:
    """Configuration class for batch transcription parameters"""
    
    def __init__(self, 
                 model: str = "ivrit-ai/whisper-large-v3-turbo-ct2",
                 engine: str = "faster-whisper",
                 speaker_config: str = "conversation",
                 timeout: int = 3600,
                 delay_between_files: int = 10,
                 input_dir: str = "examples/audio/voice",
                 output_dir: str = "output",
                 docker_image: str = "whisper-runpod-serverless:latest",
                 verbose: bool = False,
                 dry_run: bool = False):
        """
        Initialize batch transcription configuration
        
        Args:
            model: Whisper model to use for transcription
            engine: Transcription engine (faster-whisper, stable-ts, etc.)
            speaker_config: Speaker diarization configuration
            timeout: Timeout in seconds for each file
            delay_between_files: Delay between processing files
            input_dir: Directory containing audio files
            output_dir: Directory for output files
            docker_image: Docker image to use
            verbose: Enable verbose output
            dry_run: Run without actual transcription
        """
        self.model = model
        self.engine = engine
        self.speaker_config = speaker_config
        self.timeout = timeout
        self.delay_between_files = delay_between_files
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.docker_image = docker_image
        self.verbose = verbose
        self.dry_run = dry_run

class BatchTranscriptionProcessor:
    """Main processor for batch transcription operations"""
    
    def __init__(self, config: BatchTranscriptionConfig):
        """
        Initialize the batch transcription processor
        
        Args:
            config: Configuration object containing all parameters
        """
        self.config = config
        self.results: List[Dict] = []
        
    def discover_audio_files(self) -> List[str]:
        """
        Discover audio files in the input directory
        
        Returns:
            List of audio file paths
        """
        audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
        audio_files = []
        
        input_path = Path(self.config.input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {self.config.input_dir}")
        
        for ext in audio_extensions:
            audio_files.extend(input_path.glob(f"*{ext}"))
            audio_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        return sorted([str(f) for f in audio_files])
    
    def run_docker_transcription(self, audio_file: str, pbar: Optional[tqdm] = None) -> Dict:
        """
        Run transcription for a single audio file using Docker
        
        Args:
            audio_file: Path to the audio file
            pbar: Optional progress bar for status updates
            
        Returns:
            Dictionary containing processing results
        """
        file_name = os.path.basename(audio_file)
        start_time = time.time()
        
        # Update progress bar description
        if pbar:
            pbar.set_description(f"Processing {file_name}")
        
        if self.config.verbose:
            print(f"🎤 Processing: {file_name}")
            print(f"🤖 Model: {self.config.model}")
            print(f"⚙️  Engine: {self.config.engine}")
            print(f"👥 Speaker config: {self.config.speaker_config}")
            print("-" * 50)
        
        # Docker command construction
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}/{self.config.input_dir}:/app/voice",
            "-v", f"{os.getcwd()}/{self.config.output_dir}:/app/output",
            self.config.docker_image,
            "python", "-c",
            f"from src.core.speaker_diarization import speaker_diarization; "
            f"import json; "
            f"result = speaker_diarization('/app/voice/{file_name}', "
            f"'{self.config.model}', '{self.config.engine}', '{self.config.speaker_config}'); "
            f"print('✅ Transcription completed successfully!')"
        ]
        
        result_data = {
            "file": file_name,
            "full_path": audio_file,
            "success": False,
            "error": None,
            "processing_time": 0,
            "start_time": start_time,
            "end_time": None
        }
        
        try:
            if self.config.dry_run:
                print(f"🔍 DRY RUN: Would process {file_name}")
                result_data["success"] = True
                result_data["processing_time"] = 0.1
            else:
                # Run the actual transcription
                process_result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=self.config.timeout
                )
                
                result_data["end_time"] = time.time()
                result_data["processing_time"] = result_data["end_time"] - start_time
                
                if process_result.returncode == 0:
                    result_data["success"] = True
                    if pbar:
                        pbar.set_description(f"Completed {file_name}")
                    if self.config.verbose:
                        print(f"✅ Successfully processed: {file_name}")
                        if process_result.stdout:
                            print(f"Output: {process_result.stdout.strip()}")
                else:
                    result_data["error"] = process_result.stderr
                    if pbar:
                        pbar.set_description(f"Failed {file_name}")
                    if self.config.verbose:
                        print(f"❌ Failed to process: {file_name}")
                        if process_result.stderr:
                            print(f"Error: {process_result.stderr}")
                        if process_result.stdout:
                            print(f"Output: {process_result.stdout}")
                            
        except subprocess.TimeoutExpired:
            result_data["error"] = f"Timeout after {self.config.timeout} seconds"
            if pbar:
                pbar.set_description(f"Timeout {file_name}")
            if self.config.verbose:
                print(f"⏰ Timeout processing: {file_name} ({self.config.timeout} seconds)")
                
        except Exception as e:
            result_data["error"] = str(e)
            if pbar:
                pbar.set_description(f"Error {file_name}")
            if self.config.verbose:
                print(f"❌ Error processing {file_name}: {e}")
        
        return result_data
    
    def process_batch(self) -> Dict:
        """
        Process all audio files in batch
        
        Returns:
            Dictionary containing batch processing results
        """
        try:
            audio_files = self.discover_audio_files()
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return {"success": False, "error": str(e)}
        
        if not audio_files:
            print(f"❌ No audio files found in {self.config.input_dir}")
            return {"success": False, "error": "No audio files found"}
        
        print("🎤 Unified Voice-to-Text Batch Transcription")
        print("=" * 60)
        print(f"🤖 Model: {self.config.model}")
        print(f"⚙️  Engine: {self.config.engine}")
        print(f"👥 Speaker config: {self.config.speaker_config}")
        print(f"📁 Input directory: {self.config.input_dir}")
        print(f"📁 Output directory: {self.config.output_dir}")
        print(f"📁 Files to process: {len(audio_files)}")
        print(f"⏱️  Timeout per file: {self.config.timeout} seconds")
        print(f"⏳ Delay between files: {self.config.delay_between_files} seconds")
        if self.config.dry_run:
            print("🔍 DRY RUN MODE - No actual transcription will be performed")
        print("=" * 60)
        
        successful = 0
        failed = 0
        total_processing_time = 0
        
        # Process files with progress bar
        with tqdm(total=len(audio_files), desc="Overall Progress", unit="file") as pbar:
            for i, audio_file in enumerate(audio_files, 1):
                if self.config.verbose:
                    print(f"\n📝 Processing {i}/{len(audio_files)}: {os.path.basename(audio_file)}")
                
                # Process the file
                result = self.run_docker_transcription(audio_file, pbar)
                self.results.append(result)
                
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
                
                total_processing_time += result["processing_time"]
                
                # Update progress bar
                pbar.update(1)
                
                # Delay between files (except for the last one)
                if i < len(audio_files) and not self.config.dry_run:
                    if self.config.verbose:
                        print(f"⏳ Waiting {self.config.delay_between_files} seconds before next file...")
                    time.sleep(self.config.delay_between_files)
        
        # Generate summary
        summary = {
            "success": True,
            "total_files": len(audio_files),
            "successful": successful,
            "failed": failed,
            "total_processing_time": total_processing_time,
            "average_processing_time": total_processing_time / len(audio_files) if audio_files else 0,
            "results": self.results
        }
        
        self._print_summary(summary)
        return summary
    
    def _print_summary(self, summary: Dict):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("📊 Batch Processing Summary")
        print("=" * 60)
        print(f"✅ Successful: {summary['successful']}/{summary['total_files']}")
        print(f"❌ Failed: {summary['failed']}/{summary['total_files']}")
        print(f"⏱️  Total processing time: {summary['total_processing_time']:.2f} seconds")
        print(f"⏱️  Average processing time: {summary['average_processing_time']:.2f} seconds")
        
        if summary['successful'] == summary['total_files']:
            print("🎉 All files processed successfully!")
        elif summary['successful'] > 0:
            print("⚠️  Some files failed to process")
            print("💡 Check the output directory for results")
        else:
            print("❌ All files failed to process")
        
        print(f"\n📁 Check results in: {self.config.output_dir}/transcriptions/")
        
        # Print failed files if any
        if summary['failed'] > 0:
            print("\n❌ Failed files:")
            for result in summary['results']:
                if not result['success']:
                    print(f"   - {result['file']}: {result['error']}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Unified Batch Transcription Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  python batch_transcribe_unified.py
  
  # Custom model and engine
  python batch_transcribe_unified.py --model "openai/whisper-large-v3" --engine "stable-ts"
  
  # Custom input/output directories
  python batch_transcribe_unified.py --input-dir "my_audio" --output-dir "my_output"
  
  # Dry run to test configuration
  python batch_transcribe_unified.py --dry-run --verbose
  
  # Load configuration from JSON file
  python batch_transcribe_unified.py --config config.json
        """
    )
    
    # Basic parameters
    parser.add_argument("--model", default="ivrit-ai/whisper-large-v3-turbo-ct2",
                       help="Whisper model to use (default: ivrit-ai/whisper-large-v3-turbo-ct2)")
    parser.add_argument("--engine", default="faster-whisper",
                       help="Transcription engine (default: faster-whisper)")
    parser.add_argument("--speaker-config", default="conversation",
                       help="Speaker diarization configuration (default: conversation)")
    
    # Timing parameters
    parser.add_argument("--timeout", type=int, default=3600,
                       help="Timeout in seconds for each file (default: 3600)")
    parser.add_argument("--delay", type=int, default=10,
                       help="Delay between processing files in seconds (default: 10)")
    
    # Directory parameters
    parser.add_argument("--input-dir", default="examples/audio/voice",
                       help="Directory containing audio files (default: examples/audio/voice)")
    parser.add_argument("--output-dir", default="output",
                       help="Directory for output files (default: output)")
    
    # Docker parameters
    parser.add_argument("--docker-image", default="whisper-runpod-serverless:latest",
                       help="Docker image to use (default: whisper-runpod-serverless:latest)")
    
    # Control parameters
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--dry-run", action="store_true",
                       help="Run without actual transcription (test mode)")
    parser.add_argument("--config", type=str,
                       help="Load configuration from JSON file")
    
    return parser.parse_args()

def load_config_from_file(config_path: str) -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config file {config_path}: {e}")
        sys.exit(1)

def main():
    """Main function"""
    args = parse_arguments()
    
    # Load configuration from file if specified
    if args.config:
        config_data = load_config_from_file(args.config)
        # Override with command line arguments
        for key, value in vars(args).items():
            if value is not None and key != 'config':
                config_data[key] = value
    else:
        config_data = vars(args)
    
    # Map command line argument names to config parameter names
    config_mapping = {
        'delay': 'delay_between_files',
        'input_dir': 'input_dir',
        'output_dir': 'output_dir',
        'docker_image': 'docker_image',
        'speaker_config': 'speaker_config'
    }
    
    # Create properly mapped config data
    mapped_config = {}
    for key, value in config_data.items():
        if key == 'config':  # Skip the config file argument
            continue
        if key in config_mapping:
            mapped_config[config_mapping[key]] = value
        else:
            mapped_config[key] = value
    
    # Create configuration object
    config = BatchTranscriptionConfig(**mapped_config)
    
    # Create processor and run batch transcription
    processor = BatchTranscriptionProcessor(config)
    result = processor.process_batch()
    
    # Exit with appropriate code
    if not result["success"]:
        sys.exit(1)
    elif result["failed"] > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 