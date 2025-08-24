#!/usr/bin/env python3
"""
Batch processing configuration model
"""

from pydantic import BaseModel, Field, ConfigDict


class BatchConfig(BaseModel):
    """Batch processing configuration"""
    
    enabled: bool = Field(default=True, description="Enable batch processing")
    parallel_processing: bool = Field(default=False, description="Enable parallel processing")
    max_workers: int = Field(default=1, ge=1, le=16, description="Maximum number of worker processes")
    delay_between_files: int = Field(default=0, ge=0, le=60, description="Delay between processing files in seconds")
    progress_tracking: bool = Field(default=True, description="Enable progress tracking")
    continue_on_error: bool = Field(default=True, description="Continue processing on file errors")
    timeout_per_file: int = Field(default=600, ge=30, le=3600, description="Timeout per file in seconds")
    retry_failed_files: bool = Field(default=True, description="Retry failed files")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum number of retries per file")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 