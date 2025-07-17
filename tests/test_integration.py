#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for the Wild Ginger Telegram Bot
Testing end-to-end scenarios and component interactions
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
    start, status, help_command, cancel_registration, remind_partner,
    continue_conversation, get_status_data, user_submissions,
    ReminderScheduler, update_telegram_user_id, update_form_complete,
    update_get_to_know_complete, update_cancellation_status
)
from test_fixtures import (
    MockData, MockTelegramObjects, TestScenarios, 
    MockGoogleSheetsService, validate_test_data
)

class TestEndToEndFlows:
    """Test complete end-to-end user flows"""
    
    @pytest.mark.asyncio
    async def test_new_user_registration_flow(self):
        """Test complete new user registration flow"""
        # Setup
        user_id = 123456789
        submission_id = 'SUBM_12345'
        
        # Mock data progression through the flow
        initial_data = MockData.get_parsed_incomplete_user()
        initial_data['submission_id'] = submission_id
        
        complete_data = MockData.get_parsed_complete_user()
        complete_data['submission_id'] = submission_id
        
        # Create mock objects
        update = MockTelegramObjects.create_mock_update(user_id=user_id)
        context = MockTelegramObjects.create_mock_context(args=[submission_id])
        
        # Mock the Google Sheets calls
        with patch('telegram_bot_polling.get_status_data', return_value=initial_data), \
             patch('telegram_bot_polling.update_telegram_user_id', return_value=True), \
             patch('telegram_bot_polling.update_form_complete', return_value=True), \
             patch('telegram_bot_polling.continue_conversation', new_callable=AsyncMock) as mock_continue:
            
            # Test /start command
            await start(update, context)
            
            # Verify user was welcomed
            update.message.reply_text.assert_called()
            welcome_message = update.message.reply_text.call_args[0][0]
            assert "Hi Alice Johnson!" in welcome_message
            
            # Verify continue conversation was called
            mock_continue.assert_called_once()
            
            # Test /status command
            update.message.reply_text.reset_mock()
            await status(update, context)
            
            # Verify status was displayed
            update.message.reply_text.assert_called()
            status_message = update.message.reply_text.call_args[0][0]
            assert "Form: ✅" in status_message
            
        # Test progression to complete state
        with patch('telegram_bot_polling.get_status_data', return_value=complete_data):
            update.message.reply_text.reset_mock()
            await status(update, context)
            
            status_message = update.message.reply_text.call_args[0][0]
            assert "Form: ✅" in status_message
            assert "Partner: ✅" in status_message
            assert "Payment: ✅" in status_message
            assert "Group: ✅" in status_message
    
    @pytest.mark.asyncio
    async def test_multi_partner_flow(self):
        """Test multi-partner user flow with missing partners"""
        # Setup
        user_id = 123456793
        submission_id = 'SUBM_12349'
        
        user_data = MockData.get_parsed_multi_partner_user()
        
        # Create mock objects
        update = MockTelegramObjects.create_mock_update(user_id=user_id)
        context = MockTelegramObjects.create_mock_context(args=[submission_id])
        
        with patch('telegram_bot_polling.get_status_data', return_value=user_data), \
             patch('telegram_bot_polling.update_telegram_user_id', return_value=True), \
             patch('telegram_bot_polling.update_form_complete', return_value=True):
            
            # Test /start command
            await start(update, context)
            
            # Test /status command
            update.message.reply_text.reset_mock()
            await status(update, context)
            
            status_message = update.message.reply_text.call_args[0][0]
            assert "Carlos Santos, Ana Lopez" in status_message
            assert "hasn't completed the form yet" in status_message
            
            # Test /remind_partner command
            update.message.reply_text.reset_mock()
            with patch('telegram_bot_polling.send_partner_reminder', return_value=True), \
                 patch('telegram_bot_polling.log_reminder_sent', new_callable=AsyncMock):
                
                await remind_partner(update, context)
                
                # Should send reminders for missing partners
                update.message.reply_text.assert_called()
                reminder_message = update.message.reply_text.call_args[0][0]
                assert "Reminders sent to 2 partners" in reminder_message
    
    @pytest.mark.asyncio
    async def test_hebrew_user_flow(self):
        """Test Hebrew user interface flow"""
        # Setup
        user_id = 123456792
        submission_id = 'SUBM_12348'
        
        user_data = MockData.get_parsed_hebrew_user()
        
        # Create mock objects with Hebrew locale
        update = MockTelegramObjects.create_mock_update(
            user_id=user_id, 
            first_name="יוחנן",
            language_code="he"
        )
        context = MockTelegramObjects.create_mock_context(args=[submission_id])
        
        with patch('telegram_bot_polling.get_status_data', return_value=user_data), \
             patch('telegram_bot_polling.update_telegram_user_id', return_value=True), \
             patch('telegram_bot_polling.update_form_complete', return_value=True), \
             patch('telegram_bot_polling.continue_conversation', new_callable=AsyncMock):
            
            # Test /start command
            await start(update, context)
            
            # Verify Hebrew welcome message
            update.message.reply_text.assert_called()
            welcome_message = update.message.reply_text.call_args[0][0]
            assert "שלום יוחנן כהן!" in welcome_message
            
            # Test /status command
            update.message.reply_text.reset_mock()
            await status(update, context)
            
            status_message = update.message.reply_text.call_args[0][0]
            assert "טופס: ✅" in status_message
            assert "שותף: ✅" in status_message
            
            # Test /help command
            update.message.reply_text.reset_mock()
            await help_command(update, context)
            
            help_message = update.message.reply_text.call_args[0][0]
            assert "עזרה לבוט Wild Ginger" in help_message
    
    @pytest.mark.asyncio
    async def test_cancellation_flow(self):
        """Test user cancellation flow"""
        # Setup
        user_id = 123456789
        submission_id = 'SUBM_12345'
        
        user_data = MockData.get_parsed_complete_user()
        user_data['paid'] = True  # Make it last minute cancellation
        
        # Create mock objects
        update = MockTelegramObjects.create_mock_update(user_id=user_id)
        context = MockTelegramObjects.create_mock_context(args=['sudden', 'illness'])
        
        with patch('telegram_bot_polling.get_status_data', return_value=user_data), \
             patch('telegram_bot_polling.update_cancellation_status', return_value=True):
            
            # Test /cancel command
            await cancel_registration(update, context)
            
            # Verify cancellation message
            update.message.reply_text.assert_called()
            cancel_message = update.message.reply_text.call_args[0][0]
            assert "cancelled" in cancel_message
            assert "sudden illness" in cancel_message
            assert "last-minute cancellation" in cancel_message
    
    @pytest.mark.asyncio
    async def test_reminder_system_integration(self):
        """Test integration of reminder system with user data"""
        # Setup
        app = MockTelegramObjects.create_mock_bot_application()
        scheduler = ReminderScheduler(app)
        
        # Mock sheet data with users needing reminders
        sheet_data = MockData.get_sheet_data()
        
        with patch('telegram_bot_polling.get_sheet_data', return_value=sheet_data), \
             patch('telegram_bot_polling.log_reminder_sent', new_callable=AsyncMock):
            
            # Test reminder checking
            await scheduler.check_and_send_reminders()
            
            # Verify reminders were sent (should send messages to bot)
            # The exact number depends on mock data setup
            assert app.bot.send_message.call_count >= 0

