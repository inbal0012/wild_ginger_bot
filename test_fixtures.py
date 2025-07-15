#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test fixtures and mock data for Wild Ginger Telegram Bot tests
Provides comprehensive mock data for different test scenarios
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

class MockData:
    """Mock data for different test scenarios"""
    
    # Sample Google Sheets headers
    SHEET_HEADERS = [
        'Submission ID', 'שם מלא', 'מגיע.ה לבד או באיזון', 'שם הפרטנר',
        'האם תרצו להמשיך בעברית או באנגלית', 'האם השתתפת בעבר באחד מאירועי Wild Ginger',
        'Form Complete', 'Partner Complete', 'Get To Know Complete', 
        'Admin Approved', 'Payment Complete', 'Group Access',
        'Telegram User Id', 'Cancelled', 'Cancellation Date', 
        'Cancellation Reason', 'Last Minute Cancellation'
    ]
    
    # Complete user with all steps done
    COMPLETE_USER_ROW = [
        'SUBM_12345', 'John Doe', 'עם פרטנר', 'Jane Smith',
        'English', 'No', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE',
        '123456789', 'FALSE', '', '', 'FALSE'
    ]
    
    # Incomplete user waiting for partner
    INCOMPLETE_USER_PARTNER_ROW = [
        'SUBM_12346', 'Alice Johnson', 'עם פרטנר', 'Bob Wilson',
        'English', 'No', 'TRUE', 'FALSE', 'TRUE', 'FALSE', 'FALSE', 'FALSE',
        '123456790', 'FALSE', '', '', 'FALSE'
    ]
    
    # User coming alone
    ALONE_USER_ROW = [
        'SUBM_12347', 'Sarah Connor', 'לבד', '',
        'English', 'Yes', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'FALSE', 'FALSE',
        '123456791', 'FALSE', '', '', 'FALSE'
    ]
    
    # Hebrew user
    HEBREW_USER_ROW = [
        'SUBM_12348', 'יוחנן כהן', 'עם פרטנר', 'מרים לוי',
        'עברית', 'No', 'TRUE', 'TRUE', 'FALSE', 'FALSE', 'FALSE', 'FALSE',
        '123456792', 'FALSE', '', '', 'FALSE'
    ]
    
    # Multi-partner user
    MULTI_PARTNER_USER_ROW = [
        'SUBM_12349', 'David Rodriguez', 'עם פרטנר', 'Maria Garcia, Carlos Santos, Ana Lopez',
        'English', 'No', 'TRUE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', 'FALSE',
        '123456793', 'FALSE', '', '', 'FALSE'
    ]
    
    # Cancelled user
    CANCELLED_USER_ROW = [
        'SUBM_12350', 'Emma Thompson', 'עם פרטנר', 'James Wilson',
        'English', 'No', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'FALSE',
        '123456794', 'TRUE', '2024-01-15 14:30:00', 'Sudden illness', 'TRUE'
    ]
    
    # User with missing telegram ID
    NO_TELEGRAM_USER_ROW = [
        'SUBM_12351', 'Robert Brown', 'לבד', '',
        'English', 'No', 'TRUE', 'TRUE', 'TRUE', 'FALSE', 'FALSE', 'FALSE',
        '', 'FALSE', '', '', 'FALSE'
    ]
    
    # Malformed data user (missing fields)
    MALFORMED_USER_ROW = [
        'SUBM_12352', '', 'עם פרטנר', 'Invalid Partner Name',
        '', '', '', '', '', '', '', '', 
        '123456795', '', '', '', ''
    ]
    
    @classmethod
    def get_all_test_rows(cls):
        """Get all test rows for comprehensive testing"""
        return [
            cls.COMPLETE_USER_ROW,
            cls.INCOMPLETE_USER_PARTNER_ROW,
            cls.ALONE_USER_ROW,
            cls.HEBREW_USER_ROW,
            cls.MULTI_PARTNER_USER_ROW,
            cls.CANCELLED_USER_ROW,
            cls.NO_TELEGRAM_USER_ROW,
            cls.MALFORMED_USER_ROW
        ]
    
    @classmethod
    def get_sheet_data(cls):
        """Get mock Google Sheets data"""
        return {
            'headers': cls.SHEET_HEADERS,
            'rows': cls.get_all_test_rows()
        }
    
    @classmethod
    def get_parsed_complete_user(cls):
        """Get parsed complete user data"""
        return {
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': True,
            'paid': True,
            'group_open': True,
            'partner_alias': 'Jane Smith',
            'partner_names': ['Jane Smith'],
            'partner_status': {
                'all_registered': True,
                'registered_partners': ['Jane Smith'],
                'missing_partners': []
            },
            'coming_alone_or_balance': 'עם פרטנר',
            'raw_status': '',
            'telegram_user_id': '123456789',
            'language': 'en',
            'is_returning_participant': False
        }
    
    @classmethod
    def get_parsed_incomplete_user(cls):
        """Get parsed incomplete user data"""
        return {
            'submission_id': 'SUBM_12346',
            'alias': 'Alice Johnson',
            'form': True,
            'partner': False,
            'get_to_know': True,
            'approved': False,
            'paid': False,
            'group_open': False,
            'partner_alias': 'Bob Wilson',
            'partner_names': ['Bob Wilson'],
            'partner_status': {
                'all_registered': False,
                'registered_partners': [],
                'missing_partners': ['Bob Wilson']
            },
            'coming_alone_or_balance': 'עם פרטנר',
            'raw_status': '',
            'telegram_user_id': '123456790',
            'language': 'en',
            'is_returning_participant': False
        }
    
    @classmethod
    def get_parsed_alone_user(cls):
        """Get parsed user coming alone"""
        return {
            'submission_id': 'SUBM_12347',
            'alias': 'Sarah Connor',
            'form': True,
            'partner': True,  # True because no partner needed
            'get_to_know': True,
            'approved': True,
            'paid': False,
            'group_open': False,
            'partner_alias': None,
            'partner_names': [],
            'partner_status': {
                'all_registered': True,
                'registered_partners': [],
                'missing_partners': []
            },
            'coming_alone_or_balance': 'לבד',
            'raw_status': '',
            'telegram_user_id': '123456791',
            'language': 'en',
            'is_returning_participant': True
        }
    
    @classmethod
    def get_parsed_hebrew_user(cls):
        """Get parsed Hebrew user data"""
        return {
            'submission_id': 'SUBM_12348',
            'alias': 'יוחנן כהן',
            'form': True,
            'partner': True,
            'get_to_know': False,
            'approved': False,
            'paid': False,
            'group_open': False,
            'partner_alias': 'מרים לוי',
            'partner_names': ['מרים לוי'],
            'partner_status': {
                'all_registered': True,
                'registered_partners': ['מרים לוי'],
                'missing_partners': []
            },
            'coming_alone_or_balance': 'עם פרטנר',
            'raw_status': '',
            'telegram_user_id': '123456792',
            'language': 'he',
            'is_returning_participant': False
        }
    
    @classmethod
    def get_parsed_multi_partner_user(cls):
        """Get parsed multi-partner user data"""
        return {
            'submission_id': 'SUBM_12349',
            'alias': 'David Rodriguez',
            'form': True,
            'partner': False,
            'get_to_know': False,
            'approved': False,
            'paid': False,
            'group_open': False,
            'partner_alias': 'Maria Garcia, Carlos Santos, Ana Lopez',
            'partner_names': ['Maria Garcia', 'Carlos Santos', 'Ana Lopez'],
            'partner_status': {
                'all_registered': False,
                'registered_partners': ['Maria Garcia'],
                'missing_partners': ['Carlos Santos', 'Ana Lopez']
            },
            'coming_alone_or_balance': 'עם פרטנר',
            'raw_status': '',
            'telegram_user_id': '123456793',
            'language': 'en',
            'is_returning_participant': False
        }

