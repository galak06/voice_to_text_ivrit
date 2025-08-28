#!/usr/bin/env python3
"""
Test script to verify cleanup manager functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_cleanup_manager():
    """Test the cleanup manager directly"""
    print("🧹 Testing Cleanup Manager...")
    
    try:
        from src.core.engines.utilities.cleanup_manager import CleanupManager
        print("✅ Successfully imported CleanupManager")
        
        # Create a simple config object
        class SimpleConfig:
            def __init__(self):
                self.cleanup_logs_before_run = True
                self.max_output_files = 5
        
        config = SimpleConfig()
        print("✅ Created test config")
        
        # Initialize cleanup manager
        cleanup_manager = CleanupManager(config)
        print("✅ CleanupManager initialized")
        
        # Check current state
        from definition import CHUNK_RESULTS_DIR, TEMP_DIR
        print(f"📁 CHUNK_RESULTS_DIR: {CHUNK_RESULTS_DIR}")
        print(f"📁 TEMP_DIR: {TEMP_DIR}")
        
        if os.path.exists(CHUNK_RESULTS_DIR):
            files = os.listdir(CHUNK_RESULTS_DIR)
            print(f"📁 Found {len(files)} files in chunk_results: {files[:5]}...")
        else:
            print("📁 chunk_results directory does not exist")
        
        if os.path.exists(TEMP_DIR):
            temp_files = os.listdir(TEMP_DIR)
            print(f"📁 Found {len(temp_files)} files in temp: {temp_files[:5]}...")
        else:
            print("📁 temp directory does not exist")
        
        # Execute cleanup
        print("🧹 Executing cleanup...")
        cleanup_manager.execute_cleanup(clear_console=True, clear_files=True, clear_output=False)
        print("✅ Cleanup execution completed")
        
        # Check state after cleanup
        print("🧹 Checking state after cleanup...")
        if os.path.exists(CHUNK_RESULTS_DIR):
            remaining_files = os.listdir(CHUNK_RESULTS_DIR)
            print(f"📁 After cleanup: chunk_results has {len(remaining_files)} files")
            if remaining_files:
                print(f"⚠️  WARNING: Files still exist: {remaining_files[:5]}...")
            else:
                print("✅ SUCCESS: All files were cleaned up!")
        else:
            print("📁 chunk_results directory was completely removed")
        
        if os.path.exists(TEMP_DIR):
            temp_files = os.listdir(TEMP_DIR)
            print(f"📁 After cleanup: temp has {len(temp_files)} files")
        else:
            print("📁 temp directory was completely removed")
            
    except Exception as e:
        print(f"❌ Error testing cleanup manager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cleanup_manager()
