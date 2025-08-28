#!/usr/bin/env python3
"""
Speaker labeling service protocols
Defines contracts for different speaker labeling behaviors
Follows Interface Segregation Principle (ISP)
"""

from typing import Protocol, Dict, Any, Optional


class SpeakerLabelingProtocol(Protocol):
    """Protocol for speaker labeling services"""
    
    def should_label_speakers(self, config: Dict[str, Any]) -> bool:
        """Determine if speaker labeling should be enabled"""
        ...
    
    def get_speaker_label(self, speaker_id: str, segment_data: Dict[str, Any]) -> Optional[str]:
        """Get speaker label for a segment"""
        ...
    
    def is_enabled(self) -> bool:
        """Check if speaker labeling is enabled"""
        ...


class SpeakerLabelingConfigProtocol(Protocol):
    """Protocol for speaker labeling configuration"""
    
    def is_speaker_labeling_enabled(self) -> bool:
        """Check if speaker labeling is enabled in configuration"""
        ...
    
    def get_labeling_strategy(self) -> str:
        """Get the labeling strategy to use"""
        ...