class MockTelegramObjects:
    """Mock Telegram objects for testing"""
    
    @staticmethod
    def create_mock_update(user_id=123456789, first_name="John", language_code="en"):
        """Create a mock Telegram update object"""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = user_id
        update.effective_user.first_name = first_name
        update.effective_user.language_code = language_code
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update
    
    @staticmethod
    def create_mock_context(args=None):
        """Create a mock context object"""
        context = Mock()
        context.args = args or []
        return context
    
    @staticmethod
    def create_mock_bot_application():
        """Create a mock bot application"""
        app = Mock()
        app.bot = Mock()
        app.bot.send_message = AsyncMock()
        return app

class TestScenarios:
    """Test scenario data for different user flows"""
    
    # Happy path scenarios
    HAPPY_PATH_NEW_USER = {
        'description': 'New user completes entire registration flow',
        'initial_state': MockData.get_parsed_incomplete_user(),
        'expected_messages': [
            'Hi Alice Johnson!',
            'Your next steps:',
            'Would you like me to send a reminder to Bob Wilson'
        ]
    }
    
    HAPPY_PATH_RETURNING_USER = {
        'description': 'Returning user with auto-completed get-to-know',
        'initial_state': MockData.get_parsed_alone_user(),
        'expected_messages': [
            'Hi Sarah Connor!',
            'Your registration is complete'
        ]
    }
    
    HAPPY_PATH_HEBREW_USER = {
        'description': 'Hebrew user interface',
        'initial_state': MockData.get_parsed_hebrew_user(),
        'expected_messages': [
            'שלום יוחנן כהן!',
            'אתה יכול להשלים את חלק ההיכרות'
        ]
    }
    
    # Edge case scenarios
    EDGE_CASE_MULTI_PARTNER = {
        'description': 'User with multiple partners, some missing',
        'initial_state': MockData.get_parsed_multi_partner_user(),
        'expected_messages': [
            'Hi David Rodriguez!',
            'Carlos Santos, Ana Lopez',
            "hasn't completed the form yet"
        ]
    }
    
    EDGE_CASE_INVALID_SUBMISSION = {
        'description': 'Invalid submission ID provided',
        'submission_id': 'INVALID_123',
        'expected_messages': [
            'Could not find submission INVALID_123'
        ]
    }
    
    EDGE_CASE_NO_TELEGRAM_ID = {
        'description': 'User without Telegram ID',
        'initial_state': {
            'submission_id': 'SUBM_12351',
            'telegram_user_id': '',
            'alias': 'Robert Brown'
        },
        'expected_messages': [
            'No submission linked to your account'
        ]
    }
    
    EDGE_CASE_MALFORMED_DATA = {
        'description': 'User with malformed data',
        'initial_state': {
            'submission_id': 'SUBM_12352',
            'alias': '',
            'partner_names': None,
            'partner_status': None
        },
        'expected_messages': [
            'Coming alone'  # Fallback behavior
        ]
    }
    
    # Error scenarios
    ERROR_GOOGLE_SHEETS_DOWN = {
        'description': 'Google Sheets service unavailable',
        'mock_error': Exception('Google Sheets API error'),
        'expected_messages': [
            'No submission linked to your account'
        ]
    }
    
    ERROR_TELEGRAM_API_ERROR = {
        'description': 'Telegram API error when sending message',
        'mock_error': Exception('Telegram API error'),
        'expected_behavior': 'Should not crash application'
    }

