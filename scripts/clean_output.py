#!/usr/bin/env python3
"""
Output Folder Cleaner
Cleans transcription output folders and temporary files
"""

import os
import shutil
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OutputCleaner:
    """Cleans output folders and temporary files"""
    
    def __init__(self, output_base_dir: str = "output"):
        self.output_base_dir = Path(output_base_dir)
        self.cleaned_files = []
        self.cleaned_dirs = []
        self.total_size_cleaned = 0
        
    def scan_output_structure(self) -> Dict[str, Any]:
        """Scan the output directory structure"""
        logger.info(f"🔍 Scanning output directory: {self.output_base_dir}")
        
        if not self.output_base_dir.exists():
            logger.warning(f"❌ Output directory does not exist: {self.output_base_dir}")
            return {
                'status': 'not_found',
                'message': f"Output directory does not exist: {self.output_base_dir}",
                'structure': {}
            }
        
        structure = {
            'transcriptions': {},
            'temp_chunks': {},
            'logs': {},
            'other': {}
        }
        
        total_files = 0
        total_size = 0
        
        # Scan transcriptions directory
        transcriptions_dir = self.output_base_dir / "transcriptions"
        if transcriptions_dir.exists():
            structure['transcriptions'] = self._scan_directory(transcriptions_dir)
            total_files += structure['transcriptions']['file_count']
            total_size += structure['transcriptions']['total_size']
        
        # Scan temp chunks directory
        temp_chunks_dir = self.output_base_dir / "temp_chunks"
        if temp_chunks_dir.exists():
            structure['temp_chunks'] = self._scan_directory(temp_chunks_dir)
            total_files += structure['temp_chunks']['file_count']
            total_size += structure['temp_chunks']['total_size']
        
        # Scan logs directory
        logs_dir = self.output_base_dir / "logs"
        if logs_dir.exists():
            structure['logs'] = self._scan_directory(logs_dir)
            total_files += structure['logs']['file_count']
            total_size += structure['logs']['total_size']
        
        # Scan other files in output root
        structure['other'] = self._scan_directory(self.output_base_dir, include_subdirs=False)
        total_files += structure['other']['file_count']
        total_size += structure['other']['total_size']
        
        scan_result = {
            'status': 'success',
            'output_dir': str(self.output_base_dir),
            'structure': structure,
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
        
        logger.info(f"📊 OUTPUT SCAN RESULTS:")
        logger.info(f"   - Total files: {total_files}")
        logger.info(f"   - Total size: {scan_result['total_size_mb']:.2f} MB")
        logger.info(f"   - Transcriptions: {structure['transcriptions'].get('file_count', 0)} files")
        logger.info(f"   - Temp chunks: {structure['temp_chunks'].get('file_count', 0)} files")
        logger.info(f"   - Logs: {structure['logs'].get('file_count', 0)} files")
        logger.info(f"   - Other: {structure['other'].get('file_count', 0)} files")
        
        return scan_result
    
    def _scan_directory(self, directory: Path, include_subdirs: bool = True) -> Dict[str, Any]:
        """Scan a directory and return file statistics"""
        file_count = 0
        total_size = 0
        files = []
        
        try:
            for item in directory.iterdir():
                if item.is_file():
                    file_size = item.stat().st_size
                    file_count += 1
                    total_size += file_size
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'size': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(item.stat().st_mtime)
                    })
                elif item.is_dir() and include_subdirs:
                    subdir_stats = self._scan_directory(item)
                    file_count += subdir_stats['file_count']
                    total_size += subdir_stats['total_size']
                    files.extend(subdir_stats['files'])
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
        
        return {
            'file_count': file_count,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'files': files
        }
    
    def clean_temp_chunks(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean temporary chunk files"""
        logger.info("🧹 Cleaning temporary chunk files...")
        
        temp_chunks_dir = self.output_base_dir / "temp_chunks"
        if not temp_chunks_dir.exists():
            return {
                'status': 'not_found',
                'message': 'Temp chunks directory does not exist',
                'cleaned_files': 0,
                'cleaned_size': 0
            }
        
        cleaned_files = 0
        cleaned_size = 0
        
        try:
            for file_path in temp_chunks_dir.glob("chunk_*.json"):
                file_size = file_path.stat().st_size
                
                if dry_run:
                    logger.info(f"   📄 Would clean: {file_path.name} ({file_size / 1024:.1f} KB)")
                else:
                    file_path.unlink()
                    self.cleaned_files.append(str(file_path))
                    cleaned_files += 1
                    cleaned_size += file_size
                    logger.info(f"   ✅ Cleaned: {file_path.name} ({file_size / 1024:.1f} KB)")
            
            if not dry_run and cleaned_files > 0:
                # Try to remove empty directory
                try:
                    temp_chunks_dir.rmdir()
                    self.cleaned_dirs.append(str(temp_chunks_dir))
                    logger.info(f"   🗂️  Removed empty directory: {temp_chunks_dir}")
                except OSError:
                    # Directory not empty or other error
                    pass
        
        except Exception as e:
            logger.error(f"Error cleaning temp chunks: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'cleaned_files': cleaned_files,
                'cleaned_size': cleaned_size
            }
        
        result = {
            'status': 'success',
            'cleaned_files': cleaned_files,
            'cleaned_size': cleaned_size,
            'cleaned_size_mb': cleaned_size / (1024 * 1024)
        }
        
        logger.info(f"📊 TEMP CHUNKS CLEANUP:")
        logger.info(f"   - Files cleaned: {cleaned_files}")
        logger.info(f"   - Size cleaned: {result['cleaned_size_mb']:.2f} MB")
        
        return result
    
    def clean_old_transcriptions(self, days_old: int = 7, dry_run: bool = False) -> Dict[str, Any]:
        """Clean transcription files older than specified days"""
        logger.info(f"🧹 Cleaning transcriptions older than {days_old} days...")
        
        transcriptions_dir = self.output_base_dir / "transcriptions"
        if not transcriptions_dir.exists():
            return {
                'status': 'not_found',
                'message': 'Transcriptions directory does not exist',
                'cleaned_files': 0,
                'cleaned_size': 0
            }
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_files = 0
        cleaned_size = 0
        
        try:
            for file_path in transcriptions_dir.rglob("*"):
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_modified < cutoff_date:
                        file_size = file_path.stat().st_size
                        
                        if dry_run:
                            logger.info(f"   📄 Would clean: {file_path.name} ({file_modified.strftime('%Y-%m-%d')})")
                        else:
                            file_path.unlink()
                            self.cleaned_files.append(str(file_path))
                            cleaned_files += 1
                            cleaned_size += file_size
                            logger.info(f"   ✅ Cleaned: {file_path.name} ({file_modified.strftime('%Y-%m-%d')})")
            
            # Clean up empty directories
            if not dry_run:
                self._cleanup_empty_directories(transcriptions_dir)
        
        except Exception as e:
            logger.error(f"Error cleaning old transcriptions: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'cleaned_files': cleaned_files,
                'cleaned_size': cleaned_size
            }
        
        result = {
            'status': 'success',
            'cleaned_files': cleaned_files,
            'cleaned_size': cleaned_size,
            'cleaned_size_mb': cleaned_size / (1024 * 1024),
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d')
        }
        
        logger.info(f"📊 OLD TRANSCRIPTIONS CLEANUP:")
        logger.info(f"   - Files cleaned: {cleaned_files}")
        logger.info(f"   - Size cleaned: {result['cleaned_size_mb']:.2f} MB")
        logger.info(f"   - Cutoff date: {result['cutoff_date']}")
        
        return result
    
    def clean_logs(self, days_old: int = 30, dry_run: bool = False) -> Dict[str, Any]:
        """Clean log files older than specified days"""
        logger.info(f"🧹 Cleaning logs older than {days_old} days...")
        
        logs_dir = self.output_base_dir / "logs"
        if not logs_dir.exists():
            return {
                'status': 'not_found',
                'message': 'Logs directory does not exist',
                'cleaned_files': 0,
                'cleaned_size': 0
            }
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_files = 0
        cleaned_size = 0
        
        try:
            for file_path in logs_dir.rglob("*.log"):
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_modified < cutoff_date:
                        file_size = file_path.stat().st_size
                        
                        if dry_run:
                            logger.info(f"   📄 Would clean: {file_path.name} ({file_modified.strftime('%Y-%m-%d')})")
                        else:
                            file_path.unlink()
                            self.cleaned_files.append(str(file_path))
                            cleaned_files += 1
                            cleaned_size += file_size
                            logger.info(f"   ✅ Cleaned: {file_path.name} ({file_modified.strftime('%Y-%m-%d')})")
            
            # Clean up empty directories
            if not dry_run:
                self._cleanup_empty_directories(logs_dir)
        
        except Exception as e:
            logger.error(f"Error cleaning logs: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'cleaned_files': cleaned_files,
                'cleaned_size': cleaned_size
            }
        
        result = {
            'status': 'success',
            'cleaned_files': cleaned_files,
            'cleaned_size': cleaned_size,
            'cleaned_size_mb': cleaned_size / (1024 * 1024),
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d')
        }
        
        logger.info(f"📊 LOGS CLEANUP:")
        logger.info(f"   - Files cleaned: {cleaned_files}")
        logger.info(f"   - Size cleaned: {result['cleaned_size_mb']:.2f} MB")
        logger.info(f"   - Cutoff date: {result['cutoff_date']}")
        
        return result
    
    def clean_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean all output files (use with caution!)"""
        logger.warning("⚠️  CLEANING ALL OUTPUT FILES!")
        
        if not dry_run:
            confirm = input("Are you sure you want to delete ALL output files? (yes/no): ")
            if confirm.lower() != 'yes':
                logger.info("Cleanup cancelled by user")
                return {
                    'status': 'cancelled',
                    'message': 'Cleanup cancelled by user'
                }
        
        if not self.output_base_dir.exists():
            return {
                'status': 'not_found',
                'message': 'Output directory does not exist'
            }
        
        try:
            if dry_run:
                logger.info(f"   📄 Would clean entire directory: {self.output_base_dir}")
                # Count files that would be deleted
                file_count = sum(1 for _ in self.output_base_dir.rglob("*") if _.is_file())
                logger.info(f"   📄 Would delete {file_count} files")
            else:
                shutil.rmtree(self.output_base_dir)
                self.cleaned_dirs.append(str(self.output_base_dir))
                logger.info(f"   ✅ Cleaned entire output directory: {self.output_base_dir}")
        
        except Exception as e:
            logger.error(f"Error cleaning all output: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
        
        return {
            'status': 'success',
            'message': 'All output files cleaned'
        }
    
    def _cleanup_empty_directories(self, directory: Path):
        """Remove empty directories recursively"""
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    self._cleanup_empty_directories(item)
                    try:
                        item.rmdir()
                        self.cleaned_dirs.append(str(item))
                        logger.info(f"   🗂️  Removed empty directory: {item}")
                    except OSError:
                        # Directory not empty
                        pass
        except Exception as e:
            logger.error(f"Error cleaning empty directories: {e}")
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get summary of cleanup operations"""
        total_size_mb = 0
        if self.cleaned_files:
            for f in self.cleaned_files:
                try:
                    total_size_mb += Path(f).stat().st_size / (1024 * 1024)
                except FileNotFoundError:
                    # File was already deleted, skip it
                    pass
        
        return {
            'cleaned_files': len(self.cleaned_files),
            'cleaned_directories': len(self.cleaned_dirs),
            'total_size_cleaned_mb': total_size_mb,
            'cleaned_files_list': self.cleaned_files,
            'cleaned_directories_list': self.cleaned_dirs
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Clean output folders and temporary files')
    parser.add_argument('--output-dir', default='output', help='Output directory to clean')
    parser.add_argument('--temp-chunks', action='store_true', help='Clean temporary chunk files')
    parser.add_argument('--old-transcriptions', type=int, metavar='DAYS', help='Clean transcriptions older than DAYS')
    parser.add_argument('--old-logs', type=int, metavar='DAYS', help='Clean logs older than DAYS')
    parser.add_argument('--all', action='store_true', help='Clean all output files (use with caution!)')
    parser.add_argument('--scan-only', action='store_true', help='Only scan, do not clean')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without actually cleaning')
    
    args = parser.parse_args()
    
    # Create cleaner
    cleaner = OutputCleaner(args.output_dir)
    
    # Scan output structure
    scan_result = cleaner.scan_output_structure()
    
    if scan_result['status'] == 'not_found':
        logger.error(f"Output directory not found: {args.output_dir}")
        return
    
    if args.scan_only:
        logger.info("📋 Scan only mode - no cleaning performed")
        return
    
    # Perform cleaning operations
    results = {}
    
    if args.temp_chunks:
        results['temp_chunks'] = cleaner.clean_temp_chunks(dry_run=args.dry_run)
    
    if args.old_transcriptions:
        results['old_transcriptions'] = cleaner.clean_old_transcriptions(
            days_old=args.old_transcriptions, 
            dry_run=args.dry_run
        )
    
    if args.old_logs:
        results['old_logs'] = cleaner.clean_logs(
            days_old=args.old_logs, 
            dry_run=args.dry_run
        )
    
    if args.all:
        results['all'] = cleaner.clean_all(dry_run=args.dry_run)
    
    # Print summary
    if results:
        summary = cleaner.get_cleanup_summary()
        logger.info(f"📋 CLEANUP SUMMARY:")
        logger.info(f"   - Files cleaned: {summary['cleaned_files']}")
        logger.info(f"   - Directories cleaned: {summary['cleaned_directories']}")
        logger.info(f"   - Total size cleaned: {summary['total_size_cleaned_mb']:.2f} MB")
        
        if args.dry_run:
            logger.info("🔍 DRY RUN MODE - No files were actually deleted")
    else:
        logger.info("💡 No cleaning operations specified. Use --help for options.")

if __name__ == "__main__":
    main()
