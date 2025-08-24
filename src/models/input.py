#!/usr/bin/env python3
"""
Input configuration model
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class InputConfig(BaseModel):
    """Input file configuration"""
    
    directory: str = Field(default="examples/audio/voice", description="Input directory path")
    supported_formats: Optional[List[str]] = Field(
        default_factory=lambda: [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"],
        description="List of supported audio file formats"
    )
    recursive_search: bool = Field(default=True, description="Search recursively in subdirectories")
    max_file_size_mb: int = Field(default=100, ge=1, le=1000, description="Maximum file size in MB")
    validate_files: bool = Field(default=True, description="Validate input files")
    auto_discover: bool = Field(default=True, description="Auto-discover audio files")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 