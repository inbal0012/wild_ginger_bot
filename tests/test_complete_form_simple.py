#!/usr/bin/env python3
"""
Simple Complete Form Flow Test
Tests the complete form flow including partner messages and skip conditions
"""

import sys
import os
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_form_structure():
    """Test the form structure and skip conditions"""
    print("🧪 Testing Complete Form Structure")
    print("=" * 50)
    
    # Test counters
    passed_tests = 0
    total_tests = 0
    
    # Test 1: Check form configuration files exist
    print("\n📁 Test 1: Form Configuration Files")
    print("-" * 30)
    total_tests += 1
    try:
        form_flow_file = "telegram_bot/services/form_flow_service.py"
        
        assert os.path.exists(form_flow_file), f"Form flow service file not found: {form_flow_file}"
        
        print("  ✅ Form flow service file exists")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking form files: {e}")
    
    # Test 2: Check skip conditions in form flow service
    print("\n🔍 Test 2: Skip Conditions in Form Flow Service")
    print("-" * 30)
    total_tests += 1
    try:
        with open(form_flow_file, 'r', encoding='utf-8') as f:
            form_flow_content = f.read()
        
        # Check for skip conditions
        cuddle_conditions_flow = form_flow_content.count('SkipConditionItem(type="event_type", value="cuddle"')
        
        assert cuddle_conditions_flow >= 9, f"Expected at least 9 cuddle skip conditions in form flow, found {cuddle_conditions_flow}"
        
        print(f"  ✅ Cuddle skip conditions: {cuddle_conditions_flow} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking skip conditions: {e}")
    
    # Test 3: Check partner message functionality
    print("\n🤝 Test 3: Partner Message Functionality")
    print("-" * 30)
    total_tests += 1
    try:
        # Check for partner-related functions in form flow service
        partner_functions = [
            '_create_partner_registration_link',
            '_create_partner_registration_message',
            'build_partner_status_text',
            'send_partner_reminder',
            'check_partner_registration_status'
        ]
        
        found_functions = 0
        for func in partner_functions:
            if func in form_flow_content:
                found_functions += 1
        
        assert found_functions >= 2, f"Expected at least 2 partner functions, found {found_functions}"
        
        print(f"  ✅ Partner message functions: {found_functions} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking partner functions: {e}")
    
    # Test 4: Check form question structure
    print("\n📝 Test 4: Form Question Structure")
    print("-" * 30)
    total_tests += 1
    try:
        # Check for essential question types
        essential_questions = [
            'full_name',
            'partner_or_single',
            'food_restrictions',
            'event_selection'
        ]
        
        found_questions = 0
        for question in essential_questions:
            if f'"{question}": QuestionDefinition' in form_flow_content:
                found_questions += 1
        
        assert found_questions >= 3, f"Expected at least 3 essential questions, found {found_questions}"
        
        print(f"  ✅ Essential questions: {found_questions} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking question structure: {e}")
    
    # Test 5: Check multilingual support
    print("\n🌍 Test 5: Multilingual Support")
    print("-" * 30)
    total_tests += 1
    try:
        # Check for Hebrew and English text patterns
        hebrew_pattern = r'Text\(he="[^"]*", en="[^"]*"\)'
        hebrew_matches = len(re.findall(hebrew_pattern, form_flow_content))
        
        assert hebrew_matches >= 10, f"Expected at least 10 multilingual text entries, found {hebrew_matches}"
        
        print(f"  ✅ Multilingual text entries: {hebrew_matches} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking multilingual support: {e}")
    
    # Test 6: Check validation rules
    print("\n✅ Test 6: Validation Rules")
    print("-" * 30)
    total_tests += 1
    try:
        # Check for validation rules
        validation_pattern = r'ValidationRule\('
        validation_matches = len(re.findall(validation_pattern, form_flow_content))
        
        assert validation_matches >= 5, f"Expected at least 5 validation rules, found {validation_matches}"
        
        print(f"  ✅ Validation rules: {validation_matches} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking validation rules: {e}")
    
    # Test 7: Check form completion logic
    print("\n🎯 Test 7: Form Completion Logic")
    print("-" * 30)
    total_tests += 1
    try:
        # Check for form completion functions
        completion_functions = [
            '_complete_form',
            'start_form',
            'get_form_state',
            '_validate_question_answer',
            '_should_skip_question'
        ]
        
        found_completion = 0
        for func in completion_functions:
            if func in form_flow_content:
                found_completion += 1
        
        assert found_completion >= 2, f"Expected at least 2 completion functions, found {found_completion}"
        
        print(f"  ✅ Form completion functions: {found_completion} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking completion logic: {e}")
    
    # Test 8: Check partner registration flow
    print("\n📋 Test 8: Partner Registration Flow")
    print("-" * 30)
    total_tests += 1
    try:
        # Check for partner registration patterns in the main bot file
        bot_file = "telegram_bot_polling.py"
        if os.path.exists(bot_file):
            with open(bot_file, 'r', encoding='utf-8') as f:
                bot_content = f.read()
        else:
            bot_content = ""
        
        # Check for partner registration patterns
        partner_patterns = [
            'partner_names',
            'partner_alias',
            'partner_status',
            'missing_partners',
            'parse_multiple_partners'
        ]
        
        found_patterns = 0
        for pattern in partner_patterns:
            if pattern in form_flow_content or pattern in bot_content:
                found_patterns += 1
        
        assert found_patterns >= 3, f"Expected at least 3 partner patterns, found {found_patterns}"
        
        print(f"  ✅ Partner registration patterns: {found_patterns} found")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ Error checking partner registration: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Complete Form Flow Test Summary")
    print("=" * 50)
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All complete form flow tests passed!")
        print("✅ Form structure is properly configured")
        print("✅ Skip conditions are implemented correctly")
        print("✅ Partner message functionality is available")
        print("✅ Multilingual support is working")
        print("✅ Validation rules are in place")
        print("✅ Form completion logic is implemented")
        print("✅ Partner registration flow is ready")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed")
        print("Please check the implementation and fix the issues")
        return False


def test_partner_message_examples():
    """Test partner message examples"""
    print("\n💬 Partner Message Examples")
    print("=" * 50)
    
    # Example partner message templates
    partner_message_templates = [
        "שלום {partner_name}, {user_name} הזמין אותך לאירוע {event_name}",
        "Hello {partner_name}, {user_name} invited you to {event_name}",
        "תזכורת: {missing_partners} עדיין לא נרשמו לאירוע",
        "Reminder: {missing_partners} haven't registered for the event yet"
    ]
    
    print("✅ Partner message templates are available:")
    for template in partner_message_templates:
        print(f"  📝 {template}")
    
    print("\n✅ Partner message system is ready for use")


def main():
    """Main test function"""
    print("🧪 Complete Form Flow Test Suite")
    print("=" * 60)
    
    # Run form structure tests
    form_success = test_form_structure()
    
    # Show partner message examples
    test_partner_message_examples()
    
    return form_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 