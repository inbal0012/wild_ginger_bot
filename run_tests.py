#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test runner for Wild Ginger Telegram Bot
Runs all tests with different configurations and generates reports
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Wild Ginger Telegram Bot Test Suite")
    print("=" * 60)
    
    # Check if required packages are installed
    required_packages = ['pytest', 'pytest-asyncio', 'pytest-cov']
    
    for package in required_packages:
        result = subprocess.run(f"pip show {package}", shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"⚠️  Installing {package}...")
            subprocess.run(f"pip install {package}", shell=True)
    
    # Test configurations
    test_configs = [
        {
            'name': 'Unit Tests',
            'command': 'python -m pytest test_telegram_bot.py -v',
            'description': 'Core unit tests for bot functionality'
        },
        {
            'name': 'Integration Tests',
            'command': 'python -m pytest test_integration.py -v',
            'description': 'End-to-end integration tests'
        },
        {
            'name': 'Mock Data Validation',
            'command': 'python test_fixtures.py',
            'description': 'Validate test fixtures and mock data'
        },
        {
            'name': 'Existing Tests',
            'command': 'python -m pytest test_reminders.py test_multipartner.py -v',
            'description': 'Run existing test files'
        },
        {
            'name': 'Admin Notification Tests',
            'command': 'python test_admin_notifications.py',
            'description': 'Test admin notification system and commands'
        },
        {
            'name': 'All Tests with Coverage',
            'command': 'python -m pytest test_telegram_bot.py test_integration.py --cov=telegram_bot_polling --cov-report=html --cov-report=term',
            'description': 'All tests with coverage report'
        }
    ]
    
    # Run tests
    results = []
    
    for config in test_configs:
        success = run_command(config['command'], config['description'])
        results.append({
            'name': config['name'],
            'success': success,
            'description': config['description']
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{status} - {result['name']}")
    
    print(f"\n📈 Overall Results:")
    print(f"   Total: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Generate test report
    if passed_tests > 0:
        print(f"\n📋 Test Report Generated:")
        print(f"   Coverage Report: htmlcov/index.html")
        print(f"   Run 'python -m http.server 8000' in project directory")
        print(f"   Then visit: http://localhost:8000/htmlcov/")
    
    # Exit with appropriate code
    sys.exit(0 if failed_tests == 0 else 1)

def run_specific_test(test_name):
    """Run a specific test category"""
    test_map = {
        'unit': 'python -m pytest test_telegram_bot.py -v',
        'integration': 'python -m pytest test_integration.py -v',
        'fixtures': 'python test_fixtures.py',
        'reminders': 'python -m pytest test_reminders.py -v',
        'multipartner': 'python -m pytest test_multipartner.py -v',
        'all': 'python -m pytest test_telegram_bot.py test_integration.py -v'
    }
    
    if test_name not in test_map:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_map.keys())}")
        return False
    
    return run_command(test_map[test_name], f"Running {test_name} tests")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        main() 