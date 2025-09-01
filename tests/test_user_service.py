import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.user_service import UserService
from telegram_bot.models.user import CreateUserFromTelegramDTO


class TestUserService:
    """Test suite for UserService class"""
    
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
                "relevant_experience": 4
            }
        }
        return sheets_service
    
    @pytest.fixture
    def user_service(self, mock_sheets_service):
        """Create a UserService instance with mocked dependencies"""
        return UserService(mock_sheets_service)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience'],
            'rows': [
                ['123456789', '@testuser', 'Test User', 'en', '{}'],
                ['987654321', '@anotheruser', 'Another User', 'he', '{"event1": "experienced"}']
            ]
        }
    
    def test_init(self, mock_sheets_service):
        """Test UserService initialization"""
        user_service = UserService(mock_sheets_service)
        
        assert user_service.sheets_service == mock_sheets_service
        assert user_service.headers == mock_sheets_service.headers["Users"]
    
    def test_get_user_by_telegram_id_found(self, user_service, sample_user_data):
        """Test getting user by telegram ID when user exists"""
        user_service.sheets_service.get_data_from_sheet.return_value = sample_user_data
        
        result = user_service.get_user_by_telegram_id("123456789")
        
        assert result is not None
        assert result[0] == "123456789"
        assert result[1] == "@testuser"
        assert result[2] == "Test User"
        assert result[3] == "en"
        user_service.sheets_service.get_data_from_sheet.assert_called_once_with("Users")
    
    def test_get_user_by_telegram_id_not_found(self, user_service, sample_user_data):
        """Test getting user by telegram ID when user doesn't exist"""
        user_service.sheets_service.get_data_from_sheet.return_value = sample_user_data
        
        result = user_service.get_user_by_telegram_id("999999999")
        
        assert result is None
        user_service.sheets_service.get_data_from_sheet.assert_called_once_with("Users")
    
    def test_get_user_by_telegram_id_no_sheet_data(self, user_service):
        """Test getting user by telegram ID when sheet data is empty"""
        user_service.sheets_service.get_data_from_sheet.return_value = None
        
        result = user_service.get_user_by_telegram_id("123456789")
        
        assert result is None
        user_service.sheets_service.get_data_from_sheet.assert_called_once_with("Users")
    
    def test_get_user_by_telegram_id_empty_rows(self, user_service):
        """Test getting user by telegram ID when rows are empty"""
        user_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language'],
            'rows': []
        }
        
        result = user_service.get_user_by_telegram_id("123456789")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_new_user_success(self, user_service):
        """Test successful user creation"""
        sheet_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience'],
            'rows': []
        }
        user_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        user_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        user_dto = CreateUserFromTelegramDTO(
            full_name="New User",
            telegram_user_id="555666777",
            telegram_username="@newuser",
            language="en"
        )
        
        result = await user_service.create_new_user(user_dto)
        
        assert result is True
        user_service.sheets_service.get_data_from_sheet.assert_called_once_with("Users")
        user_service.sheets_service.append_row.assert_called_once()
        
        # Check that the correct data was passed to append_row
        call_args = user_service.sheets_service.append_row.call_args
        assert call_args[0][0] == "Users"  # sheet name
        new_row = call_args[0][1]  # the new row data
        assert new_row[0] == "555666777"  # telegram_user_id
        assert new_row[1] == "@newuser"   # telegram username
        assert new_row[2] == "New User"   # full_name
        assert new_row[3] == "en"         # language
    
    @pytest.mark.asyncio
    async def test_create_new_user_failure_no_sheet_data(self, user_service):
        """Test user creation failure when sheet data is not available"""
        user_service.sheets_service.get_data_from_sheet.return_value = None
        
        user_dto = CreateUserFromTelegramDTO(
            full_name="New User",
            telegram_user_id="555666777",
            telegram_username="@newuser",
            language="en"
        )
        
        result = await user_service.create_new_user(user_dto)
        
        assert result is False
        user_service.sheets_service.get_data_from_sheet.assert_called_once_with("Users")
        user_service.sheets_service.append_row.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_new_user_failure_append_fails(self, user_service):
        """Test user creation failure when append_row fails"""
        sheet_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language'],
            'rows': []
        }
        user_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        user_service.sheets_service.append_row = AsyncMock(return_value=False)
        
        user_dto = CreateUserFromTelegramDTO(
            full_name="New User",
            telegram_user_id="555666777",
            telegram_username="@newuser",
            language="en"
        )
        
        result = await user_service.create_new_user(user_dto)
        
        assert result is False
        user_service.sheets_service.append_row.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_field(self, user_service):
        """Test updating user field"""
        user_service.sheets_service.update_cell = AsyncMock(return_value=True)
        
        result = await user_service.update_user_field("123456789", "full_name", "Updated Name")
        
        assert result is True
        user_service.sheets_service.update_cell.assert_called_once_with(
            "123456789", "telegram_user_id", "Users", "full_name", "Updated Name"
        )
    
    @pytest.mark.asyncio
    async def test_save_relevant_experience_new_user(self, user_service):
        """Test saving relevant experience for new user"""
        user_data = ['123456789', '@testuser', 'Test User', 'en', '{}']
        with patch.object(user_service, 'get_user_by_telegram_id', return_value=user_data):
            user_service.update_user_field = AsyncMock(return_value=True)
            
            result = await user_service.save_relevant_experience("123456789", "event1", "experienced")
            
            assert result is True
            user_service.update_user_field.assert_called_once_with(
                "123456789", "relevant_experience", "{'event1': 'experienced'}"
            )
    
    @pytest.mark.asyncio
    async def test_save_relevant_experience_existing_user(self, user_service):
        """Test saving relevant experience for user with existing experience"""
        user_data = ['123456789', '@testuser', 'Test User', 'en', '{"event1": "beginner"}']
        with patch.object(user_service, 'get_user_by_telegram_id', return_value=user_data):
            user_service.update_user_field = AsyncMock(return_value=True)
            
            result = await user_service.save_relevant_experience("123456789", "event1", "experienced")
            
            assert result is True
            user_service.update_user_field.assert_called_once_with(
                "123456789", "relevant_experience", "{'event1': 'experienced'}"
            )
    
    @pytest.mark.asyncio
    async def test_save_relevant_experience_user_not_found(self, user_service):
        """Test saving relevant experience when user is not found"""
        with patch.object(user_service, 'get_user_by_telegram_id', return_value=None):
            user_service.update_user_field = AsyncMock()
            
            result = await user_service.save_relevant_experience("999999999", "event1", "experienced")
            
            assert result is False
            user_service.update_user_field.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_save_relevant_experience_with_string_experience(self, user_service):
        """Test saving relevant experience when experience is stored as string"""
        user_data = ['123456789', '@testuser', 'Test User', 'en', '{"event1": "beginner"}']
        with patch.object(user_service, 'get_user_by_telegram_id', return_value=user_data):
            user_service.update_user_field = AsyncMock(return_value=True)
            
            result = await user_service.save_relevant_experience("123456789", "event2", "intermediate")
            
            assert result is True
            user_service.update_user_field.assert_called_once_with(
                "123456789", "relevant_experience", "{'event1': 'beginner', 'event2': 'intermediate'}"
            )
    
    @pytest.mark.asyncio
    async def test_save_relevant_experience_empty_experience(self, user_service):
        """Test saving relevant experience when experience field is empty"""
        user_data = ['123456789', '@testuser', 'Test User', 'en', '']
        with patch.object(user_service, 'get_user_by_telegram_id', return_value=user_data):
            user_service.update_user_field = AsyncMock(return_value=True)
            
            result = await user_service.save_relevant_experience("123456789", "event1", "experienced")
            
            assert result is True
            user_service.update_user_field.assert_called_once_with(
                "123456789", "relevant_experience", "{'event1': 'experienced'}"
            )
    
    def test_get_user_by_telegram_id_string_conversion(self, user_service, sample_user_data):
        """Test that telegram_user_id is converted to string for comparison"""
        user_service.sheets_service.get_data_from_sheet.return_value = sample_user_data
        
        # Test with integer input
        result = user_service.get_user_by_telegram_id(123456789)
        
        assert result is not None
        assert result[0] == "123456789"
    
    @pytest.mark.asyncio
    async def test_create_new_user_with_none_username(self, user_service):
        """Test creating user with None username"""
        sheet_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language'],
            'rows': []
        }
        user_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        user_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        user_dto = CreateUserFromTelegramDTO(
            full_name="New User",
            telegram_user_id="555666777",
            telegram_username=None,
            language="en"
        )
        
        result = await user_service.create_new_user(user_dto)
        
        assert result is True
        call_args = user_service.sheets_service.append_row.call_args
        new_row = call_args[0][1]
        assert new_row[1] == ""  # Empty string for None username 