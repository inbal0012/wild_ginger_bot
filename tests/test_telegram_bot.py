#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive unit tests for the Wild Ginger Telegram Bot
Testing both happy path and edge cases with proper mocking
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot_polling import (
    get_message, 
    get_status_message, 
    build_partner_status_text,
    parse_multiple_partners,
    check_partner_registration_status,
    find_submission_by_id,
    find_submission_by_telegram_id,
    update_telegram_user_id,
    update_form_complete,
    update_cancellation_status,
    parse_submission_row,
    get_column_indices,
    column_index_to_letter,
    ReminderScheduler,
    start, status, help_command, cancel_registration, remind_partner,
    user_submissions,
    MESSAGES
)

class TestMessageLocalization:
    """Test multilingual message functionality"""
    
    def test_get_message_english(self):
        """Test getting English messages"""
        message = get_message('en', 'welcome', name="John")
        assert "Hi John!" in message
        assert "registration assistant" in message
        
    def test_get_message_hebrew(self):
        """Test getting Hebrew messages"""
        message = get_message('he', 'welcome', name="יוחנן")
        assert "שלום יוחנן!" in message
        assert "עוזר הרשמה" in message
        
    def test_get_message_fallback_to_english(self):
        """Test fallback to English when key not found in Hebrew"""
        # Test with non-existent key
        message = get_message('he', 'non_existent_key')
        assert "Message key 'non_existent_key' not found" in message
        
    def test_get_message_with_formatting(self):
        """Test message formatting with parameters"""
        message = get_message('en', 'submission_not_found', submission_id="TEST_123")
        assert "TEST_123" in message
        assert "Could not find submission" in message
        
    def test_get_message_invalid_language(self):
        """Test handling of invalid language codes"""
        message = get_message('invalid', 'welcome', name="Test")
        assert "Hi Test!" in message  # Should fallback to English

class TestPartnerManagement:
    """Test partner-related functionality"""
    
    def test_parse_single_partner(self):
        """Test parsing a single partner name"""
        result = parse_multiple_partners("John Doe")
        assert result == ["John Doe"]
        
    def test_parse_multiple_partners_comma(self):
        """Test parsing multiple partners separated by comma"""
        result = parse_multiple_partners("John Doe, Jane Smith")
        assert result == ["John Doe", "Jane Smith"]
        
    def test_parse_multiple_partners_hebrew_connector(self):
        """Test parsing with Hebrew connector"""
        result = parse_multiple_partners("יוחנן ו מרים")
        assert result == ["יוחנן", "מרים"]
        
    def test_parse_multiple_partners_mixed_separators(self):
        """Test parsing with mixed separators"""
        result = parse_multiple_partners("John, Jane & Bob + Alice")
        assert len(result) == 4
        assert "John" in result
        assert "Jane" in result
        assert "Bob" in result
        assert "Alice" in result
        
    def test_parse_empty_partner_string(self):
        """Test parsing empty or None partner string"""
        assert parse_multiple_partners("") == []
        assert parse_multiple_partners(None) == []
        assert parse_multiple_partners("   ") == []
        
    def test_parse_partners_with_duplicates(self):
        """Test parsing removes duplicates"""
        result = parse_multiple_partners("John, John, Jane")
        assert result == ["John", "Jane"]

class TestStatusMessageGeneration:
    """Test status message generation"""
    
    def test_build_partner_status_single_partner_complete(self):
        """Test partner status with single complete partner"""
        status_data = {
            'partner_names': ['John Doe'],
            'partner_status': {'registered_partners': ['John Doe'], 'missing_partners': []},
            'partner': True,
            'partner_alias': 'John Doe'
        }
        result = build_partner_status_text(status_data, 'en')
        assert "Partner: ✅" in result
        
    def test_build_partner_status_coming_alone(self):
        """Test partner status when coming alone"""
        status_data = {
            'partner_names': [],
            'partner_status': {},
            'partner': False,
            'partner_alias': None
        }
        result = build_partner_status_text(status_data, 'en')
        assert "Coming alone" in result
        
    def test_build_partner_status_hebrew_coming_alone(self):
        """Test Hebrew partner status when coming alone"""
        status_data = {
            'partner_names': [],
            'partner_status': {},
            'partner': False,
            'partner_alias': None
        }
        result = build_partner_status_text(status_data, 'he')
        assert "מגיע.ה לבד" in result
        
    def test_build_partner_status_multiple_partners_mixed(self):
        """Test multiple partners with some registered, some missing"""
        status_data = {
            'partner_names': ['John Doe', 'Jane Smith', 'Bob Wilson'],
            'partner_status': {
                'registered_partners': ['John Doe', 'Jane Smith'],
                'missing_partners': ['Bob Wilson']
            },
            'partner': False,
            'partner_alias': 'John Doe, Jane Smith, Bob Wilson'
        }
        result = build_partner_status_text(status_data, 'en')
        assert "John Doe, Jane Smith completed" in result
        assert "Bob Wilson hasn't completed" in result
        
    def test_get_status_message_complete_flow(self):
        """Test complete status message generation"""
        status_data = {
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': True,
            'paid': True,
            'group_open': True,
            'language': 'en',
            'partner_names': ['John Doe'],
            'partner_status': {'registered_partners': ['John Doe'], 'missing_partners': []},
            'partner_alias': 'John Doe'
        }
        result = get_status_message(status_data)
        assert "Form: ✅" in result
        assert "Partner: ✅" in result
        assert "Get-to-know: ✅" in result
        assert "Status: ✅ Approved" in result
        assert "Payment: ✅" in result
        assert "Group: ✅" in result

