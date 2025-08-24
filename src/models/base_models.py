#!/usr/bin/env python3
"""
Base Pydantic models with common functionality
"""

from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class BaseConfigModel(BaseModel):
    """Base configuration model with common functionality"""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
        use_enum_values=True
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return self.model_dump()
    
    def update(self, **kwargs) -> None:
        """Update model with new values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate_and_update(self, **kwargs) -> bool:
        """Validate and update model, return success status"""
        try:
            self.update(**kwargs)
            return True
        except Exception:
            return False


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorInfo(BaseConfigModel):
    """Standardized error information"""
    
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate error code format"""
        if not v or not v.strip():
            raise ValueError("Error code cannot be empty")
        return v.strip().upper()


class ProcessingResult(BaseConfigModel):
    """Standardized processing result"""
    
    success: bool = Field(description="Whether processing was successful")
    status: ProcessingStatus = Field(description="Processing status")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Processing result data")
    error: Optional[ErrorInfo] = Field(default=None, description="Error information if failed")
    processing_time: float = Field(default=0.0, ge=0.0, description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Result timestamp")
    
    @field_validator('error')
    @classmethod
    def validate_error_present_when_failed(cls, v: Optional[ErrorInfo], info) -> Optional[ErrorInfo]:
        """Ensure error is present when success is False"""
        if not info.data.get('success', True) and v is None:
            raise ValueError("Error information must be provided when processing fails")
        return v


class SessionInfo(BaseConfigModel):
    """Session information for tracking processing"""
    
    session_id: str = Field(description="Unique session identifier")
    start_time: datetime = Field(default_factory=datetime.now, description="Session start time")
    end_time: Optional[datetime] = Field(default=None, description="Session end time")
    total_files: int = Field(default=0, ge=0, description="Total files processed")
    successful_files: int = Field(default=0, ge=0, description="Successfully processed files")
    failed_files: int = Field(default=0, ge=0, description="Failed files")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.successful_files / self.total_files) * 100
    
    @property
    def duration(self) -> float:
        """Calculate session duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def mark_completed(self) -> None:
        """Mark session as completed"""
        self.end_time = datetime.now()


class PerformanceMetrics(BaseConfigModel):
    """Performance metrics for monitoring"""
    
    memory_usage_mb: float = Field(default=0.0, ge=0.0, description="Memory usage in MB")
    cpu_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="CPU usage percentage")
    processing_time_seconds: float = Field(default=0.0, ge=0.0, description="Processing time in seconds")
    throughput_files_per_minute: float = Field(default=0.0, ge=0.0, description="Files processed per minute")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metrics timestamp")
    
    def update_throughput(self, files_processed: int, time_seconds: float) -> None:
        """Update throughput calculation"""
        if time_seconds > 0:
            self.throughput_files_per_minute = (files_processed / time_seconds) * 60
