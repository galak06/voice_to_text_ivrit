"""
Transcription result collector implementations
"""

import time
from typing import List, Dict, Any


class TranscriptionResultCollector:
    """Default implementation of transcription result collector"""
    
    def collect(self, run_request, max_timeouts: int = 5) -> List[Dict[str, Any]]:
        """Collect transcription results from RunPod"""
        segments = []
        timeouts = 0
        
        while True:
            try:
                for segment in run_request.stream():
                    if "error" in segment:
                        raise RuntimeError(f"Transcription error: {segment['error']}")
                    
                    segments.append(segment)
                
                break  # Successfully completed
                
            except Exception as e:
                timeouts += 1
                if timeouts > max_timeouts:
                    raise RuntimeError(f"Too many timeouts ({max_timeouts})")
                
                time.sleep(1)
        
        return segments