class MockGoogleSheetsService:
    """Mock Google Sheets service for testing"""
    
    def __init__(self, mock_data=None):
        self.mock_data = mock_data or MockData.get_sheet_data()
        self.updated_cells = {}
        
        # Create proper Google Sheets API mock structure
        # service.spreadsheets().values().get() / .update()
        self.spreadsheets = Mock()
        self.spreadsheets.return_value.values.return_value = self
        
    def get(self, spreadsheetId, range):
        """Mock getting values from sheet"""
        result = Mock()
        result.execute.return_value = {'values': [self.mock_data['headers']] + self.mock_data['rows']}
        return result
    
    def update(self, spreadsheetId, range, valueInputOption, body):
        """Mock updating values in sheet"""
        self.updated_cells[range] = body['values'][0][0]
        result = Mock()
        result.execute.return_value = {'updatedCells': 1}
        return result
    
    def get_updated_cells(self):
        """Get cells that were updated during testing"""
        return self.updated_cells

# Pytest fixtures
@pytest.fixture
def mock_complete_user():
    """Fixture for complete user data"""
    return MockData.get_parsed_complete_user()

@pytest.fixture
def mock_incomplete_user():
    """Fixture for incomplete user data"""
    return MockData.get_parsed_incomplete_user()

@pytest.fixture
def mock_alone_user():
    """Fixture for user coming alone"""
    return MockData.get_parsed_alone_user()

@pytest.fixture
def mock_hebrew_user():
    """Fixture for Hebrew user"""
    return MockData.get_parsed_hebrew_user()

@pytest.fixture
def mock_multi_partner_user():
    """Fixture for multi-partner user"""
    return MockData.get_parsed_multi_partner_user()

@pytest.fixture
def mock_update():
    """Fixture for mock Telegram update"""
    return MockTelegramObjects.create_mock_update()

@pytest.fixture
def mock_context():
    """Fixture for mock context"""
    return MockTelegramObjects.create_mock_context()

@pytest.fixture
def mock_bot_application():
    """Fixture for mock bot application"""
    return MockTelegramObjects.create_mock_bot_application()

@pytest.fixture
def mock_sheets_service():
    """Fixture for mock Google Sheets service"""
    return MockGoogleSheetsService()

# Test data validation
def validate_test_data():
    """Validate that test data is consistent"""
    data = MockData.get_sheet_data()
    
    # Check that all rows have the same number of columns as headers
    for i, row in enumerate(data['rows']):
        assert len(row) == len(data['headers']), f"Row {i} has {len(row)} columns, expected {len(data['headers'])}"
    
    # Check that submission IDs are unique
    submission_ids = [row[0] for row in data['rows']]
    assert len(submission_ids) == len(set(submission_ids)), "Duplicate submission IDs found"
    
    print("Test data validation passed")

if __name__ == '__main__':
    validate_test_data()
    print("Test fixtures initialized successfully") 