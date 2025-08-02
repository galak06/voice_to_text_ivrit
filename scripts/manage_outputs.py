#!/usr/bin/env python3
"""
Output management script
Manages transcription outputs, logs, and temporary files
"""

import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.output_manager import OutputManager

def show_output_stats():
    """Show output statistics"""
    output_manager = OutputManager()
    stats = output_manager.get_output_stats()
    
    print("📊 Output Statistics")
    print("=" * 50)
    
    print(f"📁 Transcription Sessions: {stats['transcriptions']['sessions']}")
    print(f"📄 Transcription Files: {stats['transcriptions']['total_files']} total")
    print(f"   • JSON: {stats['transcriptions']['json_files']} files")
    print(f"   • TXT: {stats['transcriptions']['txt_files']} files")
    print(f"   • DOCX: {stats['transcriptions']['docx_files']} files")
    print(f"📝 Total Size: {stats['transcriptions']['size_mb']:.2f} MB")
    
    print(f"📋 Logs:")
    print(f"   Count: {stats['logs']['count']}")
    print(f"   Size: {stats['logs']['size_mb']:.2f} MB")
    
    print(f"🗑️  Temp Files:")
    print(f"   Count: {stats['temp_files']['count']}")
    print(f"   Size: {stats['temp_files']['size_mb']:.2f} MB")
    
    total_size = (stats['transcriptions']['size_mb'] + 
                  stats['logs']['size_mb'] + 
                  stats['temp_files']['size_mb'])
    print(f"\n💾 Total Size: {total_size:.2f} MB")

def list_transcriptions():
    """List all transcription files"""
    output_manager = OutputManager()
    transcriptions_dir = output_manager.transcriptions_dir
    
    print("📝 Transcription Sessions")
    print("=" * 50)
    
    # Get all run session folders
    run_sessions = [d for d in transcriptions_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    
    if not run_sessions:
        print("No transcription sessions found.")
        return
    
    # Sort by modification time (newest first)
    run_sessions.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    
    for i, run_session_dir in enumerate(run_sessions, 1):
        run_session_name = run_session_dir.name
        modified = run_session_dir.stat().st_mtime
        from datetime import datetime
        modified_str = datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get subfolders within this run session
        subfolders = [d for d in run_session_dir.iterdir() if d.is_dir()]
        
        print(f"{i:2d}. 📁 {run_session_name}")
        print(f"    📅 Created: {modified_str}")
        print(f"    📂 Audio Files: {len(subfolders)}")
        
        # Show subfolders (individual audio files)
        for j, subfolder in enumerate(subfolders, 1):
            audio_name = subfolder.name
            json_files = list(subfolder.glob("*.json"))
            txt_files = list(subfolder.glob("*.txt"))
            docx_files = list(subfolder.glob("*.docx"))
            
            print(f"       {j}. 📁 {audio_name}")
            print(f"          📄 Files: {len(json_files)} JSON, {len(txt_files)} TXT, {len(docx_files)} DOCX")
            
            # Show individual files
            all_files = json_files + txt_files + docx_files
            for file in all_files:
                size = file.stat().st_size
                file_type = file.suffix.upper()
                if file_type == '.JSON':
                    file_type = 'JSON Data'
                elif file_type == '.TXT':
                    file_type = 'Text File'
                elif file_type == '.DOCX':
                    file_type = 'Word Document'
                else:
                    file_type = 'Unknown'
                
                print(f"             • {file.name} ({file_type}, {size:,} bytes)")
        
        print()

def cleanup_temp_files(hours: int = 24):
    """Clean up temporary files"""
    output_manager = OutputManager()
    
    print(f"🧹 Cleaning up temporary files older than {hours} hours...")
    output_manager.cleanup_temp_files(hours)
    
    # Show updated stats
    stats = output_manager.get_output_stats()
    print(f"✅ Remaining temp files: {stats['temp_files']['count']}")

def show_recent_logs(lines: int = 20):
    """Show recent log entries"""
    output_manager = OutputManager()
    logs_dir = output_manager.logs_dir
    
    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        print("No log files found.")
        return
    
    # Get the most recent log file
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    
    print(f"📋 Recent logs from {latest_log.name}")
    print("=" * 50)
    
    try:
        with open(latest_log, 'r') as f:
            log_lines = f.readlines()
            # Show last N lines
            recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
            for line in recent_lines:
                print(line.rstrip())
    except Exception as e:
        print(f"Error reading log file: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Manage transcription outputs, logs, and temporary files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_outputs.py --stats                    # Show statistics
  python scripts/manage_outputs.py --list                     # List transcriptions
  python scripts/manage_outputs.py --cleanup                  # Clean temp files
  python scripts/manage_outputs.py --cleanup --hours 48       # Clean files older than 48h
  python scripts/manage_outputs.py --logs                     # Show recent logs
  python scripts/manage_outputs.py --logs --lines 50          # Show last 50 log lines
        """
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show output statistics'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all transcription files'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up temporary files'
    )
    
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Age threshold for cleanup (default: 24 hours)'
    )
    
    parser.add_argument(
        '--logs',
        action='store_true',
        help='Show recent log entries'
    )
    
    parser.add_argument(
        '--lines',
        type=int,
        default=20,
        help='Number of log lines to show (default: 20)'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.stats, args.list, args.cleanup, args.logs]):
        parser.print_help()
        return
    
    print("🎤 ivrit-ai Output Manager")
    print("=" * 50)
    
    if args.stats:
        show_output_stats()
        print()
    
    if args.list:
        list_transcriptions()
        print()
    
    if args.cleanup:
        cleanup_temp_files(args.hours)
        print()
    
    if args.logs:
        show_recent_logs(args.lines)
        print()

if __name__ == "__main__":
    main() 