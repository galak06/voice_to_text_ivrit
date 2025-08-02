#!/usr/bin/env python3
"""
Test runner for ivrit-ai voice transcription service
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=False):
    """Run tests based on type"""
    
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    test_dir = Path(__file__).parent
    
    if test_type == "all":
        test_patterns = ["test_*.py"]
    elif test_type == "unit":
        test_patterns = ["unit/test_*.py"]
    elif test_type == "integration":
        test_patterns = ["integration/test_*.py"]
    elif test_type == "e2e":
        test_patterns = ["e2e/test_*.py"]
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False
    
    all_tests = []
    for pattern in test_patterns:
        all_tests.extend(test_dir.glob(pattern))
    
    if not all_tests:
        print(f"❌ No tests found for type: {test_type}")
        return False
    
    print(f"🧪 Running {test_type} tests...")
    print(f"📁 Found {len(all_tests)} test files")
    
    success_count = 0
    total_count = len(all_tests)
    
    for test_file in all_tests:
        print(f"\n📝 Running: {test_file.name}")
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=project_root,
                capture_output=not verbose,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file.name} passed")
                success_count += 1
            else:
                print(f"❌ {test_file.name} failed")
                if not verbose and result.stdout:
                    print(f"Output: {result.stdout}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file.name} timed out")
        except Exception as e:
            print(f"❌ {test_file.name} error: {e}")
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    return success_count == total_count

def main():
    parser = argparse.ArgumentParser(description="Run ivrit-ai voice transcription tests")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "e2e"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    success = run_tests(args.type, args.verbose)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 