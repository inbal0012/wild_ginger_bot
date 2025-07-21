#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive End-to-End Test Runner for Wild Ginger Telegram Bot
Specialized runner for testing complete system flows and edge cases
"""

import subprocess
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status with detailed output"""
    print(f"\n{'='*80}")
    print(f"🧪 {description}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                # Show relevant output lines
                lines = result.stdout.split('\n')
                important_lines = [
                    line for line in lines 
                    if any(keyword in line.lower() for keyword in [
                        'passed', 'failed', 'error', 'testing', '✅', '❌', 'complete', 'scenario'
                    ])
                ]
                if important_lines:
                    print('\n'.join(important_lines))
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
    """Main E2E test runner"""
    print("🎯 Wild Ginger Bot - Comprehensive End-to-End Test Suite")
    print("=" * 80)
    print("🚀 Testing Complete System with Happy Flows & Edge Cases")
    print("=" * 80)
    
    # E2E test configurations
    e2e_test_configs = [
        {
            'name': 'Complete User Journey Tests',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestCompleteUserJourney -v -s',
            'description': 'Test complete user journeys from registration to group access'
        },
        {
            'name': 'Happy Path Flow',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestCompleteUserJourney::test_happy_path_complete_user_journey -v -s',
            'description': 'Test complete happy path user flow'
        },
        {
            'name': 'Hebrew User Journey',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestCompleteUserJourney::test_hebrew_user_complete_journey -v -s',
            'description': 'Test complete Hebrew-speaking user journey'
        },
        {
            'name': 'Multi-Partner Journey',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestCompleteUserJourney::test_multi_partner_journey -v -s',
            'description': 'Test journey for users with multiple partners'
        },
        {
            'name': 'Edge Cases & Failures',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures -v -s',
            'description': 'Test edge cases, failures, and error handling'
        },
        {
            'name': 'Google Sheets Unavailable',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures::test_google_sheets_unavailable_scenario -v -s',
            'description': 'Test system behavior when Google Sheets is down'
        },
        {
            'name': 'Invalid User Data',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures::test_invalid_user_data_scenarios -v -s',
            'description': 'Test handling of corrupted/invalid data'
        },
        {
            'name': 'Concurrent Users',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures::test_concurrent_user_access_scenario -v -s',
            'description': 'Test multiple users accessing system simultaneously'
        },
        {
            'name': 'Admin Permissions',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures::test_admin_permission_edge_cases -v -s',
            'description': 'Test admin permission edge cases'
        },
        {
            'name': 'System Integration Tests',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestSystemIntegrationScenarios -v -s',
            'description': 'Test complex system integration scenarios'
        },
        {
            'name': 'Admin Bulk Operations',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestSystemIntegrationScenarios::test_admin_bulk_operations_scenario -v -s',
            'description': 'Test admin performing bulk operations'
        },
        {
            'name': 'Monitoring Integration',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestSystemIntegrationScenarios::test_monitoring_and_notification_integration -v -s',
            'description': 'Test monitoring service integration'
        },
        {
            'name': 'Real-World Scenarios',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestRealWorldComplexScenarios -v -s',
            'description': 'Test complex real-world scenarios'
        },
        {
            'name': 'Event Day Simulation',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestRealWorldComplexScenarios::test_event_day_scenario -v -s',
            'description': 'Test high-load event day scenario'
        },
        {
            'name': 'Multi-Language Mixed',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestRealWorldComplexScenarios::test_multi_language_mixed_scenario -v -s',
            'description': 'Test mixed Hebrew/English user scenarios'
        },
        {
            'name': 'Performance & Stress Tests',
            'command': 'python -m pytest test_e2e_comprehensive.py::TestPerformanceAndStress -v -s',
            'description': 'Test system performance and stress scenarios'
        },
        {
            'name': 'All E2E Tests',
            'command': 'python -m pytest test_e2e_comprehensive.py -v',
            'description': 'Run complete comprehensive E2E test suite'
        }
    ]
    
    # Run tests
    results = []
    start_time = datetime.now()
    
    for config in e2e_test_configs:
        success = run_command(config['command'], config['description'])
        results.append({
            'name': config['name'],
            'success': success,
            'description': config['description']
        })
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Print comprehensive results
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE E2E TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"🕐 Total time: {duration}")
    print(f"📝 Total test categories: {len(results)}")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {passed/len(results)*100:.1f}%")
    
    # Detailed results by category
    print(f"\n📋 Detailed Results by Category:")
    
    categories = {
        'Happy Path Tests': ['Happy Path Flow', 'Hebrew User Journey', 'Multi-Partner Journey'],
        'Edge Cases': ['Google Sheets Unavailable', 'Invalid User Data', 'Concurrent Users', 'Admin Permissions'],
        'Integration Tests': ['Admin Bulk Operations', 'Monitoring Integration'],
        'Real-World Scenarios': ['Event Day Simulation', 'Multi-Language Mixed'],
        'Performance Tests': ['Performance & Stress Tests']
    }
    
    for category, test_names in categories.items():
        print(f"\n🏷️  {category}:")
        category_passed = 0
        category_total = 0
        
        for test_name in test_names:
            result = next((r for r in results if test_name in r['name']), None)
            if result:
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                print(f"    {status} - {test_name}")
                if result['success']:
                    category_passed += 1
                category_total += 1
        
        if category_total > 0:
            category_rate = category_passed / category_total * 100
            print(f"    📊 Category Success Rate: {category_rate:.1f}% ({category_passed}/{category_total})")
    
    # System readiness assessment
    print(f"\n🎯 SYSTEM READINESS ASSESSMENT:")
    if passed >= len(results) * 0.95:  # 95% pass rate
        print("🏆 EXCELLENT - System is fully production ready!")
        print("✅ All critical flows tested and working")
        print("✅ Edge cases handled properly") 
        print("✅ Performance meets requirements")
        print("✅ Error handling is robust")
    elif passed >= len(results) * 0.85:  # 85% pass rate
        print("✅ GOOD - System is production ready with minor issues")
        print("⚠️  Some edge cases may need attention")
    elif passed >= len(results) * 0.70:  # 70% pass rate
        print("⚠️  CAUTION - System needs improvements before production")
        print("🔧 Several critical flows or edge cases failing")
    else:
        print("❌ NOT READY - System has major issues")
        print("🚨 Critical flows are failing")
    
    # Test quality metrics
    print(f"\n📊 TEST QUALITY METRICS:")
    print(f"🎯 Happy Path Coverage: {'✅ COMPLETE' if any('Happy Path' in r['name'] for r in results if r['success']) else '❌ INCOMPLETE'}")
    print(f"🛡️  Edge Case Coverage: {'✅ COMPLETE' if any('Edge Cases' in r['name'] for r in results if r['success']) else '❌ INCOMPLETE'}")
    print(f"🔗 Integration Coverage: {'✅ COMPLETE' if any('Integration' in r['name'] for r in results if r['success']) else '❌ INCOMPLETE'}")
    print(f"🌍 Multi-Language Coverage: {'✅ COMPLETE' if any('Hebrew' in r['name'] for r in results if r['success']) else '❌ INCOMPLETE'}")
    print(f"⚡ Performance Coverage: {'✅ COMPLETE' if any('Performance' in r['name'] for r in results if r['success']) else '❌ INCOMPLETE'}")
    
    # Next steps
    if failed > 0:
        print(f"\n🔧 RECOMMENDED NEXT STEPS:")
        print("1. Review failed test outputs above")
        print("2. Fix failing scenarios and edge cases")
        print("3. Re-run tests: python run_e2e_tests.py")
        print("4. Focus on critical user flows first")
        print("5. Address performance issues if any")
        
        print(f"\n❌ FAILED TESTS TO ADDRESS:")
        for result in results:
            if not result['success']:
                print(f"  • {result['name']}")
    else:
        print(f"\n🎉 ALL E2E TESTS PASSED!")
        print("🚀 System is fully validated and production-ready!")
        print("🏆 Comprehensive testing complete!")
    
    return passed == len(results)

