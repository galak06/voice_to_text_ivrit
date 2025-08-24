#!/usr/bin/env python3
"""
Environment configuration model
"""

from enum import Enum


class Environment(str, Enum):
    """Environment types for configuration management"""
    BASE = "base"
    DEVELOPMENT = "development"
    PRODUCTION = "production" 