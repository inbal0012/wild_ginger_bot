#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test fixtures and mock data for Wild Ginger Telegram Bot - Microservice Architecture
Provides comprehensive mock data and fixtures for testing the new services
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

class MockData:
    """Mock data for different test scenarios - Updated for microservices"""
    
    # Sample Google Sheets headers
    SHEET_HEADERS = [
        'Submission ID', 'שם מלא', 'מגיע.ה לבד או באיזון', 'שם הפרטנר',
        'האם תרצו להמשיך בעברית או באנגלית', 'האם השתתפת בעבר באחד מאירועי Wild Ginger',
        'Form Complete', 'Partner Complete', 'Get To Know Complete', 
        'Admin Approved', 'Payment Complete', 'Group Access',
        'Telegram User Id', 'Cancelled', 'Cancellation Date', 
        'Cancellation Reason', 'Last Minute Cancellation', 'Get To Know Response'
    ]
    
    # Complete user with all steps done
    COMPLETE_USER_ROW = [
        'SUBM_12345', 'John Doe', 'עם פרטנר', 'Jane Smith',
        'English', 'No', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE',
        '123456789', 'FALSE', '', '', 'FALSE', 
        'I am a software developer with experience in community events. I love cooking and playing guitar.'
    ]
    
    # Incomplete user waiting for partner
    INCOMPLETE_USER_PARTNER_ROW = [
        'SUBM_12346', 'Alice Johnson', 'עם פרטנר', 'Bob Wilson',
        'English', 'No', 'TRUE', 'FALSE', 'TRUE', 'FALSE', 'FALSE', 'FALSE',
        '123456790', 'FALSE', '', '', 'FALSE', 
        'I work in marketing and enjoy hiking and photography.'
    ]
    
    # User coming alone
    ALONE_USER_ROW = [
        'SUBM_12347', 'Sarah Connor', 'לבד', '',
        'English', 'Yes', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'FALSE', 'FALSE',
        '123456791', 'FALSE', '', '', 'FALSE', 
        'I am a teacher and love reading sci-fi novels. I have attended similar events before.'
    ]
    
    # Hebrew user
    HEBREW_USER_ROW = [
        'SUBM_12348', 'יוחנן כהן', 'עם פרטנר', 'מרים לוי',
        'עברית', 'No', 'TRUE', 'TRUE', 'FALSE', 'FALSE', 'FALSE', 'FALSE',
        '123456792', 'FALSE', '', '', 'FALSE', 
        'אני מהנדס תוכנה ואוהב לבשל. זה הפעם הראשונה שלי באירוע כזה.'
    ]
    
    # Cancelled user
    CANCELLED_USER_ROW = [
        'SUBM_12349', 'Mike Johnson', 'לבד', '',
        'English', 'No', 'TRUE', 'TRUE', 'TRUE', 'FALSE', 'FALSE', 'FALSE',
        '123456793', 'TRUE', '2024-01-15 10:30:00', 'sudden illness', 'FALSE',
        'I am a designer who loves outdoor activities.'
    ]
    
    # Multi-partner user
    MULTI_PARTNER_USER_ROW = [
        'SUBM_12350', 'Group Leader', 'עם פרטנר', 'Partner1, Partner2, Partner3',
        'English', 'Yes', 'TRUE', 'FALSE', 'TRUE', 'FALSE', 'FALSE', 'FALSE',
        '123456794', 'FALSE', '', '', 'FALSE',
        'I organize community events and bring multiple partners to activities.'
    ]
    
    @classmethod
    def get_parsed_complete_user(cls):
        """Get parsed data for a complete user"""
        return {
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'partner_type': 'עם פרטנר',
            'partner_alias': 'Jane Smith',
            'language': 'en',
            'is_returning_participant': False,
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': True,
            'paid': True,
            'group_open': True,
            'telegram_user_id': '123456789',
            'cancelled': False,
            'cancellation_date': '',
            'cancellation_reason': '',
            'last_minute_cancellation': False,
            'get_to_know_response': 'I am a software developer with experience in community events. I love cooking and playing guitar.',
            'partner_names': ['Jane Smith'],
            'partner_status': {
                'registered_partners': ['Jane Smith'],
                'missing_partners': [],
                'total_partners': 1,
                'completed_partners': 1
            }
        }
    
    @classmethod
    def get_parsed_incomplete_user(cls):
        """Get parsed data for an incomplete user (waiting for partner)"""
        return {
            'submission_id': 'SUBM_12346',
            'alias': 'Alice Johnson',
            'partner_type': 'עם פרטנר',
            'partner_alias': 'Bob Wilson',
            'language': 'en',
            'is_returning_participant': False,
            'form': True,
            'partner': False,
            'get_to_know': True,
            'approved': False,
            'paid': False,
            'group_open': False,
            'telegram_user_id': '123456790',
            'cancelled': False,
            'cancellation_date': '',
            'cancellation_reason': '',
            'last_minute_cancellation': False,
            'get_to_know_response': 'I work in marketing and enjoy hiking and photography.',
            'partner_names': ['Bob Wilson'],
            'partner_status': {
                'registered_partners': [],
                'missing_partners': ['Bob Wilson'],
                'total_partners': 1,
                'completed_partners': 0
            }
        }
    
    @classmethod
    def get_parsed_alone_user(cls):
        """Get parsed data for a user coming alone"""
        return {
            'submission_id': 'SUBM_12347',
            'alias': 'Sarah Connor',
            'partner_type': 'לבד',
            'partner_alias': '',
            'language': 'en',
            'is_returning_participant': True,
            'form': True,
            'partner': True,  # True for alone users
            'get_to_know': True,
            'approved': True,
            'paid': False,
            'group_open': False,
            'telegram_user_id': '123456791',
            'cancelled': False,
            'cancellation_date': '',
            'cancellation_reason': '',
            'last_minute_cancellation': False,
            'get_to_know_response': 'I am a teacher and love reading sci-fi novels. I have attended similar events before.',
            'partner_names': [],
            'partner_status': {
                'registered_partners': [],
                'missing_partners': [],
                'total_partners': 0,
                'completed_partners': 0
            }
        }
    
    @classmethod
    def get_parsed_hebrew_user(cls):
        """Get parsed data for a Hebrew-speaking user"""
        return {
            'submission_id': 'SUBM_12348',
            'alias': 'יוחנן כהן',
            'partner_type': 'עם פרטנר',
            'partner_alias': 'מרים לוי',
            'language': 'he',
            'is_returning_participant': False,
            'form': True,
            'partner': True,
            'get_to_know': False,
            'approved': False,
            'paid': False,
            'group_open': False,
            'telegram_user_id': '123456792',
            'cancelled': False,
            'cancellation_date': '',
            'cancellation_reason': '',
            'last_minute_cancellation': False,
            'get_to_know_response': 'אני מהנדס תוכנה ואוהב לבשל. זה הפעם הראשונה שלי באירוע כזה.',
            'partner_names': ['מרים לוי'],
            'partner_status': {
                'registered_partners': ['מרים לוי'],
                'missing_partners': [],
                'total_partners': 1,
                'completed_partners': 1
            }
        }
    
    @classmethod
    def get_parsed_cancelled_user(cls):
        """Get parsed data for a cancelled user"""
        return {
            'submission_id': 'SUBM_12349',
            'alias': 'Mike Johnson',
            'partner_type': 'לבד',
            'partner_alias': '',
            'language': 'en',
            'is_returning_participant': False,
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': False,
            'paid': False,
            'group_open': False,
            'telegram_user_id': '123456793',
            'cancelled': True,
            'cancellation_date': '2024-01-15 10:30:00',
            'cancellation_reason': 'sudden illness',
            'last_minute_cancellation': False,
            'get_to_know_response': 'I am a designer who loves outdoor activities.',
            'partner_names': [],
            'partner_status': {
                'registered_partners': [],
                'missing_partners': [],
                'total_partners': 0,
                'completed_partners': 0
            }
        }
    
    @classmethod
    def get_parsed_multi_partner_user(cls):
        """Get parsed data for a user with multiple partners"""
        return {
            'submission_id': 'SUBM_12350',
            'alias': 'Group Leader',
            'partner_type': 'עם פרטנר',
            'partner_alias': 'Partner1, Partner2, Partner3',
            'language': 'en',
            'is_returning_participant': True,
            'form': True,
            'partner': False,
            'get_to_know': True,
            'approved': False,
            'paid': False,
            'group_open': False,
            'telegram_user_id': '123456794',
            'cancelled': False,
            'cancellation_date': '',
            'cancellation_reason': '',
            'last_minute_cancellation': False,
            'get_to_know_response': 'I organize community events and bring multiple partners to activities.',
            'partner_names': ['Partner1', 'Partner2', 'Partner3'],
            'partner_status': {
                'registered_partners': ['Partner1'],
                'missing_partners': ['Partner2', 'Partner3'],
                'total_partners': 3,
                'completed_partners': 1
            }
        }


