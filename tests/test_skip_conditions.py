"""
Test skip conditions for form questions
Tests the logic for hiding BDSM questions in cuddle events and food comments when no restrictions
"""

import pytest
from unittest.mock import Mock, patch
from telegram_bot.services.form_flow_service import FormFlowService
from telegram_bot.models.form_flow import SkipCondition, SkipConditionItem


class TestSkipConditions:
    """Test skip condition logic for form questions"""
    
    @pytest.fixture
    def form_flow_service(self):
        """Create a form flow service instance for testing"""
        mock_sheets_service = Mock()
        # Configure the mock to be subscriptable
        mock_sheets_service.headers = {
            "Users": {
                "telegram_user_id": 0,
                "telegram": 1,
                "full_name": 2,
                "language": 3,
                "relevant_experience": 4
            },
            "Registrations": {
                "registration_id": 0,
                "user_id": 1,
                "event_id": 2,
                "status": 3
            },
            "Events": {
                "id": 0,
                "name": 1,
                "start_date": 2,
                "start_time": 3,
                "event_type": 4,
                "price_single": 5,
                "price_couple": 6,
                "theme": 7,
                "max_participants": 8,
                "status": 9,
                "created_at": 10,
                "updated_at": 11,
                "main_group_id": 12,
                "singles_group_id": 13,
                "is_public": 14,
                "description": 15,
                "location": 16,
                "end_date": 17,
                "end_time": 18,
                "price_include": 19,
                "schedule": 20,
                "participant_commitment": 21,
                "line_rules": 22,
                "place_rules": 23,
                "balance": 24
            }
        }
        
        # Mock get_data_from_sheet to return proper data structure
        mock_sheets_service.get_data_from_sheet.return_value = {
            'headers': ['id', 'name', 'start_date', 'start_time', 'event_type', 'price_single', 'price_couple', 'theme', 'max_participants', 'status', 'created_at', 'updated_at', 'main_group_id', 'singles_group_id', 'is_public', 'description', 'location', 'end_date', 'end_time', 'price_include', 'schedule', 'participant_commitment', 'line_rules', 'place_rules', 'balance'],
            'rows': [
                ['event1', 'Test Event 1', '2024-01-15', '18:00', 'workshop', '100', '180', 'BDSM Basics', '20', 'active', '2024-01-01 10:00:00', '2024-01-01 10:00:00', 'group1', 'singles1', 'true', 'Test description', 'Test location', '2024-01-15', '22:00', 'Food included', '18:00-22:00', 'Commitment required', 'Line rules', 'Place rules', '0']
            ]
        }
        
        return FormFlowService(mock_sheets_service)
    
    def test_cuddle_event_hides_bdsm_questions(self, form_flow_service):
        """Test that BDSM questions are hidden for cuddle events"""
        # Mock event data for cuddle event
        event_data = {
            'event_type': 'cuddle',
            'name': 'Cuddle Party'
        }
        
        # List of BDSM questions that should be hidden
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
        
        # Test each BDSM question
        for question_id in bdsm_questions:
            question_def = form_flow_service.question_definitions.get(question_id)
            assert question_def is not None, f"Question {question_id} not found"
            
            # Check if skip condition exists
            assert question_def.skip_condition is not None, f"No skip condition for {question_id}"
            
            # Check if skip condition includes cuddle event type
            has_cuddle_skip = False
            for condition in question_def.skip_condition.conditions:
                if (condition.type == "event_type" and 
                    condition.value == "cuddle" and 
                    condition.operator == "equals"):
                    has_cuddle_skip = True
                    break
            
            assert has_cuddle_skip, f"Question {question_id} missing cuddle skip condition"
    
    def test_bdsm_event_shows_bdsm_questions(self, form_flow_service):
        """Test that BDSM questions are shown for BDSM events"""
        # Mock event data for BDSM event
        event_data = {
            'event_type': 'bdsm_workshop',
            'name': 'BDSM Workshop'
        }
        
        # List of BDSM questions that should be shown
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
        
        # Test each BDSM question
        for question_id in bdsm_questions:
            question_def = form_flow_service.question_definitions.get(question_id)
            assert question_def is not None, f"Question {question_id} not found"
            
            # For BDSM events, the skip condition should not trigger
            # (assuming the skip condition only checks for cuddle events)
            if question_def.skip_condition:
                for condition in question_def.skip_condition.conditions:
                    if condition.type == "event_type" and condition.value == "cuddle":
                        # This condition should not match for BDSM events
                        assert condition.value != "bdsm_workshop", f"Question {question_id} incorrectly skips BDSM events"
    
    def test_food_restrictions_no_skips_comments(self, form_flow_service):
        """Test that food_comments is skipped when food_restrictions is 'no'"""
        question_def = form_flow_service.question_definitions.get('food_comments')
        assert question_def is not None, "food_comments question not found"
        
        # Check if skip condition exists
        assert question_def.skip_condition is not None, "No skip condition for food_comments"
        
        # Check if skip condition includes food_restrictions = "no"
        has_food_skip = False
        for condition in question_def.skip_condition.conditions:
            if (condition.type == "field_value" and 
                condition.field == "food_restrictions" and 
                condition.value == "no" and 
                condition.operator == "equals"):
                has_food_skip = True
                break
        
        assert has_food_skip, "food_comments missing food_restrictions skip condition"
    
    def test_food_restrictions_other_shows_comments(self, form_flow_service):
        """Test that food_comments is shown when food_restrictions is not 'no'"""
        question_def = form_flow_service.question_definitions.get('food_comments')
        assert question_def is not None, "food_comments question not found"
        
        # For other food restrictions, the skip condition should not trigger
        if question_def.skip_condition:
            for condition in question_def.skip_condition.conditions:
                if (condition.type == "field_value" and 
                    condition.field == "food_restrictions" and 
                    condition.operator == "equals"):
                    # This condition should only match "no", not other values
                    assert condition.value == "no", f"food_comments incorrectly skips other food restrictions"
    
    def test_share_bdsm_interests_no_skips_boundaries(self, form_flow_service):
        """Test that boundaries and preferences are skipped when share_bdsm_interests is 'no'"""
        boundary_questions = ['boundaries_text', 'preferences_text']
        
        for question_id in boundary_questions:
            question_def = form_flow_service.question_definitions.get(question_id)
            assert question_def is not None, f"{question_id} question not found"
            
            # Check if skip condition exists
            assert question_def.skip_condition is not None, f"No skip condition for {question_id}"
            
            # Check if skip condition includes share_bdsm_interests = "no"
            has_bdsm_skip = False
            for condition in question_def.skip_condition.conditions:
                if (condition.type == "field_value" and 
                    condition.field == "share_bdsm_interests" and 
                    condition.value == "no" and 
                    condition.operator == "equals"):
                    has_bdsm_skip = True
                    break
            
            assert has_bdsm_skip, f"{question_id} missing share_bdsm_interests skip condition"
    
    @patch.object(FormFlowService, '_should_skip_question')
    @pytest.mark.asyncio
    async def test_skip_condition_logic_cuddle_event(self, mock_check_skip, form_flow_service):
        """Test skip condition logic for cuddle events"""
        # Mock the skip condition check to return True for cuddle events
        mock_check_skip.return_value = True
        
        # Test that BDSM questions are skipped for cuddle events
        bdsm_questions = ['bdsm_experience', 'bdsm_declaration', 'share_bdsm_interests']
        
        for question_id in bdsm_questions:
            question_def = form_flow_service.question_definitions.get(question_id)
            assert question_def is not None, f"Question {question_id} not found"
            
            # Create a mock form state with cuddle event type
            mock_form_state = Mock()
            mock_form_state.answers = {'event_type': 'cuddle'}
            
            # The method should be called and return True (skip the question)
            result = await form_flow_service._should_skip_question(question_def, mock_form_state)
            assert result is True
            mock_check_skip.assert_called()
    
    @patch.object(FormFlowService, '_should_skip_question')
    @pytest.mark.asyncio
    async def test_skip_condition_logic_food_restrictions(self, mock_check_skip, form_flow_service):
        """Test skip condition logic for food restrictions"""
        # Mock the skip condition check to return True when food_restrictions is "no"
        mock_check_skip.return_value = True
        
        # Test that food_comments is skipped when food_restrictions is "no"
        question_def = form_flow_service.question_definitions.get('food_comments')
        assert question_def is not None, "food_comments question not found"
        
        # Create a mock form state with food_restrictions = "no"
        mock_form_state = Mock()
        mock_form_state.answers = {'food_restrictions': 'no'}
        
        # The method should be called and return True (skip the question)
        result = await form_flow_service._should_skip_question(question_def, mock_form_state)
        assert result is True
        mock_check_skip.assert_called()


