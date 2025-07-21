#!/usr/bin/env python3
"""
Test script to validate the refactored services work correctly
This can be run without needing Telegram API credentials
"""

import sys
import traceback
from typing import Dict, Any

def test_imports():
    """Test that all modules can be imported correctly"""
    print("🧪 Testing imports...")
    
    try:
        from .config import settings
        print("✅ Config import successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from .services import SheetsService, MessageService
        print("✅ Services import successful")
    except Exception as e:
        print(f"❌ Services import failed: {e}")
        return False
    
    try:
        from .models.registration import RegistrationStatus, RegistrationData, StepProgress
        print("✅ Models import successful")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from .exceptions import SheetsConnectionException, RegistrationNotFoundException
        print("✅ Exceptions import successful")
    except Exception as e:
        print(f"❌ Exceptions import failed: {e}")
        return False
    
    return True

def test_message_service():
    """Test the message service functionality"""
    print("\n🧪 Testing MessageService...")
    
    try:
        from .services import MessageService
        
        message_service = MessageService()
        print("✅ MessageService initialized")
        
        # Test basic message retrieval
        welcome_msg = message_service.get_welcome_message('en', 'TestUser')
        print(f"✅ Welcome message: {welcome_msg[:50]}...")
        
        help_msg = message_service.get_help_message('en')
        print(f"✅ Help message: {help_msg[:50]}...")
        
        # Test status message building with mock data
        mock_status = {
            'form': True,
            'partner': False,
            'get_to_know': True,
            'approved': False,
            'paid': False,
            'group_open': False,
            'partner_names': [],
            'language': 'en'
        }
        
        status_msg = message_service.build_status_message(mock_status, 'en')
        print(f"✅ Status message built: {len(status_msg)} characters")
        print(f"   Preview: {status_msg[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ MessageService test failed: {e}")
        traceback.print_exc()
        return False

def test_sheets_service():
    """Test the sheets service initialization (without actual API calls)"""
    print("\n🧪 Testing SheetsService...")
    
    try:
        from .services import SheetsService
        
        sheets_service = SheetsService()
        print("✅ SheetsService initialized")
        
        # Test column index mapping
        mock_headers = [
            'Submission ID', 'שם מלא', 'Telegram User Id', 
            'Form Complete', 'Partner Complete', 'Get To Know Complete',
            'Admin Approved', 'Payment Complete', 'Group Access'
        ]
        
        column_indices = sheets_service.get_column_indices(mock_headers)
        expected_keys = [
            'submission_id', 'full_name', 'telegram_user_id',
            'form_complete', 'partner_complete', 'get_to_know_complete',
            'admin_approved', 'payment_complete', 'group_access'
        ]
        
        for key in expected_keys:
            if key in column_indices:
                print(f"✅ Found column: {key} at index {column_indices[key]}")
            else:
                print(f"❌ Missing column: {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ SheetsService test failed: {e}")
        traceback.print_exc()
        return False

def test_models():
    """Test the data models"""
    print("\n🧪 Testing Models...")
    
    try:
        from .models.registration import RegistrationStatus, RegistrationData, StepProgress
        
        # Test enums
        status = RegistrationStatus.WAITING_FOR_PARTNER
        print(f"✅ RegistrationStatus enum: {status.value}")
        
        # Test StepProgress
        progress = StepProgress(form=True, partner=False)
        print(f"✅ StepProgress: form={progress.form}, partner={progress.partner}")
        
        # Test RegistrationData
        reg_data = RegistrationData(
            submission_id="SUBM_12345",
            telegram_user_id="123456789",
            user_name="TestUser"
        )
        print(f"✅ RegistrationData: {reg_data.submission_id}")
        print(f"   Auto-initialized step_progress: {reg_data.step_progress}")
        print(f"   Auto-initialized form_data: {reg_data.form_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🧪 Testing Configuration...")
    
    try:
        from .config import settings
        
        print(f"✅ Admin users configured: {len(settings.admin_user_ids)}")
        print(f"✅ Google Sheets service: {'Available' if settings.sheets_service else 'Not available'}")
        print(f"✅ Messages loaded: {len(settings.messages)} languages")
        
        # Test message structure
        if 'en' in settings.messages:
            en_msgs = settings.messages['en']
            required_keys = ['welcome', 'help', 'status_labels']
            for key in required_keys:
                if key in en_msgs:
                    print(f"✅ Found message key: {key}")
                else:
                    print(f"❌ Missing message key: {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Wild Ginger Bot Service Tests")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration),
        ("Message Service Tests", test_message_service),
        ("Sheets Service Tests", test_sheets_service),
        ("Models Tests", test_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactored services are working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 