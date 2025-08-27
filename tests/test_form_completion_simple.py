"""
Simple test for form completion functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from telegram_bot.services.form_flow_service import FormFlowService, FormState


class TestFormCompletionSimple:
    """Simple test for form completion functionality."""
    
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
            "relevant_experience": "Some experience",
            "partner_or_single": "single",
            "last_sti_test": "01/01/2024",
            "facebook_profile": "https://facebook.com/testuser"
        }
        return form_state
    
    @pytest.mark.asyncio
    async def test_get_completion_message_default(self, sample_form_state):
        """Test getting default completion message."""
        # Create a minimal form flow service with mocked dependencies
        mock_sheets_service = Mock()
        mock_sheets_service.headers = {"Users": {}, "Registrations": {}, "Events": {}, "Groups": {}}
        
        # Mock the parse_upcoming_events method to avoid complex initialization
        with patch.object(FormFlowService, '_initialize_question_definitions', return_value={}):
            service = FormFlowService(mock_sheets_service)
            
            message = await service._get_completion_message(sample_form_state)
            
            assert "he" in message
            assert "en" in message
            assert "תודה על ההרשמה" in message["he"] or "Thank you for registering" in message["en"]
    
    @pytest.mark.asyncio
    async def test_get_completion_message_no_registration(self, sample_form_state):
        """Test getting completion message for no registration."""
        # Set would_you_like_to_register to "no"
        sample_form_state.answers["would_you_like_to_register"] = "no"
        
        # Create a minimal form flow service with mocked dependencies
        mock_sheets_service = Mock()
        mock_sheets_service.headers = {"Users": {}, "Registrations": {}, "Events": {}, "Groups": {}}
        
        # Mock the parse_upcoming_events method to avoid complex initialization
        with patch.object(FormFlowService, '_initialize_question_definitions', return_value={}):
            service = FormFlowService(mock_sheets_service)
            
            message = await service._get_completion_message(sample_form_state)
            
            assert "he" in message
            assert "en" in message
            assert "תודה על העניין שלך" in message["he"] or "Thank you for your interest" in message["en"]
    
    def test_create_error_response(self, sample_form_state):
        """Test creating error response."""
        # Create a minimal form flow service with mocked dependencies
        mock_sheets_service = Mock()
        mock_sheets_service.headers = {"Users": {}, "Registrations": {}, "Events": {}, "Groups": {}}
        
        # Mock the parse_upcoming_events method to avoid complex initialization
        with patch.object(FormFlowService, '_initialize_question_definitions', return_value={}):
            service = FormFlowService(mock_sheets_service)
            
            error_response = service._create_error_response("Test error message")
            
            assert error_response["completed"] is False
            assert "error" in error_response
            assert error_response["error"] == "Test error message"
            assert "message" in error_response
            assert "he" in error_response["message"]
            assert "en" in error_response["message"]


if __name__ == "__main__":
    pytest.main([__file__]) 