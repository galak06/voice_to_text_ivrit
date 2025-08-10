#!/usr/bin/env python3
"""
Test runner for the voice-to-text transcription application
Runs all tests including unit and integration tests
"""

import sys
import unittest
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def discover_and_run_tests():
    """Discover and run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Test directories
    test_dirs = [
        'tests/unit',
        'tests/integration'
    ]
    
    # Discover tests in each directory
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            # Load tests from directory
            loader = unittest.TestLoader()
            suite = loader.discover(test_dir, pattern='test_*.py')
            test_suite.addTests(suite)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


def run_specific_test(test_path):
    """Run a specific test file"""
    if not os.path.exists(test_path):
        print(f"❌ Test file not found: {test_path}")
        return False
    
    # Load and run specific test
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(test_path), pattern=os.path.basename(test_path))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_unit_tests():
    """Run only unit tests"""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    unit_test_dir = 'tests/unit'
    if not os.path.exists(unit_test_dir):
        print(f"❌ Unit test directory not found: {unit_test_dir}")
        return False
    
    loader = unittest.TestLoader()
    suite = loader.discover(unit_test_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run only integration tests"""
    print("🔗 Running Integration Tests")
    print("=" * 50)
    
    integration_test_dir = 'tests/integration'
    if not os.path.exists(integration_test_dir):
        print(f"❌ Integration test directory not found: {integration_test_dir}")
        return False
    
    loader = unittest.TestLoader()
    suite = loader.discover(integration_test_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def list_available_tests():
    """List all available test files"""
    print("📋 Available Tests")
    print("=" * 50)
    
    test_dirs = {
        'Unit Tests': 'tests/unit',
        'Integration Tests': 'tests/integration',
    }
    
    for category, test_dir in test_dirs.items():
        print(f"\n{category}:")
        if os.path.exists(test_dir):
            test_files = []
            for root, dirs, files in os.walk(test_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), test_dir)
                        test_files.append(rel_path)
            
            if test_files:
                for test_file in sorted(test_files):
                    print(f"  - {test_file}")
            else:
                print("  No test files found")
        else:
            print(f"  Directory not found: {test_dir}")


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for voice-to-text transcription application')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--file', type=str, help='Run specific test file')
    parser.add_argument('--list', action='store_true', help='List all available tests')
    
    args = parser.parse_args()
    
    print("🧪 Voice-to-Text Transcription Test Suite")
    print("=" * 60)
    
    if args.list:
        list_available_tests()
        return 0
    
    if args.file:
        print(f"🎯 Running specific test: {args.file}")
        success = run_specific_test(args.file)
    elif args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    else:
        print("🚀 Running All Tests")
        print("=" * 50)
        result = discover_and_run_tests()
        success = result.wasSuccessful()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 