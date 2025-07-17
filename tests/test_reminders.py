#!/usr/bin/env python3
"""
Test script for the reminder system
Tests both manual and automatic reminder functionality
"""

import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot_polling import (
    ReminderScheduler, 
    send_partner_reminder, 
    log_reminder_sent
)

async def test_manual_reminder():
    """Test manual partner reminder sending"""
    print("🧪 Testing manual reminder system...")
    
    # Test sending a reminder
    result = await send_partner_reminder(
        partner_name="TestPartner",
        requester_name="TestUser",
        language="en"
    )
    
    print(f"✅ Manual reminder test: {'PASSED' if result else 'FAILED'}")
    return result

async def test_reminder_logging():
    """Test reminder logging functionality"""
    print("🧪 Testing reminder logging...")
    
    # Test logging a reminder
    result = await log_reminder_sent(
        submission_id="TEST_123",
        partner_name="TestPartner",
        reminder_type="test_reminder"
    )
    
    print(f"✅ Logging test: {'PASSED' if result else 'FAILED'}")
    return result

async def test_reminder_scheduler():
    """Test the automatic reminder scheduler"""
    print("🧪 Testing reminder scheduler...")
    
    # Mock bot application
    mock_app = Mock()
    mock_app.bot = AsyncMock()
    mock_app.bot.send_message = AsyncMock()
    
    # Create scheduler
    scheduler = ReminderScheduler(mock_app)
    
    # Test reminder intervals
    expected_intervals = {
        'partner_pending': 24 * 60 * 60,  # 24 hours
        'payment_pending': 3 * 24 * 60 * 60,  # 3 days
        'group_opening': 7 * 24 * 60 * 60,  # 7 days
        'event_reminder': 24 * 60 * 60,  # 1 day
    }
    
    intervals_correct = scheduler.reminder_intervals == expected_intervals
    print(f"✅ Scheduler intervals: {'PASSED' if intervals_correct else 'FAILED'}")
    
    # Test user data processing
    test_user_data = {
        'submission_id': 'TEST_123',
        'telegram_user_id': '12345',
        'language': 'en',
        'partner_status': {
            'missing_partners': ['TestPartner1', 'TestPartner2']
        },
        'approved': True,
        'paid': False,
        'group_open': False
    }
    
    try:
        await scheduler.check_user_reminders(test_user_data)
        print("✅ User reminder check: PASSED")
        scheduler_test_passed = True
    except Exception as e:
        print(f"❌ User reminder check: FAILED - {e}")
        scheduler_test_passed = False
    
    return intervals_correct and scheduler_test_passed

async def test_partner_reminder_messages():
    """Test partner reminder message generation"""
    print("🧪 Testing partner reminder messages...")
    
    # Mock bot application
    mock_app = Mock()
    mock_app.bot = AsyncMock()
    mock_app.bot.send_message = AsyncMock()
    
    scheduler = ReminderScheduler(mock_app)
    
    # Test single partner reminder
    test_user_data_single = {
        'submission_id': 'TEST_123',
        'telegram_user_id': '12345',
        'language': 'en',
        'partner_status': {
            'missing_partners': ['TestPartner']
        }
    }
    
    try:
        await scheduler.send_automatic_partner_reminder(
            test_user_data_single, 
            ['TestPartner']
        )
        print("✅ Single partner reminder: PASSED")
        single_test_passed = True
    except Exception as e:
        print(f"❌ Single partner reminder: FAILED - {e}")
        single_test_passed = False
    
    # Test multiple partners reminder
    test_user_data_multiple = {
        'submission_id': 'TEST_123',
        'telegram_user_id': '12345',
        'language': 'en',
        'partner_status': {
            'missing_partners': ['TestPartner1', 'TestPartner2']
        }
    }
    
    try:
        await scheduler.send_automatic_partner_reminder(
            test_user_data_multiple, 
            ['TestPartner1', 'TestPartner2']
        )
        print("✅ Multiple partners reminder: PASSED")
        multiple_test_passed = True
    except Exception as e:
        print(f"❌ Multiple partners reminder: FAILED - {e}")
        multiple_test_passed = False
    
    return single_test_passed and multiple_test_passed

async def test_payment_reminder():
    """Test payment reminder functionality"""
    print("🧪 Testing payment reminder...")
    
    # Mock bot application
    mock_app = Mock()
    mock_app.bot = AsyncMock()
    mock_app.bot.send_message = AsyncMock()
    
    scheduler = ReminderScheduler(mock_app)
    
    test_user_data = {
        'submission_id': 'TEST_123',
        'telegram_user_id': '12345',
        'language': 'en',
        'approved': True,
        'paid': False
    }
    
    try:
        await scheduler.send_automatic_payment_reminder(test_user_data)
        print("✅ Payment reminder: PASSED")
        return True
    except Exception as e:
        print(f"❌ Payment reminder: FAILED - {e}")
        return False

async def test_group_reminder():
    """Test group opening reminder functionality"""
    print("🧪 Testing group reminder...")
    
    # Mock bot application
    mock_app = Mock()
    mock_app.bot = AsyncMock()
    mock_app.bot.send_message = AsyncMock()
    
    scheduler = ReminderScheduler(mock_app)
    
    test_user_data = {
        'submission_id': 'TEST_123',
        'telegram_user_id': '12345',
        'language': 'en',
        'paid': True,
        'group_open': False
    }
    
    try:
        await scheduler.send_automatic_group_reminder(test_user_data)
        print("✅ Group reminder: PASSED")
        return True
    except Exception as e:
        print(f"❌ Group reminder: FAILED - {e}")
        return False

async def run_all_tests():
    """Run all reminder system tests"""
    print("🚀 Starting reminder system tests...\n")
    
    tests = [
        test_manual_reminder,
        test_reminder_logging,
        test_reminder_scheduler,
        test_partner_reminder_messages,
        test_payment_reminder,
        test_group_reminder
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Reminder system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == '__main__':
    print("📱 Wild Ginger Bot - Reminder System Tests")
    print("=" * 50)
    
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        exit(1) 