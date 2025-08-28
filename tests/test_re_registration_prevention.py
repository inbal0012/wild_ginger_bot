"""
Test re-registration prevention functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from telegram_bot.services.form_flow_service import FormFlowService, FormState
from telegram_bot.services.registration_service import RegistrationService


class TestReRegistrationPrevention:
    """Test re-registration prevention functionality."""
    
    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock sheets service."""
        mock = Mock()
        mock.headers = {"Users": {}, "Registrations": {}, "Events": {}, "Groups": {}}
        return mock
    
    @pytest.fixture
    def mock_registration_service(self):
        """Create a mock registration service."""
        mock = Mock(spec=RegistrationService)
        mock.is_user_registered_for_event = Mock(return_value=False)  # Default: not registered
        mock.get_user_registration_for_event = Mock(return_value=None)
        mock.create_new_registration = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def form_flow_service(self, mock_sheets_service, mock_registration_service):
        """Create a form flow service with mocked dependencies."""
        # Create a minimal question definition for testing
        from telegram_bot.models.form_flow import QuestionDefinition, QuestionType, Text, QuestionOption, ValidationRule, ValidationRuleType
        
        question_definitions = {
            "language": QuestionDefinition(
                question_id="language",
                question_type=QuestionType.SELECT,
                title=Text(he="שפה", en="Language"),
                required=True,
                save_to="Users",
                order=1,
                options=[
                    QuestionOption(value="he", text=Text(he="עברית", en="Hebrew")),
                    QuestionOption(value="en", text=Text(he="English", en="English"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="נדרש", en="Required")
                    )
                ]
            ),
            "event_selection": QuestionDefinition(
                question_id="event_selection",
                question_type=QuestionType.SELECT,
                title=Text(he="אירוע", en="Event"),
                required=True,
                save_to="Registrations",
                order=2,
                options=[
                    QuestionOption(value="event_001", text=Text(he="אירוע 1", en="Event 1")),
                    QuestionOption(value="event_002", text=Text(he="אירוע 2", en="Event 2"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="נדרש", en="Required")
                    )
                ]
            )
        }
        
        with patch.object(FormFlowService, '_initialize_question_definitions', return_value=question_definitions):
            service = FormFlowService(mock_sheets_service)
            service.registration_service = mock_registration_service
            service.question_definitions = question_definitions
            return service
    
    @pytest.fixture
    def sample_form_state(self):
        """Create a sample form state for testing."""
        form_state = FormState(user_id="12345", event_id="event_001", language="he")
        form_state.answers = {
            "language": "he",
            "event_selection": "event_001"
        }
        return form_state
    
    @pytest.mark.asyncio
    async def test_handle_register_start_already_registered(self, form_flow_service, mock_registration_service):
        """Test that handle_register_start prevents re-registration."""
        # Mock that user is already registered
        mock_registration_service.is_user_registered_for_event.return_value = True
        mock_registration_service.get_user_registration_for_event.return_value = {
            "registration_id": "REG_12345",
            "status": "approved"
        }
        
        result = await form_flow_service.handle_register_start("12345", "event_001", "he")
        
        # Verify the result indicates already registered
        assert result["error"] is True
        assert result["already_registered"] is True
        assert "אתה כבר רשום לאירוע זה" in result["message"]
        assert result["registration_id"] == "REG_12345"
        assert result["status"] == "approved"
    
    @pytest.mark.asyncio
    async def test_handle_register_start_not_registered(self, form_flow_service, mock_registration_service):
        """Test that handle_register_start allows registration for new users."""
        # Mock that user is not registered
        mock_registration_service.is_user_registered_for_event.return_value = False
        
        result = await form_flow_service.handle_register_start("12345", "event_001", "he")
        
        # Verify the result allows registration
        assert result is not None
        if isinstance(result, dict):
            assert "error" not in result or result["error"] is False
            assert "already_registered" not in result or result["already_registered"] is False
    
    @pytest.mark.asyncio
    async def test_save_event_selection_already_registered(self, form_flow_service, mock_registration_service, sample_form_state):
        """Test that save_event_selection_to_sheets prevents re-registration."""
        # Add form state to active forms
        form_flow_service.active_forms["12345"] = sample_form_state
        
        # Mock that user is already registered
        mock_registration_service.is_user_registered_for_event.return_value = True
        mock_registration_service.get_user_registration_for_event.return_value = {
            "registration_id": "REG_12345",
            "status": "pending"
        }
        
        result = await form_flow_service.save_event_selection_to_sheets("12345", "event_001")
        
        # Verify the result is False (failed)
        assert result is False
        
        # Verify error info was stored in form state
        error_info = sample_form_state.get_answer("event_selection_error")
        assert error_info is not None
        assert error_info["already_registered"] is True
        assert error_info["registration_id"] == "REG_12345"
        assert error_info["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_save_event_selection_not_registered(self, form_flow_service, mock_registration_service, sample_form_state):
        """Test that save_event_selection_to_sheets allows registration for new users."""
        # Add form state to active forms
        form_flow_service.active_forms["12345"] = sample_form_state
        
        # Mock that user is not registered
        mock_registration_service.is_user_registered_for_event.return_value = False
        mock_registration_service.create_new_registration.return_value = True
        
        result = await form_flow_service.save_event_selection_to_sheets("12345", "event_001")
        
        # Verify the result is True (success)
        assert result is True
        
        # Verify no error info was stored
        error_info = sample_form_state.get_answer("event_selection_error")
        assert error_info is None
    
    @pytest.mark.asyncio
    async def test_handle_text_answer_event_selection_error(self, form_flow_service, mock_registration_service, sample_form_state):
        """Test that handle_text_answer handles event selection errors."""
        # For SELECT questions, handle_text_answer returns the question definition
        # The re-registration check happens in handle_poll_answer instead
        sample_form_state.current_question = "event_selection"
        form_flow_service.active_forms["12345"] = sample_form_state
        
        # Mock the update object
        mock_update = Mock()
        mock_update.effective_user.id = "12345"
        mock_update.message.text = "event_001"
        
        result = await form_flow_service.handle_text_answer(mock_update, None)
        
        # For SELECT questions, it should return the question definition
        assert result is not None
        assert hasattr(result, 'question_id')
        assert result.question_id == "event_selection"
    
    @pytest.mark.asyncio
    async def test_handle_poll_answer_event_selection_error(self, form_flow_service, mock_registration_service, sample_form_state):
        """Test that handle_poll_answer handles event selection errors."""
        # Add error info to form state
        sample_form_state.answers["event_selection_error"] = {
            "already_registered": True,
            "registration_id": "REG_12345",
            "status": "pending"
        }
        form_flow_service.active_forms["12345"] = sample_form_state
        
        # Mock the save to fail
        with patch.object(form_flow_service, 'save_answer_to_sheets', return_value=False):
            result = await form_flow_service.handle_poll_answer("event_selection", "12345", [0])
            
            # Verify the result indicates already registered
            assert result["error"] is True
            assert result["already_registered"] is True
            assert "אתה כבר רשום לאירוע זה" in result["message"]
            assert result["registration_id"] == "REG_12345"
            assert result["status"] == "pending"
    
    def test_is_user_registered_for_event_active_statuses(self, mock_sheets_service):
        """Test that is_user_registered_for_event correctly identifies active registrations."""
        # Create a mock registration service
        mock_reg_service = RegistrationService(mock_sheets_service)
        
        # Mock the sheet data
        mock_sheets_service.get_data_from_sheet.return_value = {
            'headers': ['user_id', 'event_id', 'status'],
            'rows': [
                ['12345', 'event_001', 'pending'],
                ['12345', 'event_002', 'cancelled'],
                ['67890', 'event_001', 'approved']
            ]
        }
        
        # Mock the headers
        mock_reg_service.headers = {
            'user_id': 0,
            'event_id': 1,
            'status': 2
        }
        
        # Test active registration
        assert mock_reg_service.is_user_registered_for_event("12345", "event_001") is True
        
        # Test cancelled registration (should not be considered active)
        assert mock_reg_service.is_user_registered_for_event("12345", "event_002") is False
        
        # Test non-existent registration
        assert mock_reg_service.is_user_registered_for_event("99999", "event_001") is False


if __name__ == "__main__":
    pytest.main([__file__]) 