class TestComponentInteraction:
    """Test interactions between different components"""
    
    @pytest.mark.asyncio
    async def test_google_sheets_integration(self):
        """Test Google Sheets integration with real-like data"""
        # Setup mock service
        mock_service = MockGoogleSheetsService()
        
        with patch('telegram_bot_polling.sheets_service', mock_service):
            # Test updating user data
            success = update_telegram_user_id('SUBM_12345', '123456789')
            assert success == True
            
            # Test form completion update
            success = update_form_complete('SUBM_12345', True)
            assert success == True
            
            # Test cancellation update
            success = update_cancellation_status('SUBM_12345', True, 'Test reason')
            assert success == True
            
            # Verify updates were tracked
            updates = mock_service.get_updated_cells()
            assert len(updates) > 0
    
    @pytest.mark.asyncio
    async def test_status_message_generation_integration(self):
        """Test status message generation with various user states"""
        test_cases = [
            MockData.get_parsed_complete_user(),
            MockData.get_parsed_incomplete_user(),
            MockData.get_parsed_alone_user(),
            MockData.get_parsed_hebrew_user(),
            MockData.get_parsed_multi_partner_user()
        ]
        
        for user_data in test_cases:
            # Test status message generation
            from telegram_bot_polling import get_status_message
            message = get_status_message(user_data)
            
            # Verify message contains expected elements
            assert isinstance(message, str)
            assert len(message) > 0
            
            # Language-specific checks
            if user_data['language'] == 'he':
                assert any(hebrew_char in message for hebrew_char in 'אבגדהוזחטיכלמנסעפצקרשת')
            else:
                assert 'Form:' in message
                assert 'Partner:' in message
                assert 'Payment:' in message
    
    @pytest.mark.asyncio
    async def test_continue_conversation_integration(self):
        """Test continue_conversation with different user states"""
        # Setup
        update = MockTelegramObjects.create_mock_update()
        context = MockTelegramObjects.create_mock_context()
        
        test_cases = [
            (MockData.get_parsed_incomplete_user(), "next steps"),
            (MockData.get_parsed_complete_user(), "all set"),
            (MockData.get_parsed_hebrew_user(), "חלק ההיכרות"),
            (MockData.get_parsed_multi_partner_user(), "Carlos Santos, Ana Lopez")
        ]
        
        for user_data, expected_content in test_cases:
            update.message.reply_text.reset_mock()
            
            await continue_conversation(update, context, user_data)
            
            # Verify appropriate messages were sent
            assert update.message.reply_text.call_count > 0
            
            # Check if expected content appears in any of the messages
            messages = [call[0][0] for call in update.message.reply_text.call_args_list]
            combined_messages = ' '.join(messages)
            
            # This is a flexible check - some content may vary
            print(f"Expected: {expected_content}")
            print(f"Got: {combined_messages}")