class MockTelegramObjects:
    """Mock Telegram objects for testing"""
    
    @staticmethod
    def create_mock_update(user_id=123456789, message_text="", username="testuser", 
                          language_code="en", first_name="TestUser"):
        """Create a mock Telegram Update object"""
        update = Mock()
        
        # Mock effective_user
        update.effective_user = Mock()
        update.effective_user.id = user_id
        update.effective_user.username = username
        update.effective_user.first_name = first_name
        update.effective_user.language_code = language_code
        
        # Mock message
        update.message = Mock()
        update.message.text = message_text
        update.message.reply_text = AsyncMock()
        update.message.edit_text = AsyncMock()
        
        return update
    
    @staticmethod
    def create_mock_context(args=None, user_data=None, chat_data=None, bot_data=None):
        """Create a mock Telegram Context object"""
        context = Mock()
        context.args = args or []
        context.user_data = user_data or {}
        context.chat_data = chat_data or {}
        context.bot_data = bot_data or {}
        
        # Mock bot
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        
        return context


class MockServiceResponses:
    """Mock responses from various services"""
    
    @staticmethod
    def get_successful_sheets_response():
        """Get a successful Google Sheets API response"""
        return {
            'values': [
                MockData.SHEET_HEADERS,
                MockData.COMPLETE_USER_ROW,
                MockData.INCOMPLETE_USER_PARTNER_ROW,
                MockData.ALONE_USER_ROW
            ]
        }
    
    @staticmethod
    def get_empty_sheets_response():
        """Get an empty Google Sheets API response"""
        return {'values': []}
    
    @staticmethod
    def get_successful_update_response():
        """Get a successful Google Sheets update response"""
        return {
            'spreadsheetId': 'test_spreadsheet_id',
            'updatedRows': 1,
            'updatedColumns': 1,
            'updatedCells': 1
        }


