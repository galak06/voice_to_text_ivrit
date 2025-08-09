"""
Transcription Result Collector Interface
Defines the contract for collecting transcription results
"""

from typing import Dict, Any, List, Protocol


class TranscriptionResultCollectorInterface(Protocol):
    """Protocol for collecting transcription results"""
    
    def collect(self, run_request, max_timeouts: int = 5) -> List[Dict[str, Any]]:
        """
        Collect transcription results
        
        Args:
            run_request: The run request to collect results from
            max_timeouts: Maximum number of timeouts to allow
            
        Returns:
            List of transcription result segments
        """
        ... 