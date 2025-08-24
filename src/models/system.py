#!/usr/bin/env python3
"""
System configuration model
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ApplicationConstants(BaseModel):
    """Application constants and thresholds"""
    
    # Performance monitoring
    max_metrics_history: int = Field(default=1000, ge=100, le=10000, description="Maximum number of metrics to keep in history")
    max_processing_stats_history: int = Field(default=100, ge=50, le=500, description="Maximum number of processing stats to keep")
    performance_log_threshold_seconds: int = Field(default=30, ge=10, le=300, description="Threshold for logging performance metrics")
    
    # Retry and backoff
    max_backoff_seconds: int = Field(default=30, ge=10, le=300, description="Maximum backoff time for retries")
    exponential_backoff_base: int = Field(default=2, ge=1, le=5, description="Base for exponential backoff calculation")
    
    # File processing
    large_file_threshold_mb: int = Field(default=100, ge=10, le=1000, description="Threshold for considering a file large")
    chunk_preview_length: int = Field(default=100, ge=50, le=500, description="Length of chunk preview in characters")
    
    # Timeouts
    default_request_timeout: int = Field(default=30, ge=10, le=300, description="Default HTTP request timeout")
    queue_wait_timeout: int = Field(default=300, ge=60, le=1800, description="Default queue wait timeout")
    
    # Validation thresholds
    min_timeout_per_file: int = Field(default=30, ge=10, le=300, description="Minimum timeout per file")
    min_silence_duration_ms: int = Field(default=300, ge=100, le=1000, description="Minimum silence duration for VAD")
    
    # Text processing
    min_text_length_for_segment: int = Field(default=10, ge=1, le=50, description="Minimum text length for a valid segment")
    min_segment_duration_seconds: int = Field(default=30, ge=10, le=300, description="Minimum duration for a valid segment")
    
    # Cleanup
    default_cleanup_days: int = Field(default=30, ge=1, le=365, description="Default days for cleanup operations")
    min_file_size_bytes: int = Field(default=1000, ge=100, le=10000, description="Minimum file size to consider valid")


class SystemConfig(BaseModel):
    """System and performance configuration"""
    
    debug: bool = Field(default=False, description="Enable debug mode")
    dev_mode: bool = Field(default=False, description="Enable development mode")
    hugging_face_token: Optional[str] = Field(default=None, description="Hugging Face API token")
    timeout_seconds: int = Field(default=300, ge=30, le=3600, description="Default timeout in seconds")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    auto_cleanup: bool = Field(default=True, description="Enable automatic cleanup")
    session_management: bool = Field(default=True, description="Enable session management")
    error_reporting: bool = Field(default=True, description="Enable error reporting")
    
    # Application constants
    constants: ApplicationConstants = Field(default_factory=ApplicationConstants, description="Application constants and thresholds")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 