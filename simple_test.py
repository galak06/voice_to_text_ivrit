#!/usr/bin/env python3
"""
Simple test for the refactored chunking system
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test basic imports"""
    try:
        print("🧪 Testing basic imports...")
        
        # Test importing the chunking strategy directly
        from src.core.engines.strategies.chunking_strategy import ChunkingStrategy
        print("✅ ChunkingStrategy imported successfully")
        
        from src.core.engines.strategies.chunking_strategy import OverlappingChunkingStrategy
        print("✅ OverlappingChunkingStrategy imported successfully")
        
        from src.core.engines.strategies.chunking_strategy import FixedDurationChunkingStrategy
        print("✅ FixedDurationChunkingStrategy imported successfully")
        
        from src.core.engines.strategies.chunking_strategy import ChunkingStrategyFactory
        print("✅ ChunkingStrategyFactory imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_services():
    """Test service imports"""
    try:
        print("🧪 Testing service imports...")
        
        from src.core.services.chunk_management_service import ChunkManagementService
        print("✅ ChunkManagementService imported successfully")
        
        from src.core.services.chunk_processing_service import ChunkProcessingService
        print("✅ ChunkProcessingService imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Service import failed: {e}")
        return False

def main():
    """Run basic tests"""
    print("🚀 Starting basic chunking system tests...")
    print("=" * 50)
    
    # Test 1: Basic imports
    if not test_basic_imports():
        print("❌ Basic imports failed")
        return False
    
    # Test 2: Service imports
    if not test_services():
        print("❌ Service imports failed")
        return False
    
    print("=" * 50)
    print("✅ All basic tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