class TestGoogleSheetsIntegration:
    """Test Google Sheets related functions"""
    
    def test_column_index_to_letter(self):
        """Test column index to letter conversion"""
        assert column_index_to_letter(0) == 'A'
        assert column_index_to_letter(1) == 'B'
        assert column_index_to_letter(25) == 'Z'
        assert column_index_to_letter(26) == 'AA'
        assert column_index_to_letter(27) == 'AB'
        
    def test_get_column_indices(self):
        """Test getting column indices from headers"""
        headers = [
            'Submission ID', 'שם מלא', 'שם הפרטנר', 
            'Form Complete', 'Partner Complete', 'Admin Approved',
            'Payment Complete', 'Group Access', 'Telegram User Id'
        ]
        indices = get_column_indices(headers)
        
        assert indices['submission_id'] == 0
        assert indices['full_name'] == 1
        assert indices['partner_name'] == 2
        assert indices['form_complete'] == 3
        assert indices['partner_complete'] == 4
        assert indices['admin_approved'] == 5
        assert indices['payment_complete'] == 6
        assert indices['group_access'] == 7
        assert indices['telegram_user_id'] == 8
        
    def test_parse_submission_row_complete(self):
        """Test parsing a complete submission row"""
        row = [
            'SUBM_12345', 'John Doe', 'Jane Smith', 
            'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 
            '123456789', 'English', 'לבד', 'FALSE'
        ]
        column_indices = {
            'submission_id': 0, 'full_name': 1, 'partner_name': 2,
            'form_complete': 3, 'partner_complete': 4, 'admin_approved': 5,
            'payment_complete': 6, 'group_access': 7, 'telegram_user_id': 8,
            'language_preference': 9, 'coming_alone_or_balance': 10,
            'returning_participant': 11
        }
        
        result = parse_submission_row(row, column_indices)
        
        assert result['submission_id'] == 'SUBM_12345'
        assert result['alias'] == 'John Doe'
        assert result['form'] == True
        assert result['partner'] == True
        assert result['approved'] == True
        assert result['paid'] == True
        assert result['group_open'] == True
        assert result['telegram_user_id'] == '123456789'
        assert result['language'] == 'en'
        
    def test_parse_submission_row_incomplete(self):
        """Test parsing an incomplete submission row"""
        row = [
            'SUBM_12345', 'John Doe', '', 
            'TRUE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', 
            '', '', 'לבד'
        ]
        column_indices = {
            'submission_id': 0, 'full_name': 1, 'partner_name': 2,
            'form_complete': 3, 'partner_complete': 4, 'admin_approved': 5,
            'payment_complete': 6, 'group_access': 7, 'telegram_user_id': 8,
            'language_preference': 9, 'coming_alone_or_balance': 10
        }
        
        result = parse_submission_row(row, column_indices)
        
        assert result['submission_id'] == 'SUBM_12345'
        assert result['form'] == True
        assert result['partner'] == False
        assert result['approved'] == False
        assert result['paid'] == False
        assert result['group_open'] == False
        assert result['partner_alias'] == None