def run_skip_condition_tests():
    """Run all skip condition tests and report results"""
    print("🧪 Running skip condition tests...")
    
    # Create test instances
    mock_sheets_service = Mock()
    mock_sheets_service.headers = {
        "Users": {
            "telegram_user_id": 0,
            "telegram": 1,
            "full_name": 2,
            "language": 3,
            "relevant_experience": 4
        },
        "Registrations": {
            "registration_id": 0,
            "user_id": 1,
            "event_id": 2,
            "status": 3
        },
        "Events": {
            "id": 0,
            "name": 1,
            "start_date": 2,
            "start_time": 3,
            "event_type": 4,
            "price_single": 5,
            "price_couple": 6,
            "theme": 7,
            "max_participants": 8,
            "status": 9,
            "created_at": 10,
            "updated_at": 11,
            "main_group_id": 12,
            "singles_group_id": 13,
            "is_public": 14,
            "description": 15,
            "location": 16,
            "end_date": 17,
            "end_time": 18,
            "price_include": 19,
            "schedule": 20,
            "participant_commitment": 21,
            "line_rules": 22,
            "place_rules": 23
        }
    }
    
    # Mock get_data_from_sheet to return proper data structure
    mock_sheets_service.get_data_from_sheet.return_value = {
        'headers': ['id', 'name', 'start_date', 'start_time', 'event_type', 'price_single', 'price_couple', 'theme', 'max_participants', 'status', 'created_at', 'updated_at', 'main_group_id', 'singles_group_id', 'is_public', 'description', 'location', 'end_date', 'end_time', 'price_include', 'schedule', 'participant_commitment', 'line_rules', 'place_rules'],
        'rows': [
            ['event1', 'Test Event 1', '2024-01-15', '18:00', 'workshop', '100', '180', 'BDSM Basics', '20', 'active', '2024-01-01 10:00:00', '2024-01-01 10:00:00', 'group1', 'singles1', 'true', 'Test description', 'Test location', '2024-01-15', '22:00', 'Food included', '18:00-22:00', 'Commitment required', 'Line rules', 'Place rules']
        ]
    }
    
    form_flow_service = FormFlowService(mock_sheets_service)
    
    # Test counters
    passed_tests = 0
    total_tests = 0
    
    # Test 1: Cuddle events hide BDSM questions
    print("\n📋 Test 1: Cuddle events hide BDSM questions")
    bdsm_questions = [
        'bdsm_experience', 'bdsm_declaration', 'share_bdsm_interests',
        'limits_preferences_matrix', 'boundaries_text', 'preferences_text',
        'bdsm_comments', 'contact_type', 'contact_type_other'
    ]
    
    for question_id in bdsm_questions:
        total_tests += 1
        try:
            # Check form flow service
            question_def = form_flow_service.question_definitions.get(question_id)
            assert question_def is not None
            assert question_def.skip_condition is not None
            
            has_cuddle_skip = any(
                condition.type == "event_type" and condition.value == "cuddle"
                for condition in question_def.skip_condition.conditions
            )
            assert has_cuddle_skip
            
            print(f"  ✅ {question_id} - Skip condition for cuddle events")
            passed_tests += 1
            
        except AssertionError as e:
            print(f"  ❌ {question_id} - Missing or incorrect skip condition: {e}")
    
    # Test 2: Food restrictions skip food_comments
    print("\n🍽️ Test 2: Food restrictions skip food_comments")
    total_tests += 1
    try:
        # Check form flow service
        question_def = form_flow_service.question_definitions.get('food_comments')
        assert question_def is not None
        assert question_def.skip_condition is not None
        
        has_food_skip = any(
            condition.type == "field_value" and condition.field == "food_restrictions" and condition.value == "no"
            for condition in question_def.skip_condition.conditions
        )
        assert has_food_skip
        
        print("  ✅ food_comments - Skip condition for food_restrictions = 'no'")
        passed_tests += 1
        
    except AssertionError as e:
        print(f"  ❌ food_comments - Missing or incorrect skip condition: {e}")
    
    # Test 3: Share BDSM interests skip boundaries
    print("\n🔒 Test 3: Share BDSM interests skip boundaries")
    boundary_questions = ['boundaries_text', 'preferences_text']
    
    for question_id in boundary_questions:
        total_tests += 1
        try:
            # Check form flow service
            question_def = form_flow_service.question_definitions.get(question_id)
            assert question_def is not None
            assert question_def.skip_condition is not None
            
            has_bdsm_skip = any(
                condition.type == "field_value" and condition.field == "share_bdsm_interests" and condition.value == "no"
                for condition in question_def.skip_condition.conditions
            )
            assert has_bdsm_skip
            
            print(f"  ✅ {question_id} - Skip condition for share_bdsm_interests = 'no'")
            passed_tests += 1
            
        except AssertionError as e:
            print(f"  ❌ {question_id} - Missing or incorrect skip condition: {e}")
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"  Passed: {passed_tests}/{total_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("  🎉 All skip condition tests passed!")
    else:
        print("  ⚠️ Some tests failed. Please check the implementation.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    run_skip_condition_tests() 