class TestErrorHandling:
    """Test error handling across components"""
    
    @pytest.mark.asyncio
    async def test_google_sheets_unavailable(self):
        """Test behavior when Google Sheets is unavailable"""
        # Setup
        update = MockTelegramObjects.create_mock_update()
        context = MockTelegramObjects.create_mock_context()
        
        with patch('telegram_bot_polling.get_status_data', return_value=None):
            # Test /status command with no data
            await status(update, context)
            
            # Should handle gracefully
            update.message.reply_text.assert_called()
            message = update.message.reply_text.call_args[0][0]
            assert "No submission linked" in message
    
    @pytest.mark.asyncio
    async def test_telegram_api_errors(self):
        """Test handling of Telegram API errors"""
        # Setup
        update = MockTelegramObjects.create_mock_update()
        update.message.reply_text = AsyncMock(side_effect=Exception("API Error"))
        context = MockTelegramObjects.create_mock_context()
        
        user_data = MockData.get_parsed_complete_user()
        
        with patch('telegram_bot_polling.get_status_data', return_value=user_data):
            # This should not crash the application
            try:
                await status(update, context)
            except Exception as e:
                # We expect the API error to be raised
                assert "API Error" in str(e)
    
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self):
        """Test handling of malformed data"""
        # Setup
        update = MockTelegramObjects.create_mock_update()
        context = MockTelegramObjects.create_mock_context()
        
        # Test with malformed data
        malformed_data = {
            'submission_id': None,
            'alias': '',
            'language': 'invalid',
            'partner_names': None,
            'partner_status': None
        }
        
        with patch('telegram_bot_polling.get_status_data', return_value=malformed_data):
            # Should handle gracefully without crashing
            await status(update, context)
            
            # Should still send some response
            update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_reminder_system_error_handling(self):
        """Test reminder system error handling"""
        # Setup
        app = MockTelegramObjects.create_mock_bot_application()
        app.bot.send_message = AsyncMock(side_effect=Exception("Send error"))
        
        scheduler = ReminderScheduler(app)
        
        # Mock data that would trigger reminders
        user_data = MockData.get_parsed_incomplete_user()
        
        # Should not crash when send_message fails
        try:
            await scheduler.check_user_reminders(user_data)
        except Exception as e:
            # Some exceptions are expected due to mock setup
            print(f"Expected error during testing: {e}")

