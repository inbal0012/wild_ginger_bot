import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.message_service import MessageService


class TestMessageService:
    """Test suite for MessageService class"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings with test messages"""
        mock_settings = Mock()
        mock_settings.messages = {
            'en': {
                'welcome': 'Welcome {name}!',
                'welcome_no_name': 'Welcome!',
                'help': 'Help message',
                'status_no_name': 'No user found',
                'status_labels': {
                    'partner': 'Partner',
                    'approved': 'Approved',
                    'waiting_review': 'Waiting for review',
                    'form_complete': 'Form Complete',
                    'payment_complete': 'Payment Complete',
                    'get_to_know_complete': 'Get to Know Complete',
                    'paid': 'Paid',
                    'not_paid': 'Not Paid',
                    'group_open': 'Group Open',
                    'group_not_open': 'Group Not Open',
                    'form': 'Form',
                    'get_to_know': 'Get to Know',
                    'status': 'Status',
                    'payment': 'Payment',
                    'group': 'Group'
                }
            },
            'he': {
                'welcome': 'ברוך הבא {name}!',
                'welcome_no_name': 'ברוך הבא!',
                'help': 'הודעת עזרה',
                'status_no_name': 'לא נמצא משתמש',
                'status_labels': {
                    'partner': 'פרטנר',
                    'approved': 'אושר',
                    'waiting_review': 'ממתין לבדיקה',
                    'form_complete': 'טופס הושלם',
                    'payment_complete': 'תשלום הושלם',
                    'get_to_know_complete': 'היכרות הושלמה',
                    'paid': 'שולם',
                    'not_paid': 'לא שולם',
                    'group_open': 'קבוצה פתוחה',
                    'group_not_open': 'קבוצה סגורה',
                    'form': 'טופס',
                    'get_to_know': 'היכרות',
                    'status': 'סטטוס',
                    'payment': 'תשלום',
                    'group': 'קבוצה'
                }
            }
        }
        return mock_settings
    
    @pytest.fixture
    def message_service(self, mock_settings):
        """Create a MessageService instance with mocked settings"""
        with patch('telegram_bot.services.message_service.settings', mock_settings):
            return MessageService()
    
    def test_init(self, mock_settings):
        """Test MessageService initialization"""
        with patch('telegram_bot.services.message_service.settings', mock_settings):
            service = MessageService()
            assert service.messages == mock_settings.messages
    
    def test_get_message_simple(self, message_service):
        """Test getting a simple message without formatting"""
        result = message_service.get_message('en', 'welcome_no_name')
        assert result == 'Welcome!'
    
    def test_get_message_with_formatting(self, message_service):
        """Test getting a message with formatting"""
        result = message_service.get_message('en', 'welcome', name='John')
        assert result == 'Welcome John!'
    
    def test_get_message_hebrew(self, message_service):
        """Test getting a Hebrew message"""
        result = message_service.get_message('he', 'welcome', name='יוחנן')
        assert result == 'ברוך הבא יוחנן!'
    
    def test_get_message_key_not_found_fallback_to_english(self, message_service):
        """Test fallback to English when key not found in requested language"""
        result = message_service.get_message('he', 'nonexistent_key')
        assert result == "Message key 'nonexistent_key' not found"
    
    def test_get_message_key_not_found_anywhere(self, message_service):
        """Test when key is not found in any language"""
        result = message_service.get_message('en', 'nonexistent_key')
        assert result == "Message key 'nonexistent_key' not found"
    
    def test_get_message_multiple_formatting_params(self, message_service):
        """Test message formatting with multiple parameters"""
        # Add a test message with multiple parameters
        message_service.messages['en']['test_multi'] = 'Hello {name}, you are {age} years old'
        
        result = message_service.get_message('en', 'test_multi', name='Alice', age='25')
        assert result == 'Hello Alice, you are 25 years old'
    
    def test_build_partner_status_text_no_partners(self, message_service):
        """Test building partner status text when user has no partners"""
        status_data = {
            'partner_names': [],
            'partner_status': {},
            'partner': False
        }
        
        result_en = message_service.build_partner_status_text(status_data, 'en')
        result_he = message_service.build_partner_status_text(status_data, 'he')
        
        assert result_en == 'Partner: Coming alone'
        assert result_he == 'פרטנר: מגיע.ה לבד'
    
    def test_build_partner_status_text_single_partner_complete(self, message_service):
        """Test building partner status text for single partner who completed form"""
        status_data = {
            'partner_names': ['Partner Name'],
            'partner_status': {},
            'partner': True,
            'partner_alias': 'Partner Alias'
        }
        
        result = message_service.build_partner_status_text(status_data, 'en')
        assert result == 'Partner: ✅ (Partner Alias)'
    
    def test_build_partner_status_text_single_partner_incomplete(self, message_service):
        """Test building partner status text for single partner who hasn't completed form"""
        status_data = {
            'partner_names': ['Partner Name'],
            'partner_status': {},
            'partner': False,
            'partner_alias': 'Partner Alias'
        }
        
        result = message_service.build_partner_status_text(status_data, 'en')
        assert result == 'Partner: ❌ (Partner Alias)'
    
    def test_build_partner_status_text_multiple_partners(self, message_service):
        """Test building partner status text for multiple partners"""
        status_data = {
            'partner_names': ['Partner1', 'Partner2', 'Partner3'],
            'partner_status': {
                'registered_partners': ['Partner1', 'Partner2'],
                'missing_partners': ['Partner3']
            },
            'partner': False
        }
        
        result = message_service.build_partner_status_text(status_data, 'en')
        
        assert 'Partner: Your partners\' status:' in result
        assert '✅ Partner1, Partner2 completed the form' in result
        assert '❌ Partner3 hasn\'t completed the form yet' in result
    
    def test_build_partner_status_text_multiple_partners_hebrew(self, message_service):
        """Test building partner status text for multiple partners in Hebrew"""
        status_data = {
            'partner_names': ['פרטנר1', 'פרטנר2', 'פרטנר3'],
            'partner_status': {
                'registered_partners': ['פרטנר1', 'פרטנר2'],
                'missing_partners': ['פרטנר3']
            },
            'partner': False
        }
        
        result = message_service.build_partner_status_text(status_data, 'he')
        
        assert 'פרטנר: סטטוס הפרטנרים שלך:' in result
        assert '✅ פרטנר1, פרטנר2 השלמו את הטופס' in result
        assert '❌ פרטנר3 עוד לא השלים את הטופס' in result
    
    def test_build_partner_status_text_single_registered_partner_hebrew(self, message_service):
        """Test building partner status text for single registered partner in Hebrew"""
        status_data = {
            'partner_names': ['פרטנר1'],
            'partner_status': {
                'registered_partners': ['פרטנר1'],
                'missing_partners': []
            },
            'partner': True
        }
        
        result = message_service.build_partner_status_text(status_data, 'he')
        
        assert 'פרטנר: ✅' in result
    
    def test_build_partner_status_text_no_detailed_status(self, message_service):
        """Test building partner status text when no detailed status is available"""
        status_data = {
            'partner_names': ['Partner1'],
            'partner_status': {},
            'partner': True,
            'partner_alias': 'Partner Alias'
        }
        
        result = message_service.build_partner_status_text(status_data, 'en')
        assert result == 'Partner: ✅ (Partner Alias)'
    
    def test_build_status_message_approved(self, message_service):
        """Test building status message for approved user"""
        status_data = {
            'approved': True,
            'partner_names': [],
            'partner_status': {},
            'partner': False
        }
        
        result = message_service.build_status_message(status_data, 'en')
        
        assert 'Approved' in result
        assert 'Partner: Coming alone' in result
    
    def test_build_status_message_waiting_review(self, message_service):
        """Test building status message for user waiting for review"""
        status_data = {
            'approved': False,
            'partner_names': [],
            'partner_status': {},
            'partner': False
        }
        
        result = message_service.build_status_message(status_data, 'en')
        
        assert 'Waiting for review' in result
        assert 'Partner: Coming alone' in result
    
    def test_build_status_message_invalid_language_fallback(self, message_service):
        """Test building status message with invalid language falls back to English"""
        status_data = {
            'approved': True,
            'partner_names': [],
            'partner_status': {},
            'partner': False
        }
        
        result = message_service.build_status_message(status_data, 'invalid_lang')
        
        assert 'Approved' in result
        assert 'Partner: Coming alone' in result
    
    def test_build_status_message_with_partners(self, message_service):
        """Test building status message with partners"""
        status_data = {
            'approved': True,
            'partner_names': ['Partner1', 'Partner2'],
            'partner_status': {
                'registered_partners': ['Partner1'],
                'missing_partners': ['Partner2']
            },
            'partner': False
        }
        
        result = message_service.build_status_message(status_data, 'en')
        
        assert 'Approved' in result
        assert 'Partner: Your partners\' status:' in result
        assert '✅ Partner1 completed the form' in result
        assert '❌ Partner2 hasn\'t completed the form yet' in result
    
    def test_get_message_empty_formatting_params(self, message_service):
        """Test getting message with empty formatting parameters"""
        result = message_service.get_message('en', 'welcome_no_name')
        assert result == 'Welcome!'
    
    def test_get_message_extra_formatting_params(self, message_service):
        """Test getting message with extra formatting parameters (should be ignored)"""
        result = message_service.get_message('en', 'welcome_no_name', extra_param='value')
        assert result == 'Welcome!'
    
    def test_get_message_missing_formatting_params(self, message_service):
        """Test getting message with missing formatting parameters"""
        # The service should handle missing parameters gracefully
        result = message_service.get_message('en', 'welcome_no_name')
        assert result == 'Welcome!'
    
    def test_build_partner_status_text_malformed_data(self, message_service):
        """Test building partner status text with malformed data"""
        status_data = {
            # Missing required fields
        }
        
        # Should handle gracefully without crashing
        result = message_service.build_partner_status_text(status_data, 'en')
        assert 'Partner: Coming alone' in result
    
    def test_build_status_message_malformed_data(self, message_service):
        """Test building status message with malformed data"""
        status_data = {
            # Missing required fields
        }
        
        # Should handle gracefully without crashing
        result = message_service.build_status_message(status_data, 'en')
        assert result is not None
        assert len(result) > 0 