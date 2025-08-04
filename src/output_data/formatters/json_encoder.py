#!/usr/bin/env python3
"""
JSON Encoder
Handles custom JSON encoding for non-serializable objects
"""

import json
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle non-serializable objects"""
    
    def default(self, obj: Any) -> Any:
        """Handle non-serializable objects by converting them to strings"""
        try:
            # Try to convert to string representation
            return str(obj)
        except:
            # If that fails, return a placeholder
            return f"<Non-serializable object: {type(obj).__name__}>" 