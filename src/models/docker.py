#!/usr/bin/env python3
"""
Docker configuration model
"""

from pydantic import BaseModel, Field, ConfigDict


class DockerConfig(BaseModel):
    """Docker container configuration"""
    
    enabled: bool = Field(default=False, description="Enable Docker containerization")
    image_name: str = Field(default="whisper-runpod-serverless", description="Docker image name")
    tag: str = Field(default="latest", description="Docker image tag")
    container_name_prefix: str = Field(default="whisper-batch", description="Container name prefix")
    auto_cleanup: bool = Field(default=True, description="Automatically cleanup containers")
    timeout_seconds: int = Field(default=3600, ge=60, le=7200, description="Container timeout in seconds")
    memory_limit: str = Field(default="4g", description="Memory limit for containers")
    cpu_limit: str = Field(default="2", description="CPU limit for containers")
    kill_existing_containers: bool = Field(default=True, description="Kill existing containers before starting")
    detached_mode: bool = Field(default=True, description="Run containers in detached mode")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    ) 