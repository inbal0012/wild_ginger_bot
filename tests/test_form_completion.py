"""
Test form completion functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from telegram_bot.services.form_flow_service import FormFlowService
from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.services.user_service import UserService
from telegram_bot.services.registration_service import RegistrationService
from telegram_bot.models.form_flow import FormState


class TestFormCompletion:
    """Test form completion functionality."""
    
    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock sheets service."""
        mock = Mock(spec=SheetsService)
        mock.headers = {"Users": {}, "Registrations": {}, "Events": {}, "Groups": {}}
        mock.get_user_by_telegram_id = Mock(return_value=None)  # User doesn't exist
        mock.add_user = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_user_service(self):
        """Create a mock user service."""
        mock = Mock(spec=UserService)
        mock.get_user_by_telegram_id = Mock(return_value=None)  # User doesn't exist
        mock.create_new_user = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_registration_service(self):
        """Create a mock registration service."""
        mock = Mock(spec=RegistrationService)
        mock.create_new_registration = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def form_flow_service(self, mock_sheets_service, mock_user_service):
        """Create a form flow service with mocked dependencies."""
        service = FormFlowService(mock_sheets_service)
        return service
    
    @pytest.fixture
    def sample_form_state(self):
        """Create a sample form state for testing."""
        form_state = FormState(user_id="12345", event_id="event_001", language="he")
        form_state.answers = {
            "language": "he",
            "event_selection": "event_001",
            "interested_in_event_types": "play",
            "would_you_like_to_register": "yes",
            "full_name": "Test User",
            "relevent_experience": "Some experience",
            "partner_or_single": "single",
            "last_sti_test": "01/01/2024",
            "facebook_profile": "https://facebook.com/testuser"
        }
        return form_state
    
    @pytest.mark.asyncio
    async def test_complete_form_success(self, form_flow_service, sample_form_state, mock_sheets_service):
        """Test successful form completion."""
        # Mock the update_form_complete function
        with patch('telegram_bot.services.form_flow_service.update_form_complete', return_value=True):
            result = await form_flow_service._complete_form(sample_form_state)
        
        # Verify the result
        assert result["completed"] is True
        assert "form_id" in result
        assert "registration_id" in result
        assert "user_id" in result
        assert "message" in result
        assert "completion_date" in result
        
        # Verify that user and registration were created
        mock_sheets_service.add_user.assert_called_once()
        mock_sheets_service.add_registration.assert_called_once()
        
        # Verify form state was updated
        assert sample_form_state.completed is True
        assert sample_form_state.completion_date is not None
    
    @pytest.mark.asyncio
    async def test_complete_form_user_creation_failure(self, form_flow_service, sample_form_state, mock_sheets_service):
        """Test form completion when user creation fails."""
        # Mock user creation to fail
        mock_sheets_service.add_user = AsyncMock(return_value=False)
        
        result = await form_flow_service._complete_form(sample_form_state)
        
        # Verify error response
        assert result["completed"] is False
        assert "error" in result
        assert "Failed to create user record" in result["error"]
        
        # Verify form state was not marked as completed
        assert sample_form_state.completed is False
    
    @pytest.mark.asyncio
    async def test_complete_form_registration_creation_failure(self, form_flow_service, sample_form_state, mock_sheets_service):
        """Test form completion when registration creation fails."""
        # Mock registration creation to fail
        mock_sheets_service.add_registration = AsyncMock(return_value=False)
        
        result = await form_flow_service._complete_form(sample_form_state)
        
        # Verify error response
        assert result["completed"] is False
        assert "error" in result
        assert "Failed to create registration record" in result["error"]
    
    @pytest.mark.asyncio
    async def test_complete_form_no_registration(self, form_flow_service, sample_form_state, mock_sheets_service):
        """Test form completion when user chooses not to register."""
        # Set would_you_like_to_register to "no"
        sample_form_state.answers["would_you_like_to_register"] = "no"
        
        with patch('telegram_bot.services.form_flow_service.update_form_complete', return_value=True):
            result = await form_flow_service._complete_form(sample_form_state)
        
        # Verify the result
        assert result["completed"] is True
        assert "message" in result
        
        # Verify the message is appropriate for no registration
        message = result["message"]
        assert "תודה על העניין שלך" in message["he"] or "Thank you for your interest" in message["en"]
    
    @pytest.mark.asyncio
    async def test_complete_form_returning_participant(self, form_flow_service, sample_form_state, mock_sheets_service):
        """Test form completion for returning participant."""
        # Add returning participant answer
        sample_form_state.answers["returning_participant"] = "yes"
        
        with patch('telegram_bot.services.form_flow_service.update_form_complete', return_value=True), \
             patch('telegram_bot.services.form_flow_service.update_get_to_know_complete', return_value=True):
            result = await form_flow_service._complete_form(sample_form_state)
        
        # Verify the result
        assert result["completed"] is True
        
        # Verify that get-to-know was auto-marked complete
        # This would be verified by checking if update_get_to_know_complete was called
    
    def test_get_completion_message_default(self, form_flow_service, sample_form_state):
        """Test getting default completion message."""
        message = asyncio.run(form_flow_service._get_completion_message(sample_form_state))
        
        assert "he" in message
        assert "en" in message
        assert "תודה על ההרשמה" in message["he"] or "Thank you for registering" in message["en"]
    
    def test_get_completion_message_no_registration(self, form_flow_service, sample_form_state):
        """Test getting completion message for no registration."""
        sample_form_state.answers["would_you_like_to_register"] = "no"
        
        message = asyncio.run(form_flow_service._get_completion_message(sample_form_state))
        
        assert "he" in message
        assert "en" in message
        assert "תודה על העניין שלך" in message["he"] or "Thank you for your interest" in message["en"]


if __name__ == "__main__":
    pytest.main([__file__]) 