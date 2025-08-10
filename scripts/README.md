# Helper Scripts

This folder contains utility scripts for the voice-to-text transcription project.

## Scripts Overview

### `clean_output.py`
**Purpose**: Clean and manage transcription output folders and temporary files.

**Usage**:
```bash
python scripts/clean_output.py [options]
```

**Options**:
- `--temp-chunks`: Clean temporary chunk files
- `--old-transcriptions DAYS`: Clean transcription files older than DAYS
- `--old-logs DAYS`: Clean log files older than DAYS
- `--all`: Clean all output files (dangerous!)
- `--scan-only`: Only scan and report, don't clean
- `--dry-run`: Show what would be cleaned without actually cleaning

**Examples**:
```bash
# Scan output directory
python scripts/clean_output.py --scan-only

# Clean temp chunks with dry run
python scripts/clean_output.py --temp-chunks --dry-run

# Clean temp chunks
python scripts/clean_output.py --temp-chunks

# Clean old transcriptions (older than 30 days)
python scripts/clean_output.py --old-transcriptions 30
```

### `download_ivrit_model.py`
**Purpose**: Download the Hebrew-optimized Whisper model.

**Usage**:
```bash
python scripts/download_ivrit_model.py
```

**Description**: Downloads the `ivrit-ai/whisper-large-v3` model for Hebrew transcription.

### `infer.py`
**Purpose**: Direct inference script for quick transcription testing.

**Usage**:
```bash
python scripts/infer.py <audio_file>
```

**Description**: Simple script for testing transcription on individual audio files.

### `monitor_progress.py`
**Purpose**: Monitor transcription progress in real-time.

**Usage**:
```bash
python scripts/monitor_progress.py [options]
```

**Options**:
- `--output-dir`: Output directory to monitor
- `--interval`: Monitoring interval in seconds (default: 5)

**Description**: Provides real-time monitoring of transcription progress, including chunk processing status and output file generation.

### `test_small_chunk.py`
**Purpose**: Test small chunk processing functionality.

**Usage**:
```bash
python scripts/test_small_chunk.py
```

**Description**: Test script for verifying chunk processing logic and temporary file management.

## Running Scripts

All scripts should be run from the project root directory:

```bash
# From /Users/gilcohen/voic_to_text_docker
python scripts/script_name.py [options]
```

## Dependencies

Make sure you have all required dependencies installed:

```bash
pip install -r requirements.txt
```

## Safety Features

- **Dry Run Mode**: Most scripts support `--dry-run` to preview changes
- **Confirmation Prompts**: Dangerous operations require user confirmation
- **Logging**: All scripts provide detailed logging for transparency
- **Error Handling**: Robust error handling with graceful fallbacks

## Best Practices

1. **Always use dry-run first**: Test what a script will do before running it
2. **Monitor disk space**: Large audio files can consume significant disk space
3. **Check logs**: Review logs for any issues or warnings
4. **Backup important files**: Before running cleanup scripts, ensure important files are backed up
5. **Use appropriate configurations**: Different scripts may require different environment configurations
