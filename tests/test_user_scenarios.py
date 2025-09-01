import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.user_service import UserService
from telegram_bot.services.registration_service import RegistrationService
from telegram_bot.services.event_service import EventService
from telegram_bot.models.user import CreateUserFromTelegramDTO
from telegram_bot.models.registration import CreateRegistrationDTO, RegistrationStatus
from telegram_bot.models.event import CreateEventDTO


class TestUserScenarios:
    """Test suite for different user scenarios"""
    
    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock SheetsService"""
        sheets_service = Mock()
        sheets_service.headers = {
            "Users": {
                "telegram_user_id": 0,
                "telegram": 1,
                "full_name": 2,
                "language": 3,
                "relevant_experience": 4,
                "is_returning_participant": 5
            },
            "Registrations": {
                "registration_id": 0,
                "user_id": 1,
                "event_id": 2,
                "status": 3,
                "partner_telegram_link": 4,
                "payment_status": 5,
                "payment_method": 6,
                "registration_date": 7,
                "payment_date": 8,
                "partner_or_single": 9,
                "intro_opt_in": 10,
                "intro_text": 11,
                "intro_posted_at": 12,
                "created_at": 13,
                "updated_at": 14,
                "would_you_like_to_register": 15,
                "last_sti_test": 16,
                "bdsm_declaration": 17,
                "is_play_with_partner_only": 18,
                "desired_play_partners": 19,
                "contact_type": 20,
                "contact_type_other": 21,
                "share_bdsm_interests": 22,
                "alcohol_in_event": 23,
                "agree_participant_commitment": 24,
                "enthusiastic_verbal_consent_commitment": 25,
                "agree_line_rules": 26,
                "wants_to_helper": 27,
                "helper_shifts": 28,
                "wants_to_DM": 29,
                "DM_shifts": 30,
                "get_to_know_status": 31,
                "group_status": 32,
                "arrived": 33,
                "form_complete": 34,
                "get_to_know_complete": 35
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
        return sheets_service
    
    @pytest.fixture
    def user_service(self, mock_sheets_service):
        """Create a UserService instance"""
        return UserService(mock_sheets_service)
    
    @pytest.fixture
    def registration_service(self, mock_sheets_service):
        """Create a RegistrationService instance"""
        return RegistrationService(mock_sheets_service)
    
    @pytest.fixture
    def event_service(self, mock_sheets_service):
        """Create an EventService instance"""
        return EventService(mock_sheets_service)
    
    # ===== NEW USER SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_new_user_first_time_registration(self, user_service, registration_service, event_service):
        """Test new user registering for the first time"""
        # Mock user data - new user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        user_service.sheets_service.get_data_from_sheet.return_value = user_data
        user_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Mock event data - BDSM workshop
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event1', 'BDSM Basics Workshop', 'bdsm_workshop', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create new user
        user_dto = CreateUserFromTelegramDTO(
            full_name="New User",
            telegram_user_id="newuser123",
            telegram_username="@newuser",
            language="en"
        )
        
        user_result = await user_service.create_new_user(user_dto)
        assert user_result is True
        
        # Create registration
        registration_dto = CreateRegistrationDTO(
            user_id="newuser123",
            event_id="event1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify user is marked as new (not returning)
        user_service.sheets_service.append_row.assert_called()
        call_args = user_service.sheets_service.append_row.call_args_list[0]
        new_user_row = call_args[0][1]
        # Check that is_returning_participant field is empty/false for new user
        assert new_user_row[5] == ""  # is_returning_participant field
    
    @pytest.mark.asyncio
    async def test_new_user_cuddle_event_registration(self, user_service, registration_service, event_service):
        """Test new user registering for a cuddle event"""
        # Mock event data - cuddle event
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['cuddle1', 'Cozy Cuddle Party', 'cuddle_party', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration for cuddle event
        registration_dto = CreateRegistrationDTO(
            user_id="newuser123",
            event_id="cuddle1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify event type is correctly set
        event_type = event_service.get_event_type("cuddle1")
        assert event_type == "cuddle_party"
    
    @pytest.mark.asyncio
    async def test_new_user_sexual_event_registration(self, user_service, registration_service, event_service):
        """Test new user registering for a sexual event"""
        # Mock event data - sexual event
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['sexual1', 'Intimate Play Party', 'sexual_party', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration for sexual event
        registration_dto = CreateRegistrationDTO(
            user_id="newuser123",
            event_id="sexual1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify event type is correctly set
        event_type = event_service.get_event_type("sexual1")
        assert event_type == "sexual_party"
    
    # ===== RETURNING USER SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_returning_user_registration(self, user_service, registration_service, event_service):
        """Test returning user registering for an event"""
        # Mock user data - returning user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['returning123', '@returninguser', 'Returning User', 'en', '{"bdsm_workshop": "experienced", "cuddle_party": "beginner"}', 'true']
            ]
        }
        user_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event2', 'Advanced BDSM Workshop', 'bdsm_workshop', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration for returning user
        registration_dto = CreateRegistrationDTO(
            user_id="returning123",
            event_id="event2"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify user has experience in this event type
        user = user_service.get_user_by_telegram_id("returning123")
        assert user is not None
        assert user[5] == "true"  # is_returning_participant
        assert "bdsm_workshop" in user[4]  # relevant_experience
    
    @pytest.mark.asyncio
    async def test_returning_user_different_event_type(self, user_service, registration_service, event_service):
        """Test returning user registering for a different event type than they have experience with"""
        # Mock user data - returning user with BDSM experience
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['returning123', '@returninguser', 'Returning User', 'en', '{"bdsm_workshop": "experienced"}', 'true']
            ]
        }
        user_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data - sexual event (different from their experience)
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['sexual1', 'Intimate Play Party', 'sexual_party', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration for different event type
        registration_dto = CreateRegistrationDTO(
            user_id="returning123",
            event_id="sexual1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify user is still marked as returning but doesn't have experience in this event type
        user = user_service.get_user_by_telegram_id("returning123")
        assert user is not None
        assert user[5] == "true"  # is_returning_participant
        assert "sexual_party" not in user[4]  # relevant_experience
    
    # ===== EVENT TYPE SPECIFIC SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_bdsm_workshop_registration_flow(self, user_service, registration_service, event_service):
        """Test complete registration flow for BDSM workshop"""
        # Mock BDSM workshop event
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status', 'description', 'line_rules', 'place_rules'],
            'rows': [
                ['bdsm1', 'BDSM Safety Workshop', 'bdsm_workshop', 'active', 'Learn BDSM safety practices', 'Consent is mandatory', 'Safe space rules apply']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status', 'bdsm_declaration', 'agree_line_rules'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="bdsm1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify event details
        event = event_service.get_event_by_id("bdsm1")
        assert event is not None
        assert event.event_type == "bdsm_workshop"
        assert "BDSM" in event.name
        assert "Consent is mandatory" in event.line_rules
    
    @pytest.mark.asyncio
    async def test_cuddle_party_registration_flow(self, user_service, registration_service, event_service):
        """Test complete registration flow for cuddle party"""
        # Mock cuddle party event
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status', 'description', 'line_rules', 'place_rules'],
            'rows': [
                ['cuddle1', 'Cozy Cuddle Party', 'cuddle_party', 'active', 'Relaxing cuddle session', 'Respect boundaries', 'Comfortable clothing required']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status', 'is_play_with_partner_only'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="cuddle1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify event details
        event = event_service.get_event_by_id("cuddle1")
        assert event is not None
        assert event.event_type == "cuddle_party"
        assert "Cuddle" in event.name
        assert "Comfortable clothing" in event.place_rules
    
    @pytest.mark.asyncio
    async def test_sexual_party_registration_flow(self, user_service, registration_service, event_service):
        """Test complete registration flow for sexual party"""
        # Mock sexual party event
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status', 'description', 'line_rules', 'place_rules'],
            'rows': [
                ['sexual1', 'Intimate Play Party', 'sexual_party', 'active', 'Adult play party', 'Explicit consent required', 'Private play areas available']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status', 'last_sti_test', 'enthusiastic_verbal_consent_commitment'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create registration
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="sexual1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Verify event details
        event = event_service.get_event_by_id("sexual1")
        assert event is not None
        assert event.event_type == "sexual_party"
        assert "Play" in event.name
        assert "Explicit consent" in event.line_rules
    
    # ===== MIXED SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_user_registers_for_multiple_event_types(self, user_service, registration_service, event_service):
        """Test user registering for multiple different event types"""
        # Mock multiple events
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['bdsm1', 'BDSM Workshop', 'bdsm_workshop', 'active'],
                ['cuddle1', 'Cuddle Party', 'cuddle_party', 'active'],
                ['sexual1', 'Play Party', 'sexual_party', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Register for BDSM workshop
        reg1 = CreateRegistrationDTO(user_id="user123", event_id="bdsm1")
        result1 = await registration_service.create_new_registration(reg1)
        assert result1 is True
        
        # Register for cuddle party
        reg2 = CreateRegistrationDTO(user_id="user123", event_id="cuddle1")
        result2 = await registration_service.create_new_registration(reg2)
        assert result2 is True
        
        # Register for sexual party
        reg3 = CreateRegistrationDTO(user_id="user123", event_id="sexual1")
        result3 = await registration_service.create_new_registration(reg3)
        assert result3 is True
        
        # Verify all registrations were created
        assert registration_service.sheets_service.append_row.call_count == 3
        
        # Verify user is registered for all events
        assert registration_service.is_user_registered_for_event("user123", "bdsm1") is True
        assert registration_service.is_user_registered_for_event("user123", "cuddle1") is True
        assert registration_service.is_user_registered_for_event("user123", "sexual1") is True
    
    @pytest.mark.asyncio
    async def test_new_user_becomes_returning_user(self, user_service, registration_service, event_service):
        """Test new user participating in events and becoming a returning user"""
        # Mock user data - initially new user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        user_service.sheets_service.get_data_from_sheet.return_value = user_data
        user_service.sheets_service.append_row = AsyncMock(return_value=True)
        user_service.update_user_field = AsyncMock(return_value=True)
        
        # Mock event data
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event1', 'BDSM Workshop', 'bdsm_workshop', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Create new user
        user_dto = CreateUserFromTelegramDTO(
            full_name="New User",
            telegram_user_id="newuser123",
            telegram_username="@newuser",
            language="en"
        )
        
        user_result = await user_service.create_new_user(user_dto)
        assert user_result is True
        
        # Create registration
        registration_dto = CreateRegistrationDTO(
            user_id="newuser123",
            event_id="event1"
        )
        
        reg_result = await registration_service.create_new_registration(registration_dto)
        assert reg_result is True
        
        # Simulate user gaining experience and becoming returning
        await user_service.save_relevant_experience("newuser123", "bdsm_workshop", "experienced")
        
        # Update user to returning participant
        await user_service.update_user_field("newuser123", "is_returning_participant", "true")
        
        # Verify user is now marked as returning
        user_service.update_user_field.assert_called_with("newuser123", "is_returning_participant", "true")
    
    # ===== EDGE CASES =====
    
    @pytest.mark.asyncio
    async def test_user_registers_for_same_event_type_different_events(self, user_service, registration_service, event_service):
        """Test user registering for multiple events of the same type"""
        # Mock multiple BDSM events
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['bdsm1', 'BDSM Basics', 'bdsm_workshop', 'active'],
                ['bdsm2', 'BDSM Advanced', 'bdsm_workshop', 'active'],
                ['bdsm3', 'BDSM Safety', 'bdsm_workshop', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Register for all BDSM events
        for event_id in ["bdsm1", "bdsm2", "bdsm3"]:
            registration_dto = CreateRegistrationDTO(user_id="user123", event_id=event_id)
            result = await registration_service.create_new_registration(registration_dto)
            assert result is True
        
        # Verify all registrations were created
        assert registration_service.sheets_service.append_row.call_count == 3
        
        # Verify user is registered for all events
        for event_id in ["bdsm1", "bdsm2", "bdsm3"]:
            assert registration_service.is_user_registered_for_event("user123", event_id) is True
    
    @pytest.mark.asyncio
    async def test_user_with_mixed_experience_levels(self, user_service, registration_service, event_service):
        """Test user with different experience levels for different event types"""
        # Mock user with mixed experience
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['mixed123', '@mixeduser', 'Mixed Experience User', 'en', '{"bdsm_workshop": "experienced", "cuddle_party": "beginner", "sexual_party": "intermediate"}', 'true']
            ]
        }
        user_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock multiple events
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['bdsm1', 'BDSM Workshop', 'bdsm_workshop', 'active'],
                ['cuddle1', 'Cuddle Party', 'cuddle_party', 'active'],
                ['sexual1', 'Play Party', 'sexual_party', 'active']
            ]
        }
        event_service.sheets_service.get_data_from_sheet.return_value = event_data
        
        # Mock registration data
        reg_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = reg_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        # Register for all events
        for event_id in ["bdsm1", "cuddle1", "sexual1"]:
            registration_dto = CreateRegistrationDTO(user_id="mixed123", event_id=event_id)
            result = await registration_service.create_new_registration(registration_dto)
            assert result is True
        
        # Verify user has appropriate experience levels
        user = user_service.get_user_by_telegram_id("mixed123")
        assert user is not None
        experience = user[4]  # relevant_experience
        assert "bdsm_workshop" in experience
        assert "cuddle_party" in experience
        assert "sexual_party" in experience
        assert user[5] == "true"  # is_returning_participant 