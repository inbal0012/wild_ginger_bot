#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test runner for Wild Ginger Telegram Bot - Microservice Architecture
Runs all tests for the new professional microservice architecture
"""

import subprocess
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"🧪 {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                # Filter out verbose output, show summary
                lines = result.stdout.split('\n')
                summary_lines = [line for line in lines if any(keyword in line for keyword in ['passed', 'failed', 'error', 'PASSED', 'FAILED', 'ERROR', '=='])]
                if summary_lines:
                    print('\n'.join(summary_lines))
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

def check_dependencies():
    """Check and install required test dependencies"""
    required_packages = [
        'pytest',
        'pytest-asyncio', 
        'pytest-cov',
        'pytest-mock'
    ]
    
    print("🔧 Checking test dependencies...")
    
    for package in required_packages:
        result = subprocess.run(f"pip show {package}", shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"⚠️  Installing {package}...")
            install_result = subprocess.run(f"pip install {package}", shell=True, capture_output=True)
            if install_result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
                return False
    
    print("✅ All dependencies checked")
    return True

def main():
    """Main test runner for microservice architecture"""
    print("🚀 Wild Ginger Telegram Bot - Microservice Test Suite")
    print("=" * 70)
    print("🎯 Testing Professional Architecture with 8 Services")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to install required dependencies")
        return False
    
    # Test configurations for the new architecture
    test_configs = [
        {
            'name': 'Individual Service Tests',
            'command': 'python -m pytest test_microservices.py::TestSheetsService -v',
            'description': 'Test SheetsService microservice'
        },
        {
            'name': 'Message Service Tests',
            'command': 'python -m pytest test_microservices.py::TestMessageService -v',
            'description': 'Test MessageService microservice'
        },
        {
            'name': 'Reminder Service Tests',
            'command': 'python -m pytest test_microservices.py::TestReminderService -v',
            'description': 'Test ReminderService microservice'
        },
        {
            'name': 'Conversation Service Tests',
            'command': 'python -m pytest test_microservices.py::TestConversationService -v',
            'description': 'Test ConversationService microservice (get-to-know flow)'
        },
        {
            'name': 'Admin Service Tests',
            'command': 'python -m pytest test_microservices.py::TestAdminService -v',
            'description': 'Test AdminService microservice'
        },
        {
            'name': 'Background Scheduler Tests',
            'command': 'python -m pytest test_microservices.py::TestBackgroundScheduler -v',
            'description': 'Test BackgroundScheduler microservice'
        },
        {
            'name': 'Cancellation Service Tests',
            'command': 'python -m pytest test_microservices.py::TestCancellationService -v',
            'description': 'Test CancellationService microservice'
        },
        {
            'name': 'Monitoring Service Tests',
            'command': 'python -m pytest test_microservices.py::TestMonitoringService -v',
            'description': 'Test MonitoringService microservice'
        },
        {
            'name': 'Service Integration Tests',
            'command': 'python -m pytest test_microservices.py::TestServiceIntegration -v',
            'description': 'Test integration between microservices'
        },
        {
            'name': 'Complete Microservice Suite',
            'command': 'python -m pytest test_microservices.py -v',
            'description': 'Run all microservice tests together'
        },
        {
            'name': 'Legacy Integration Tests (Adapted)',
            'command': 'python -m pytest test_legacy_integration.py -v',
            'description': 'Run adapted legacy integration tests'
        },
        {
            'name': 'Bot Commands Integration',
            'command': 'python -m pytest test_bot_commands.py -v', 
            'description': 'Test bot command handlers with services'
        },
        {
            'name': 'Test Coverage Report',
            'command': 'python -m pytest test_microservices.py --cov=telegram_bot --cov-report=html --cov-report=term',
            'description': 'Generate test coverage report for microservices'
        },
        {
            'name': 'End-to-End Tests (E2E)',
            'command': 'python -m pytest test_e2e_comprehensive.py -v',
            'description': 'Run comprehensive end-to-end system tests'
        },
        {
            'name': 'E2E Happy Path',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestCompleteUserJourney::test_happy_path_complete_user_journey -v',
            'description': 'Test complete happy path user journey'
        },
        {
            'name': 'E2E Edge Cases',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures -v',
            'description': 'Test system edge cases and failure handling'
        }
    ]
    
    # Run all tests
    results = []
    start_time = datetime.now()
    
    for config in test_configs:
        success = run_command(config['command'], config['description'])
        results.append({
            'name': config['name'],
            'success': success,
            'description': config['description']
        })
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 MICROSERVICE TEST RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"🕐 Total time: {duration}")
    print(f"📝 Total tests: {len(results)}")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {passed/len(results)*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"  {status} - {result['name']}")
    
    # Service-specific summary
    print(f"\n🏗️ MICROSERVICE ARCHITECTURE TEST STATUS:")
    service_tests = [
        ("SheetsService", "Google Sheets Integration"),
        ("MessageService", "Multilingual Messaging"),
        ("ReminderService", "Partner Reminder System"),
        ("ConversationService", "Interactive Get-to-Know Flow"),
        ("AdminService", "Administrative Management"),
        ("BackgroundScheduler", "Automated Task Scheduling"),
        ("CancellationService", "Registration Cancellation"),
        ("MonitoringService", "Sheet1 Monitoring System"),
    ]
    
    e2e_tests = [
        ("E2E Tests", "Complete User Journeys & Edge Cases"),
        ("E2E Happy Path", "End-to-End User Flow Validation"),
        ("E2E Edge Cases", "System Failure & Recovery Testing"),
    ]
    
    for service_name, description in service_tests:
        service_result = next((r for r in results if service_name in r['name']), None)
        if service_result:
            status = "✅" if service_result['success'] else "❌"
            print(f"  {status} {service_name}: {description}")
    
    print(f"\n🎯 END-TO-END TEST STATUS:")
    for test_name, description in e2e_tests:
        e2e_result = next((r for r in results if test_name in r['name']), None)
        if e2e_result:
            status = "✅" if e2e_result['success'] else "❌"
            print(f"  {status} {test_name}: {description}")
    
    # Architecture validation
    print(f"\n🎯 ARCHITECTURE VALIDATION:")
    if passed >= len(results) * 0.8:  # 80% pass rate
        print("✅ Microservice architecture is stable and ready for production")
        print("🏆 Professional quality achieved!")
    elif passed >= len(results) * 0.6:  # 60% pass rate
        print("⚠️  Microservice architecture needs some attention")
        print("🔧 Some services require fixes")
    else:
        print("❌ Microservice architecture needs significant work")
        print("🚨 Multiple services are failing")
    
    # Next steps
    if failed > 0:
        print(f"\n🔧 NEXT STEPS:")
        print("1. Review failed test outputs above")
        print("2. Fix failing services and tests")
        print("3. Re-run tests: python run_microservice_tests.py")
        print("4. Check individual services with: python -m telegram_bot.test_[service_name]")
    else:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("🚀 Microservice architecture is production-ready!")
        print("🏆 Professional quality achieved!")
    
    return passed == len(results)

def run_quick_validation():
    """Run a quick validation of the microservice architecture"""
    print("⚡ Running quick microservice validation...")
    
    # Change to parent directory for imports
    original_dir = os.getcwd()
    parent_dir = os.path.dirname(os.getcwd()) if 'tests' in os.getcwd() else os.getcwd()
    
    quick_tests = [
        f'cd {parent_dir} && python -m telegram_bot.quick_test',
        f'cd {parent_dir} && python -c "from telegram_bot.services import *; print(\'✅ All services import successfully\')"',
        f'cd {parent_dir} && python -c "from telegram_bot.main import WildGingerBot; print(\'✅ Main bot class imports successfully\')"'
    ]
    
    all_passed = True
    for test in quick_tests:
        result = subprocess.run(test, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Quick test passed")
        else:
            print("❌ Quick test failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            all_passed = False
    
    return all_passed

def run_specific_service_test(service_name):
    """Run tests for a specific service"""
    service_map = {
        'sheets': 'TestSheetsService',
        'message': 'TestMessageService', 
        'reminder': 'TestReminderService',
        'conversation': 'TestConversationService',
        'admin': 'TestAdminService',
        'scheduler': 'TestBackgroundScheduler',
        'cancellation': 'TestCancellationService',
        'monitoring': 'TestMonitoringService',
        'integration': 'TestServiceIntegration',
        'e2e': 'test_e2e_comprehensive.py',
        'e2e-happy': 'test_e2e_comprehensive.py::TestCompleteUserJourney::test_happy_path_complete_user_journey',
        'e2e-edge': 'test_e2e_comprehensive.py::TestEdgeCasesAndFailures'
    }
    
    if service_name.lower() in service_map:
        test_class = service_map[service_name.lower()]
        if service_name.lower().startswith('e2e'):
            # E2E tests use different file
            command = f'python -m pytest {test_class} -v'
        else:
            # Regular service tests
            command = f'python -m pytest test_microservices.py::{test_class} -v'
        return run_command(command, f"Testing {service_name} service")
    else:
        print(f"❌ Unknown service: {service_name}")
        print(f"Available services: {', '.join(service_map.keys())}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'quick':
            # Run quick validation
            success = run_quick_validation()
            sys.exit(0 if success else 1)
            
        elif command in ['sheets', 'message', 'reminder', 'conversation', 'admin', 'scheduler', 'cancellation', 'monitoring', 'integration', 'e2e', 'e2e-happy', 'e2e-edge']:
            # Run specific service test
            success = run_specific_service_test(command)
            sys.exit(0 if success else 1)
            
        elif command == 'help':
            print("🧪 Microservice Test Runner")
            print("Usage:")
            print("  python run_microservice_tests.py           # Run all tests")
            print("  python run_microservice_tests.py quick     # Quick validation")
            print("  python run_microservice_tests.py [service] # Test specific service")
            print("")
            print("Available services:")
            print("  sheets, message, reminder, conversation, admin,")
            print("  scheduler, cancellation, monitoring, integration")
            print("")
            print("End-to-End tests:")
            print("  e2e, e2e-happy, e2e-edge")
            sys.exit(0)
    
    # Run full test suite
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏸️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 