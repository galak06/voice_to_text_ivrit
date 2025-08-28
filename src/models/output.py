#!/usr/bin/env python3
"""
Output configuration model
"""

from pydantic import BaseModel, Field, ConfigDict


class OutputConfig(BaseModel):
    """Output and logging configuration"""
    
    output_dir: str = Field(default="output/transcriptions", description="Base output directory")
    logs_dir: str = Field(default="output/logs", description="Logs directory")
    transcriptions_dir: str = Field(default="output/transcriptions", description="Transcriptions directory")
    temp_dir: str = Field(default="output/temp", description="Temporary files directory")
    chunk_results_dir: str = Field(default="output/chunk_results", description="Chunk processing results directory")
    audio_chunks_dir: str = Field(default="output/audio_chunks", description="Audio chunks directory")
    chunk_temp_dir: str = Field(default="output/temp_chunks", description="Chunk temporary files directory")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="transcription.log", description="Log file name")
    save_json: bool = Field(default=True, description="Save output as JSON")
    save_txt: bool = Field(default=True, description="Save output as text")
    save_docx: bool = Field(default=True, description="Save output as DOCX")
    cleanup_temp_files: bool = Field(default=True, description="Clean up temporary files")
    temp_file_retention_hours: int = Field(default=24, ge=1, le=168, description="Temp file retention in hours")
    auto_organize: bool = Field(default=True, description="Auto-organize output files")
    include_metadata: bool = Field(default=True, description="Include metadata in output")
    include_timestamps: bool = Field(default=True, description="Include timestamps in output")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 