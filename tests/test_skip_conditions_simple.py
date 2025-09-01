#!/usr/bin/env python3
"""
Simple test script for skip conditions
Run this script to verify that skip conditions are working correctly
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from telegram_bot.config.form_config import FormConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def test_skip_conditions():
    """Test skip conditions for form questions"""
    print("🧪 Testing Skip Conditions for Form Questions")
    print("=" * 50)
    
    # Create instances
    try:
        form_config = FormConfig()
        question_definitions = form_config.get_question_definitions()
        print("✅ Successfully created form config instance")
    except Exception as e:
        print(f"❌ Failed to create form config instance: {e}")
        return False
    
    # Test counters
    passed_tests = 0
    total_tests = 0
    
    # Test 1: BDSM questions should be hidden for cuddle events
    print("\n📋 Test 1: BDSM Questions Hidden for Cuddle Events")
    print("-" * 40)
    
    bdsm_questions = [
        'bdsm_experience',
        'bdsm_declaration', 
        'share_bdsm_interests',
        'limits_preferences_matrix',
        'boundaries_text',
        'preferences_text',
        'bdsm_comments',
        'contact_type',
        'contact_type_other'
    ]
    
    for question_id in bdsm_questions:
        total_tests += 1
        try:
            # Check form config
            question_def = question_definitions.get(question_id)
            if not question_def:
                print(f"  ❌ {question_id} - Question not found in form config")
                continue
                
            if not question_def.skip_condition:
                print(f"  ❌ {question_id} - No skip condition in form config")
                continue
            
            # Check for cuddle skip condition in config
            has_cuddle_skip = False
            for condition in question_def.skip_condition.conditions:
                if (condition.type == "event_type" and 
                    condition.value == "cuddle" and 
                    condition.operator == "equals"):
                    has_cuddle_skip = True
                    break
            
            if not has_cuddle_skip:
                print(f"  ❌ {question_id} - Missing cuddle skip condition in form config")
                continue
            
            print(f"  ✅ {question_id} - Skip condition for cuddle events")
            passed_tests += 1
            
        except Exception as e:
            print(f"  ❌ {question_id} - Error: {e}")
    
    # Test 2: Food comments should be skipped when no food restrictions
    print("\n🍽️ Test 2: Food Comments Skipped for No Restrictions")
    print("-" * 40)
    
    total_tests += 1
    try:
        # Check form config
        question_def = question_definitions.get('food_comments')
        if not question_def:
            print("  ❌ food_comments - Question not found in form config")
        elif not question_def.skip_condition:
            print("  ❌ food_comments - No skip condition in form config")
        else:
            # Check for food restrictions skip condition in config
            has_food_skip = False
            for condition in question_def.skip_condition.conditions:
                if (condition.type == "field_value" and 
                    condition.field == "food_restrictions" and 
                    condition.value == "no" and 
                    condition.operator == "equals"):
                    has_food_skip = True
                    break
            
            if not has_food_skip:
                print("  ❌ food_comments - Missing food_restrictions skip condition in form config")
            else:
                print("  ✅ food_comments - Skip condition for food_restrictions = 'no'")
                passed_tests += 1
                        
    except Exception as e:
        print(f"  ❌ food_comments - Error: {e}")
    
    # Test 3: Boundaries should be skipped when not sharing BDSM interests
    print("\n🔒 Test 3: Boundaries Skipped for No BDSM Interests")
    print("-" * 40)
    
    boundary_questions = ['boundaries_text', 'preferences_text']
    
    for question_id in boundary_questions:
        total_tests += 1
        try:
            # Check form config
            question_def = question_definitions.get(question_id)
            if not question_def:
                print(f"  ❌ {question_id} - Question not found in form config")
                continue
                
            if not question_def.skip_condition:
                print(f"  ❌ {question_id} - No skip condition in form config")
                continue
            
            # Check for share_bdsm_interests skip condition in config
            has_bdsm_skip = False
            for condition in question_def.skip_condition.conditions:
                if (condition.type == "field_value" and 
                    condition.field == "share_bdsm_interests" and 
                    condition.value == "no" and 
                    condition.operator == "equals"):
                    has_bdsm_skip = True
                    break
            
            if not has_bdsm_skip:
                print(f"  ❌ {question_id} - Missing share_bdsm_interests skip condition in form config")
                continue
            
            print(f"  ✅ {question_id} - Skip condition for share_bdsm_interests = 'no'")
            passed_tests += 1
            
        except Exception as e:
            print(f"  ❌ {question_id} - Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All skip condition tests passed!")
        print("✅ BDSM questions will be hidden for cuddle events")
        print("✅ Food comments will be skipped when no restrictions")
        print("✅ Boundaries will be skipped when not sharing BDSM interests")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed")
        print("Please check the implementation and fix the issues")
        return False


if __name__ == "__main__":
    success = test_skip_conditions()
    sys.exit(0 if success else 1) 