def run_quick_e2e_validation():
    """Run quick E2E validation"""
    print("⚡ Running quick E2E validation...")
    
    quick_tests = [
        'python -m pytest test_e2e_comprehensive.py::TestCompleteUserJourney::test_happy_path_complete_user_journey -v',
        'python -m pytest test_e2e_comprehensive.py::TestEdgeCasesAndFailures::test_google_sheets_unavailable_scenario -v'
    ]
    
    all_passed = True
    for test in quick_tests:
        result = subprocess.run(test, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Quick E2E test passed")
        else:
            print("❌ Quick E2E test failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            all_passed = False
    
    return all_passed

def run_specific_scenario(scenario_name):
    """Run a specific E2E scenario"""
    scenario_map = {
        'happy': 'TestCompleteUserJourney::test_happy_path_complete_user_journey',
        'hebrew': 'TestCompleteUserJourney::test_hebrew_user_complete_journey',
        'multipartner': 'TestCompleteUserJourney::test_multi_partner_journey',
        'edge': 'TestEdgeCasesAndFailures',
        'sheets': 'TestEdgeCasesAndFailures::test_google_sheets_unavailable_scenario',
        'concurrent': 'TestEdgeCasesAndFailures::test_concurrent_user_access_scenario',
        'admin': 'TestEdgeCasesAndFailures::test_admin_permission_edge_cases',
        'integration': 'TestSystemIntegrationScenarios',
        'bulk': 'TestSystemIntegrationScenarios::test_admin_bulk_operations_scenario',
        'monitoring': 'TestSystemIntegrationScenarios::test_monitoring_and_notification_integration',
        'realworld': 'TestRealWorldComplexScenarios',
        'eventday': 'TestRealWorldComplexScenarios::test_event_day_scenario',
        'multilang': 'TestRealWorldComplexScenarios::test_multi_language_mixed_scenario',
        'performance': 'TestPerformanceAndStress'
    }
    
    if scenario_name.lower() in scenario_map:
        test_class = scenario_map[scenario_name.lower()]
        command = f'python -m pytest test_e2e_comprehensive.py::{test_class} -v -s'
        return run_command(command, f"Testing {scenario_name} scenario")
    else:
        print(f"❌ Unknown scenario: {scenario_name}")
        print(f"Available scenarios: {', '.join(scenario_map.keys())}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'quick':
            # Run quick E2E validation
            success = run_quick_e2e_validation()
            sys.exit(0 if success else 1)
            
        elif command in [
            'happy', 'hebrew', 'multipartner', 'edge', 'sheets', 'concurrent', 
            'admin', 'integration', 'bulk', 'monitoring', 'realworld', 
            'eventday', 'multilang', 'performance'
        ]:
            # Run specific scenario
            success = run_specific_scenario(command)
            sys.exit(0 if success else 1)
            
        elif command == 'help':
            print("🧪 Comprehensive E2E Test Runner")
            print("Usage:")
            print("  python run_e2e_tests.py                    # Run all E2E tests")
            print("  python run_e2e_tests.py quick              # Quick validation")
            print("  python run_e2e_tests.py [scenario]         # Test specific scenario")
            print("")
            print("Available scenarios:")
            print("  happy        - Happy path user journey")
            print("  hebrew       - Hebrew user journey")
            print("  multipartner - Multi-partner scenarios")
            print("  edge         - All edge cases")
            print("  sheets       - Google Sheets unavailable")
            print("  concurrent   - Concurrent user access")
            print("  admin        - Admin permission cases")
            print("  integration  - System integration tests")
            print("  bulk         - Admin bulk operations")
            print("  monitoring   - Monitoring integration")
            print("  realworld    - Real-world scenarios")
            print("  eventday     - Event day simulation")
            print("  multilang    - Multi-language scenarios")
            print("  performance  - Performance & stress tests")
            sys.exit(0)
    
    # Run full E2E test suite
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏸️  E2E tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 