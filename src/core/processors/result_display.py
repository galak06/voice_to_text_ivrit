"""
Result display implementations
"""

from typing import List, Dict, Any


class ResultDisplay:
    """Default implementation of result display"""
    
    def display(self, segments: List[Dict[str, Any]]) -> None:
        """Display transcription results"""
        print("\n🎉 Transcription completed!")
        print("=" * 50)
        
        if segments:
            for i, segment in enumerate(segments, 1):
                if 'text' in segment:
                    print(f"{i}. {segment['text']}")
                if 'start' in segment and 'end' in segment:
                    print(f"   Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
                print()
        else:
            print("No transcription segments received")
