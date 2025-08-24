#!/usr/bin/env python3
"""
RunPod configuration model
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RunPodConfig(BaseModel):
    """RunPod service configuration"""
    
    api_key: Optional[str] = Field(default=None, description="RunPod API key")
    endpoint_id: Optional[str] = Field(default=None, description="RunPod endpoint ID")
    max_payload_size: int = Field(default=200 * 1024 * 1024, ge=1024*1024, description="Maximum payload size in bytes (200MB)")
    streaming_enabled: bool = Field(default=True, description="Enable streaming mode")
    in_queue_timeout: int = Field(default=300, ge=30, le=1800, description="In-queue timeout in seconds")
    max_stream_timeouts: int = Field(default=5, ge=1, le=20, description="Maximum stream timeouts")
    max_payload_len: int = Field(default=10 * 1024 * 1024, ge=1024*1024, description="Maximum payload length in bytes (10MB)")
    enabled: bool = Field(default=False, description="Enable RunPod service")
    serverless_mode: bool = Field(default=True, description="Enable serverless mode")
    auto_scale: bool = Field(default=True, description="Enable auto-scaling")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 