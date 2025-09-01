#!/usr/bin/env python3
"""
Test runner for Wild Ginger Bot
Runs all tests and provides a comprehensive report
"""

import pytest
import sys
import os
import subprocess
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_tests():
    """Run all tests and generate a report"""
    print("🧪 Starting Wild Ginger Bot Test Suite")
    print("=" * 50)
    
    # Get current timestamp
    start_time = datetime.now()
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # List of test files to run
    test_files = [
        "test_wild_ginger_bot.py",
        "test_models.py", 
        "test_user_service.py",
        "test_message_service.py",
        "test_file_storage_service.py",
        "test_event_service.py",
        "test_registration_service.py",
        "test_user_scenarios.py",
        "test_form_flow_scenarios.py"
    ]
    
    # Check which test files exist
    existing_tests = []
    for test_file in test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            existing_tests.append(test_file)
        else:
            print(f"⚠️  Warning: Test file {test_file} not found")
    
    if not existing_tests:
        print("❌ No test files found!")
        return False
    
    print(f"📋 Found {len(existing_tests)} test files:")
    for test_file in existing_tests:
        print(f"   - {test_file}")
    print()
    
    # Run pytest with verbose output
    try:
        # Change to the tests directory
        os.chdir(os.path.dirname(__file__))
        
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--color=yes",  # Colored output
            "--durations=10",  # Show 10 slowest tests
            "--cov=telegram_bot",  # Coverage for telegram_bot package
            "--cov=wild_ginger_bot",  # Coverage for main bot file
            "--cov-report=term-missing",  # Show missing lines in coverage
            "--cov-report=html:htmlcov",  # Generate HTML coverage report
            "--cov-report=xml",  # Generate XML coverage report
            "--junitxml=test-results.xml",  # Generate JUnit XML report
            "--html=test-report.html",  # Generate HTML test report
            "--self-contained-html",  # Self-contained HTML report
        ] + existing_tests
        
        print("🚀 Running tests...")
        print("Command:", " ".join(cmd))
        print()
        
        # Run the tests
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print()
        print("=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        print(f"Duration: {duration}")
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        
        print()
        print("📁 Generated Reports:")
        print("   - HTML Coverage Report: htmlcov/index.html")
        print("   - XML Coverage Report: coverage.xml")
        print("   - JUnit XML Report: test-results.xml")
        print("   - HTML Test Report: test-report.html")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_specific_test(test_file):
    """Run a specific test file"""
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found!")
        return False
    
    print(f"🧪 Running specific test: {test_file}")
    print("=" * 50)
    
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",
            "--tb=short",
            "--color=yes",
            test_file
        ]
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def run_unit_tests_only():
    """Run only unit tests (no integration tests)"""
    print("🧪 Running Unit Tests Only")
    print("=" * 50)
    
    unit_test_files = [
        "test_models.py",
        "test_user_service.py", 
        "test_message_service.py",
        "test_file_storage_service.py",
        "test_event_service.py",
        "test_registration_service.py",
        "test_user_scenarios.py",
        "test_form_flow_scenarios.py"
    ]
    
    existing_unit_tests = []
    for test_file in unit_test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            existing_unit_tests.append(test_file)
    
    if not existing_unit_tests:
        print("❌ No unit test files found!")
        return False
    
    try:
        os.chdir(os.path.dirname(__file__))
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",
            "--tb=short",
            "--color=yes",
            "--cov=telegram_bot",
            "--cov-report=term-missing",
        ] + existing_unit_tests
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            success = run_unit_tests_only()
        elif command == "specific" and len(sys.argv) > 2:
            test_file = sys.argv[2]
            success = run_specific_test(test_file)
        else:
            print("Usage:")
            print("  python run_all_tests.py          # Run all tests")
            print("  python run_all_tests.py unit     # Run unit tests only")
            print("  python run_all_tests.py specific <test_file>  # Run specific test file")
            return
    else:
        success = run_tests()
    
    if success:
        print("\n🎉 Test run completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test run failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 