class TestCommandHandlers:
    """Test Telegram command handlers"""
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update object"""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.first_name = "John"
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update
        
    @pytest.fixture
    def mock_context(self):
        """Create a mock context object"""
        context = Mock()
        context.args = []
        return context
        
    @pytest.mark.asyncio
    async def test_start_command_with_submission_id(self, mock_update, mock_context):
        """Test /start command with submission ID"""
        mock_context.args = ['SUBM_12345']
        
        mock_status_data = {
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'language': 'en',
            'form': True,
            'partner': False,
            'get_to_know': False,
            'approved': False,
            'paid': False,
            'group_open': False,
            'is_returning_participant': False
        }
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data), \
             patch('telegram_bot_polling.update_telegram_user_id', return_value=True), \
             patch('telegram_bot_polling.update_form_complete', return_value=True), \
             patch('telegram_bot_polling.continue_conversation', new_callable=AsyncMock) as mock_continue:
            
            await start(mock_update, mock_context)
            
            # Verify welcome message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Hi John Doe!" in call_args
            
            # Verify continue conversation was called
            mock_continue.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_start_command_no_submission_id(self, mock_update, mock_context):
        """Test /start command without submission ID"""
        mock_context.args = []
        
        await start(mock_update, mock_context)
        
        # Verify welcome message for no submission was sent
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Hi there!" in call_args
        assert "registration assistant" in call_args
        
    @pytest.mark.asyncio
    async def test_start_command_invalid_submission_id(self, mock_update, mock_context):
        """Test /start command with invalid submission ID"""
        mock_context.args = ['INVALID_ID']
        
        with patch('telegram_bot_polling.get_status_data', return_value=None):
            await start(mock_update, mock_context)
            
            # Verify error message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Could not find submission" in call_args
            assert "INVALID_ID" in call_args
            
    @pytest.mark.asyncio
    async def test_status_command_with_linked_submission(self, mock_update, mock_context):
        """Test /status command with linked submission"""
        user_id = str(mock_update.effective_user.id)
        user_submissions[user_id] = 'SUBM_12345'
        
        mock_status_data = {
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'language': 'en',
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': True,
            'paid': False,
            'group_open': False,
            'partner_names': ['Jane Smith'],
            'partner_status': {'registered_partners': ['Jane Smith'], 'missing_partners': []},
            'partner_alias': 'Jane Smith'
        }
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data):
            await status(mock_update, mock_context)
            
            # Verify status message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Form: ✅" in call_args
            assert "Partner: ✅" in call_args
            assert "Payment: ❌" in call_args
            
    @pytest.mark.asyncio
    async def test_status_command_no_submission_linked(self, mock_update, mock_context):
        """Test /status command with no submission linked"""
        user_id = str(mock_update.effective_user.id)
        if user_id in user_submissions:
            del user_submissions[user_id]
        
        with patch('telegram_bot_polling.get_status_data', return_value=None):
            await status(mock_update, mock_context)
            
            # Verify no submission linked message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "No submission linked" in call_args
            
    @pytest.mark.asyncio
    async def test_help_command(self, mock_update, mock_context):
        """Test /help command"""
        user_id = str(mock_update.effective_user.id)
        user_submissions[user_id] = 'SUBM_12345'
        
        mock_status_data = {
            'language': 'en'
        }
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data):
            await help_command(mock_update, mock_context)
            
            # Verify help message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Wild Ginger Bot Help" in call_args
            assert "Available commands:" in call_args
            
    @pytest.mark.asyncio
    async def test_cancel_command_with_reason(self, mock_update, mock_context):
        """Test /cancel command with reason"""
        mock_context.args = ['sudden', 'illness']
        user_id = str(mock_update.effective_user.id)
        user_submissions[user_id] = 'SUBM_12345'
        
        mock_status_data = {
            'submission_id': 'SUBM_12345',
            'language': 'en',
            'paid': False  # Not last minute
        }
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data), \
             patch('telegram_bot_polling.update_cancellation_status', return_value=True):
            
            await cancel_registration(mock_update, mock_context)
            
            # Verify cancellation message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "cancelled" in call_args
            assert "sudden illness" in call_args
            
    @pytest.mark.asyncio
    async def test_cancel_command_no_reason(self, mock_update, mock_context):
        """Test /cancel command without reason"""
        mock_context.args = []
        user_id = str(mock_update.effective_user.id)
        user_submissions[user_id] = 'SUBM_12345'
        
        mock_status_data = {
            'submission_id': 'SUBM_12345',
            'language': 'en'
        }
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data):
            await cancel_registration(mock_update, mock_context)
            
            # Verify reason request message was sent
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "provide a reason" in call_args

class TestReminderScheduler:
    """Test the reminder scheduler functionality"""
    
    @pytest.fixture
    def mock_bot_application(self):
        """Create a mock bot application"""
        app = Mock()
        app.bot = Mock()
        app.bot.send_message = AsyncMock()
        return app
        
    @pytest.fixture
    def reminder_scheduler(self, mock_bot_application):
        """Create a reminder scheduler instance"""
        return ReminderScheduler(mock_bot_application)
        
    def test_quick_completion_check_complete_user(self, reminder_scheduler):
        """Test quick completion check for complete user"""
        row = ['SUBM_12345', 'John Doe', 'Jane Smith', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'TRUE', '123456789']
        column_indices = {
            'submission_id': 0, 'full_name': 1, 'partner_name': 2,
            'form_complete': 3, 'partner_complete': 4, 'admin_approved': 5,
            'payment_complete': 6, 'group_access': 7, 'telegram_user_id': 8
        }
        
        result = reminder_scheduler.quick_completion_check(row, column_indices)
        
        assert result['submission_id'] == 'SUBM_12345'
        assert result['telegram_user_id'] == '123456789'
        assert result['needs_reminders'] == False
        
    def test_quick_completion_check_incomplete_user(self, reminder_scheduler):
        """Test quick completion check for incomplete user"""
        row = ['SUBM_12345', 'John Doe', 'Jane Smith', 'TRUE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', '123456789']
        column_indices = {
            'submission_id': 0, 'full_name': 1, 'partner_name': 2,
            'form_complete': 3, 'partner_complete': 4, 'admin_approved': 5,
            'payment_complete': 6, 'group_access': 7, 'telegram_user_id': 8
        }
        
        result = reminder_scheduler.quick_completion_check(row, column_indices)
        
        assert result['submission_id'] == 'SUBM_12345'
        assert result['telegram_user_id'] == '123456789'
        assert result['needs_reminders'] == True
        
    @pytest.mark.asyncio
    async def test_send_automatic_partner_reminder(self, reminder_scheduler):
        """Test sending automatic partner reminder"""
        user_data = {
            'submission_id': 'SUBM_12345',
            'telegram_user_id': '123456789',
            'language': 'en',
            'alias': 'John Doe'
        }
        missing_partners = ['Jane Smith']
        
        with patch('telegram_bot_polling.log_reminder_sent', new_callable=AsyncMock) as mock_log:
            await reminder_scheduler.send_automatic_partner_reminder(user_data, missing_partners)
            
            # Verify message was sent
            reminder_scheduler.bot.bot.send_message.assert_called_once()
            call_args = reminder_scheduler.bot.bot.send_message.call_args
            assert call_args[1]['chat_id'] == '123456789'
            assert 'Jane Smith' in call_args[1]['text']
            
            # Verify reminder was logged
            mock_log.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_send_automatic_payment_reminder(self, reminder_scheduler):
        """Test sending automatic payment reminder"""
        user_data = {
            'submission_id': 'SUBM_12345',
            'telegram_user_id': '123456789',
            'language': 'en',
            'alias': 'John Doe'
        }
        
        with patch('telegram_bot_polling.log_reminder_sent', new_callable=AsyncMock) as mock_log:
            await reminder_scheduler.send_automatic_payment_reminder(user_data)
            
            # Verify message was sent
            reminder_scheduler.bot.bot.send_message.assert_called_once()
            call_args = reminder_scheduler.bot.bot.send_message.call_args
            assert call_args[1]['chat_id'] == '123456789'
            assert 'payment' in call_args[1]['text'].lower()
            
            # Verify reminder was logged
            mock_log.assert_called_once()

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_parse_submission_row_empty_row(self):
        """Test parsing empty row"""
        row = []
        column_indices = {'submission_id': 0}
        
        result = parse_submission_row(row, column_indices)
        
        assert result['submission_id'] == ''
        assert result['alias'] == ''
        assert result['form'] == False
        
    def test_parse_submission_row_missing_columns(self):
        """Test parsing row with missing columns"""
        row = ['SUBM_12345']
        column_indices = {'submission_id': 0, 'full_name': 5}  # Column 5 doesn't exist
        
        result = parse_submission_row(row, column_indices)
        
        assert result['submission_id'] == 'SUBM_12345'
        assert result['alias'] == ''  # Should fallback to default
        
    def test_parse_multiple_partners_special_characters(self):
        """Test parsing partners with special characters"""
        result = parse_multiple_partners("João & María, José")
        assert len(result) == 3
        assert "João" in result
        assert "María" in result
        assert "José" in result
        
    def test_get_message_missing_parameters(self):
        """Test getting message with missing parameters"""
        # This should not raise an error, just return message without formatting
        message = get_message('en', 'welcome')  # Missing 'name' parameter
        assert isinstance(message, str)
        assert "registration assistant" in message
        
    def test_column_index_to_letter_edge_cases(self):
        """Test column index conversion edge cases"""
        # Test boundary conditions
        assert column_index_to_letter(51) == 'AZ'
        assert column_index_to_letter(701) == 'ZZ'
        
    def test_build_partner_status_malformed_data(self):
        """Test partner status building with malformed data"""
        status_data = {
            'partner_names': None,  # Malformed
            'partner_status': None,  # Malformed
            'partner': False,
            'partner_alias': None
        }
        
        result = build_partner_status_text(status_data, 'en')
        assert "Coming alone" in result
        
    @pytest.mark.asyncio
    async def test_command_handler_with_bot_error(self):
        """Test command handler when bot encounters an error"""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock(side_effect=Exception("Bot error"))
        
        context = Mock()
        context.args = []
        
        # This should not crash the application
        with patch('telegram_bot_polling.get_status_data', return_value=None):
            try:
                await help_command(update, context)
            except Exception as e:
                assert "Bot error" in str(e)

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v']) 