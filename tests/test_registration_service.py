import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.registration_service import RegistrationService
from telegram_bot.models.registration import CreateRegistrationDTO, RegistrationStatus, Status, RegistrationData


class TestRegistrationService:
    """Test suite for RegistrationService class"""
    
    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock SheetsService"""
        sheets_service = Mock()
        sheets_service.headers = {
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
                "arrived": 33
            }
        }
        return sheets_service
    
    @pytest.fixture
    def registration_service(self, mock_sheets_service):
        """Create a RegistrationService instance with mocked dependencies"""
        return RegistrationService(mock_sheets_service)
    
    @pytest.fixture
    def sample_registration_data(self):
        """Sample registration data for testing"""
        return {
            'headers': ['registration_id', 'user_id', 'event_id', 'status', 'partner_telegram_link', 'payment_status', 'payment_method', 'registration_date', 'payment_date', 'partner_or_single', 'intro_opt_in', 'intro_text', 'intro_posted_at', 'created_at', 'updated_at', 'would_you_like_to_register', 'last_sti_test', 'bdsm_declaration', 'is_play_with_partner_only', 'desired_play_partners', 'contact_type', 'contact_type_other', 'share_bdsm_interests', 'alcohol_in_event', 'agree_participant_commitment', 'enthusiastic_verbal_consent_commitment', 'agree_line_rules', 'wants_to_helper', 'helper_shifts', 'wants_to_DM', 'DM_shifts', 'get_to_know_status', 'group_status', 'arrived'],
            'rows': [
                ['reg1', 'user1', 'event1', 'approved', '@partner1', 'paid', 'credit_card', '2024-01-01', '2024-01-02', 'partner', 'yes', 'Hello world', '2024-01-03', '2024-01-01', '2024-01-01', 'true', '2024-01-01', 'true', 'false', 'anyone', 'telegram', '', 'true', 'yes', 'true', 'true', 'true', 'false', '', 'false', '', 'complete', 'open', 'false'],
                ['reg2', 'user2', 'event1', 'pending', '@partner2', 'pending', 'paypal', '2024-01-01', '', 'single', 'no', '', '', '2024-01-01', '2024-01-01', 'true', '2024-01-01', 'true', 'true', 'partner_only', 'email', 'test@email.com', 'false', 'no', 'true', 'true', 'true', 'true', 'morning', 'true', 'evening', 'incomplete', 'closed', 'false'],
                ['reg3', 'user1', 'event2', 'cancelled', '', 'refunded', '', '2024-01-01', '2024-01-02', 'single', 'no', '', '', '2024-01-01', '2024-01-01', 'false', '', 'false', 'false', 'anyone', 'telegram', '', 'false', 'maybe', 'false', 'false', 'false', 'false', '', 'false', '', 'not_started', 'closed', 'false']
            ]
        }
    
    def test_init(self, mock_sheets_service):
        """Test RegistrationService initialization"""
        registration_service = RegistrationService(mock_sheets_service)
        
        assert registration_service.sheets_service == mock_sheets_service
        assert registration_service.headers == mock_sheets_service.headers["Registrations"]
    
    @pytest.mark.asyncio
    async def test_create_new_registration_success(self, registration_service):
        """Test successful registration creation"""
        sheet_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456"
        )
        
        result = await registration_service.create_new_registration(registration_dto)
        
        assert result is True
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
        registration_service.sheets_service.append_row.assert_called_once()
        
        # Check that the correct data was passed to append_row
        call_args = registration_service.sheets_service.append_row.call_args
        assert call_args[0][0] == "Registrations"  # sheet name
        new_row = call_args[0][1]  # the new row data
        assert new_row[0] == registration_dto.id  # registration_id
        assert new_row[1] == "user123"  # user_id
        assert new_row[2] == "event456"  # event_id
        assert new_row[3] == RegistrationStatus.FORM_INCOMPLETE.value  # status
    
    @pytest.mark.asyncio
    async def test_create_new_registration_with_custom_status(self, registration_service):
        """Test registration creation with custom status"""
        sheet_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456",
            status=RegistrationStatus.APPROVED.value
        )
        
        result = await registration_service.create_new_registration(registration_dto)
        
        assert result is True
        
        # Check that the custom status was used
        call_args = registration_service.sheets_service.append_row.call_args
        new_row = call_args[0][1]
        assert new_row[3] == RegistrationStatus.APPROVED.value
    
    @pytest.mark.asyncio
    async def test_create_new_registration_failure_no_sheet_data(self, registration_service):
        """Test registration creation failure when sheet data is not available"""
        registration_service.sheets_service.get_data_from_sheet.return_value = None
        
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456"
        )
        
        result = await registration_service.create_new_registration(registration_dto)
        
        assert result is False
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
        registration_service.sheets_service.append_row.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_new_registration_failure_append_fails(self, registration_service):
        """Test registration creation failure when append_row fails"""
        sheet_data = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': []
        }
        registration_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        registration_service.sheets_service.append_row = AsyncMock(return_value=False)
        
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456"
        )
        
        result = await registration_service.create_new_registration(registration_dto)
        
        assert result is False
        registration_service.sheets_service.append_row.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_new_registration_exception_handling(self, registration_service):
        """Test registration creation exception handling"""
        registration_service.sheets_service.get_data_from_sheet.side_effect = Exception("Test error")
        # Mock the logger to avoid AttributeError
        registration_service.logger = Mock()
        
        registration_dto = CreateRegistrationDTO(
            user_id="user123",
            event_id="event456"
        )
        
        result = await registration_service.create_new_registration(registration_dto)
        
        assert result is False
        registration_service.logger.error.assert_called_once()
    
    def test_get_registration_id_by_user_id_found(self, registration_service, sample_registration_data):
        """Test getting registration ID when registration exists"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        registration_id = registration_service.get_registration_id_by_user_id("user1", "event1")
        
        assert registration_id == "reg1"
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_get_registration_id_by_user_id_not_found(self, registration_service, sample_registration_data):
        """Test getting registration ID when registration doesn't exist"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        registration_id = registration_service.get_registration_id_by_user_id("user999", "event999")
        
        assert registration_id is None
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_get_registration_id_by_user_id_no_data(self, registration_service):
        """Test getting registration ID when no data is available"""
        registration_service.sheets_service.get_data_from_sheet.return_value = None
        
        registration_id = registration_service.get_registration_id_by_user_id("user1", "event1")
        
        assert registration_id is None
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_get_registration_id_by_user_id_string_conversion(self, registration_service, sample_registration_data):
        """Test that user_id and event_id are converted to string for comparison"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        # Test with integer inputs
        registration_id = registration_service.get_registration_id_by_user_id(123, 456)
        
        assert registration_id is None  # No registration with these IDs in sample data
    
    def test_is_user_registered_for_event_active_registration(self, registration_service, sample_registration_data):
        """Test checking if user is registered for event with active registration"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        is_registered = registration_service.is_user_registered_for_event("user1", "event1")
        
        assert is_registered is True
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_is_user_registered_for_event_pending_registration(self, registration_service, sample_registration_data):
        """Test checking if user is registered for event with pending registration"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        is_registered = registration_service.is_user_registered_for_event("user2", "event1")
        
        assert is_registered is True  # 'pending' is considered active
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_is_user_registered_for_event_cancelled_registration(self, registration_service, sample_registration_data):
        """Test checking if user is registered for event with cancelled registration"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        is_registered = registration_service.is_user_registered_for_event("user1", "event2")
        
        assert is_registered is False  # 'cancelled' is not considered active
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_is_user_registered_for_event_not_registered(self, registration_service, sample_registration_data):
        """Test checking if user is registered for event when not registered"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        is_registered = registration_service.is_user_registered_for_event("user999", "event999")
        
        assert is_registered is False
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_is_user_registered_for_event_no_data(self, registration_service):
        """Test checking if user is registered for event when no data is available"""
        registration_service.sheets_service.get_data_from_sheet.return_value = None
        
        is_registered = registration_service.is_user_registered_for_event("user1", "event1")
        
        assert is_registered is False
        registration_service.sheets_service.get_data_from_sheet.assert_called_once_with("Registrations")
    
    def test_is_user_registered_for_event_missing_columns(self, registration_service):
        """Test checking if user is registered for event when required columns are missing"""
        registration_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['registration_id'],  # Missing user_id and event_id columns
            'rows': []
        }
        
        is_registered = registration_service.is_user_registered_for_event("user1", "event1")
        
        assert is_registered is False
    
    def test_is_user_registered_for_event_string_conversion(self, registration_service, sample_registration_data):
        """Test that user_id and event_id are converted to string for comparison"""
        registration_service.sheets_service.get_data_from_sheet.return_value = sample_registration_data
        
        # Test with integer inputs
        is_registered = registration_service.is_user_registered_for_event(123, 456)
        
        assert is_registered is False  # No registration with these IDs in sample data
    
    def test_is_user_registered_for_event_case_insensitive_status(self, registration_service):
        """Test that status comparison is case insensitive"""
        registration_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': [
                ['reg1', 'user1', 'event1', 'APPROVED'],  # Uppercase status
                ['reg2', 'user2', 'event1', 'Pending'],   # Mixed case status
                ['reg3', 'user3', 'event1', 'form_complete']  # Lowercase status
            ]
        }
        
        # All should be considered active
        assert registration_service.is_user_registered_for_event("user1", "event1") is True
        assert registration_service.is_user_registered_for_event("user2", "event1") is True
        assert registration_service.is_user_registered_for_event("user3", "event1") is True
    
    def test_is_user_registered_for_event_inactive_statuses(self, registration_service):
        """Test that inactive statuses are not considered registered"""
        registration_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': [
                ['reg1', 'user1', 'event1', 'cancelled'],
                ['reg2', 'user2', 'event1', 'rejected'],
                ['reg3', 'user3', 'event1', 'withdrawn']
            ]
        }
        
        # All should be considered inactive
        assert registration_service.is_user_registered_for_event("user1", "event1") is False
        assert registration_service.is_user_registered_for_event("user2", "event1") is False
        assert registration_service.is_user_registered_for_event("user3", "event1") is False
    
    def test_is_user_registered_for_event_missing_status_column(self, registration_service):
        """Test behavior when status column is missing"""
        registration_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['registration_id', 'user_id', 'event_id'],  # Missing status column
            'rows': [
                ['reg1', 'user1', 'event1']
            ]
        }
        
        # Should return True when status column is missing (assumes active)
        is_registered = registration_service.is_user_registered_for_event("user1", "event1")
        
        assert is_registered is True
    
    def test_is_user_registered_for_event_empty_status(self, registration_service):
        """Test behavior when status is empty"""
        registration_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['registration_id', 'user_id', 'event_id', 'status'],
            'rows': [
                ['reg1', 'user1', 'event1', '']  # Empty status
            ]
        }
        
        # Should return False for empty status
        is_registered = registration_service.is_user_registered_for_event("user1", "event1")
        
        assert is_registered is False 