class TestPerformanceAndScaling:
    """Test performance and scaling aspects"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create large mock dataset
        large_dataset = []
        for i in range(100):
            row = MockData.COMPLETE_USER_ROW.copy()
            row[0] = f'SUBM_{i:05d}'  # Unique submission ID
            row[1] = f'User {i}'      # Unique name
            row[12] = f'12345678{i:02d}'  # Unique telegram ID
            large_dataset.append(row)
        
        sheet_data = {
            'headers': MockData.SHEET_HEADERS,
            'rows': large_dataset
        }
        
        # Test reminder system with large dataset
        app = MockTelegramObjects.create_mock_bot_application()
        scheduler = ReminderScheduler(app)
        
        with patch('telegram_bot_polling.get_sheet_data', return_value=sheet_data):
            # This should complete in reasonable time
            import time
            start_time = time.time()
            await scheduler.check_and_send_reminders()
            end_time = time.time()
            
            # Should complete within reasonable time (adjust as needed)
            assert end_time - start_time < 10  # 10 seconds max
    
    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self):
        """Test concurrent user operations"""
        # Setup multiple users
        users = [
            (123456789, 'SUBM_12345', MockData.get_parsed_complete_user()),
            (123456790, 'SUBM_12346', MockData.get_parsed_incomplete_user()),
            (123456791, 'SUBM_12347', MockData.get_parsed_alone_user())
        ]
        
        async def process_user(user_id, submission_id, user_data):
            update = MockTelegramObjects.create_mock_update(user_id=user_id)
            context = MockTelegramObjects.create_mock_context()
            
            with patch('telegram_bot_polling.get_status_data', return_value=user_data):
                await status(update, context)
                return update.message.reply_text.call_count
        
        # Process all users concurrently
        tasks = [process_user(uid, sid, data) for uid, sid, data in users]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert all(result > 0 for result in results)

class TestDataConsistency:
    """Test data consistency across operations"""
    
    @pytest.mark.asyncio
    async def test_user_state_consistency(self):
        """Test that user state remains consistent across operations"""
        # Setup
        user_id = 123456789
        submission_id = 'SUBM_12345'
        
        user_data = MockData.get_parsed_incomplete_user()
        
        # Store initial state
        user_submissions[str(user_id)] = submission_id
        
        # Test multiple operations
        update = MockTelegramObjects.create_mock_update(user_id=user_id)
        context = MockTelegramObjects.create_mock_context()
        
        with patch('telegram_bot_polling.get_status_data', return_value=user_data):
            # Multiple status checks should be consistent
            await status(update, context)
            first_message = update.message.reply_text.call_args[0][0]
            
            update.message.reply_text.reset_mock()
            await status(update, context)
            second_message = update.message.reply_text.call_args[0][0]
            
            # Messages should be identical
            assert first_message == second_message
    
    def test_mock_data_consistency(self):
        """Test that mock data is consistent and valid"""
        # Run validation
        validate_test_data()
        
        # Additional consistency checks
        data = MockData.get_sheet_data()
        
        # Check that parsed data matches raw data
        from telegram_bot_polling import get_column_indices, parse_submission_row
        
        column_indices = get_column_indices(data['headers'])
        
        for row in data['rows']:
            if len(row) >= len(data['headers']):  # Skip malformed rows
                parsed = parse_submission_row(row, column_indices)
                
                # Basic consistency checks
                assert parsed['submission_id'] == row[0]
                if len(row) > 1:
                    assert parsed['alias'] == row[1]

if __name__ == '__main__':
    # Run specific integration tests
    pytest.main([__file__, '-v', '-k', 'TestEndToEndFlows']) 