class TestScenarios:
    """Test scenarios for different user flows"""
    
    @staticmethod
    def new_user_registration():
        """Test scenario for new user registration"""
        return {
            'name': 'New User Registration',
            'description': 'Complete flow from start to group access',
            'user_data': MockData.get_parsed_incomplete_user(),
            'expected_steps': [
                'form_complete',
                'partner_complete', 
                'get_to_know_complete',
                'admin_approved',
                'payment_complete',
                'group_access'
            ]
        }
    
    @staticmethod
    def partner_reminder_flow():
        """Test scenario for partner reminder flow"""
        return {
            'name': 'Partner Reminder Flow',
            'description': 'User sends reminder to missing partners',
            'user_data': MockData.get_parsed_multi_partner_user(),
            'missing_partners': ['Partner2', 'Partner3'],
            'expected_reminders': 2
        }
    
    @staticmethod
    def admin_approval_flow():
        """Test scenario for admin approval workflow"""
        return {
            'name': 'Admin Approval Flow',
            'description': 'Admin reviews and approves registration',
            'user_data': MockData.get_parsed_incomplete_user(),
            'admin_action': 'approve',
            'expected_notifications': ['user_notification', 'admin_notification']
        }
    
    @staticmethod
    def cancellation_flow():
        """Test scenario for user cancellation"""
        return {
            'name': 'User Cancellation Flow',
            'description': 'User cancels registration with reason',
            'user_data': MockData.get_parsed_complete_user(),
            'cancellation_reason': 'sudden illness',
            'is_last_minute': True
        }
    
    @staticmethod
    def hebrew_user_flow():
        """Test scenario for Hebrew-speaking user"""
        return {
            'name': 'Hebrew User Flow',
            'description': 'Complete flow in Hebrew language',
            'user_data': MockData.get_parsed_hebrew_user(),
            'language': 'he',
            'expected_messages_in_hebrew': True
        }


class MockBotApplication:
    """Mock bot application for service testing"""
    
    def __init__(self):
        self.bot = Mock()
        self.bot.send_message = AsyncMock()
        self.handlers = []
    
    def add_handler(self, handler):
        """Mock handler registration"""
        self.handlers.append(handler)
    
    async def start(self):
        """Mock bot start"""
        pass
    
    async def stop(self):
        """Mock bot stop"""
        pass


@pytest.fixture
def mock_sheets_service():
    """Fixture for mocked SheetsService"""
    mock = Mock()
    mock.get_sheet_data.return_value = {
        'headers': MockData.SHEET_HEADERS,
        'rows': [
            MockData.COMPLETE_USER_ROW,
            MockData.INCOMPLETE_USER_PARTNER_ROW
        ]
    }
    mock.find_submission_by_id.return_value = MockData.get_parsed_complete_user()
    mock.find_submission_by_telegram_id.return_value = MockData.get_parsed_complete_user()
    mock.update_step_status = AsyncMock(return_value=True)
    mock.get_all_registrations = AsyncMock(return_value=[
        MockData.get_parsed_complete_user(),
        MockData.get_parsed_incomplete_user()
    ])
    return mock


@pytest.fixture
def mock_message_service():
    """Fixture for mocked MessageService"""
    mock = Mock()
    mock.get_message.return_value = "Test message"
    mock.build_status_message.return_value = "📋 Form: ✅\n🤝 Partner: ✅"
    return mock


@pytest.fixture
def mock_admin_service():
    """Fixture for mocked AdminService"""
    mock = Mock()
    mock.is_admin.return_value = True
    mock.get_dashboard_stats = AsyncMock(return_value={
        'stats': {'total': 2, 'pending_approval': 1},
        'pending_approvals': []
    })
    mock.approve_registration = AsyncMock(return_value={
        'success': True,
        'message': 'Registration approved'
    })
    return mock


@pytest.fixture
def mock_bot_application():
    """Fixture for mocked bot application"""
    return MockBotApplication()


def validate_service_integration():
    """Validate that services can work together"""
    # This could be used to run integration validation
    pass


if __name__ == "__main__":
    # Run fixture validation
    print("🧪 Validating test fixtures for microservice architecture...")
    
    # Test mock data creation
    complete_user = MockData.get_parsed_complete_user()
    print(f"✅ Complete user mock: {complete_user['alias']}")
    
    incomplete_user = MockData.get_parsed_incomplete_user()
    print(f"✅ Incomplete user mock: {incomplete_user['alias']}")
    
    # Test Telegram object mocks
    update = MockTelegramObjects.create_mock_update()
    print(f"✅ Mock update object: {update.effective_user.id}")
    
    context = MockTelegramObjects.create_mock_context(['arg1', 'arg2'])
    print(f"✅ Mock context object: {context.args}")
    
    print("🎉 All fixtures validated successfully!") 