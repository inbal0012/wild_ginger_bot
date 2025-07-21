#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for the Wild Ginger Telegram Bot - Microservice Architecture
Testing all services in the new professional architecture
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new microservices
from telegram_bot.services import (
    SheetsService, MessageService, ReminderService, ConversationService,
    AdminService, BackgroundScheduler, CancellationService, MonitoringService
)
from telegram_bot.exceptions import (
    ServiceException, RegistrationNotFoundException, SheetsConnectionException
)
from telegram_bot.models.registration import RegistrationStatus, StepProgress, RegistrationData

# Import test fixtures
from test_fixtures import MockData, MockTelegramObjects, TestScenarios


class TestSheetsService:
    """Test the SheetsService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.sheets_service = SheetsService()
    
    def test_sheets_service_initialization(self):
        """Test that SheetsService initializes correctly"""
        assert self.sheets_service is not None
        assert hasattr(self.sheets_service, 'sheets_service')
        assert hasattr(self.sheets_service, 'spreadsheet_id')
        assert hasattr(self.sheets_service, 'range_name')
    
    def test_column_index_to_letter_conversion(self):
        """Test column index to Excel letter conversion"""
        # Test basic conversions
        assert self.sheets_service._column_index_to_letter(0) == 'A'
        assert self.sheets_service._column_index_to_letter(25) == 'Z'
        assert self.sheets_service._column_index_to_letter(26) == 'AA'
        assert self.sheets_service._column_index_to_letter(27) == 'AB'
    
    def test_get_column_indices(self):
        """Test column index mapping from headers"""
        headers = MockData.SHEET_HEADERS
        column_indices = self.sheets_service.get_column_indices(headers)
        
        # Check key columns are found
        assert 'submission_id' in column_indices
        assert 'full_name' in column_indices
        assert 'form_complete' in column_indices
        assert 'telegram_user_id' in column_indices
        
        # Check indices are correct
        assert column_indices['submission_id'] == 0
        assert isinstance(column_indices['full_name'], int)
    
    @patch('telegram_bot.services.sheets_service.SheetsService.sheets_service')
    def test_get_sheet_data_success(self, mock_sheets):
        """Test successful sheet data retrieval"""
        # Mock Google Sheets API response
        mock_response = {
            'values': [
                MockData.SHEET_HEADERS,
                MockData.COMPLETE_USER_ROW,
                MockData.INCOMPLETE_USER_PARTNER_ROW
            ]
        }
        
        mock_sheets.spreadsheets().values().get().execute.return_value = mock_response
        
        result = self.sheets_service.get_sheet_data()
        
        assert result is not None
        assert 'headers' in result
        assert 'rows' in result
        assert len(result['headers']) == len(MockData.SHEET_HEADERS)
        assert len(result['rows']) == 2
    
    @patch('telegram_bot.services.sheets_service.SheetsService.sheets_service')
    def test_get_sheet_data_failure(self, mock_sheets):
        """Test sheet data retrieval failure"""
        mock_sheets.spreadsheets().values().get().execute.side_effect = Exception("API Error")
        
        with pytest.raises(SheetsConnectionException):
            self.sheets_service.get_sheet_data()
    
    def test_parse_submission_row(self):
        """Test parsing a submission row into structured data"""
        headers = MockData.SHEET_HEADERS
        row_data = MockData.COMPLETE_USER_ROW
        column_indices = self.sheets_service.get_column_indices(headers)
        
        parsed = self.sheets_service._parse_submission_row(row_data, column_indices)
        
        assert parsed is not None
        assert parsed['submission_id'] == 'SUBM_12345'
        assert parsed['alias'] == 'John Doe'
        assert parsed['form'] is True
        assert parsed['partner'] is True
        assert parsed['approved'] is True
        assert parsed['paid'] is True


class TestMessageService:
    """Test the MessageService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.message_service = MessageService()
    
    def test_message_service_initialization(self):
        """Test that MessageService initializes correctly"""
        assert self.message_service is not None
        assert hasattr(self.message_service, 'messages')
        assert 'en' in self.message_service.messages
        assert 'he' in self.message_service.messages
    
    def test_get_message_english(self):
        """Test getting English messages"""
        message = self.message_service.get_message('en', 'welcome', name="John")
        assert "Hi John!" in message
        assert "registration assistant" in message
        
    def test_get_message_hebrew(self):
        """Test getting Hebrew messages"""
        message = self.message_service.get_message('he', 'welcome', name="יוחנן")
        assert "שלום יוחנן!" in message
        assert "עוזר הרשמה" in message
        
    def test_get_message_fallback_to_english(self):
        """Test fallback to English when key not found in Hebrew"""
        message = self.message_service.get_message('he', 'non_existent_key')
        assert "Message key 'non_existent_key' not found" in message
    
    def test_build_status_message(self):
        """Test building user status messages"""
        user_data = MockData.get_parsed_complete_user()
        
        message = self.message_service.build_status_message(user_data, 'en')
        
        assert "📋 Form: ✅" in message
        assert "🤝 Partner: ✅" in message
        assert "💬 Get-to-know: ✅" in message
        assert "✅ Approved" in message
        assert "💸 Payment: ✅" in message
    
    def test_build_status_message_incomplete(self):
        """Test building status message for incomplete registration"""
        user_data = MockData.get_parsed_incomplete_user()
        
        message = self.message_service.build_status_message(user_data, 'en')
        
        assert "📋 Form: ✅" in message
        assert "🤝 Partner: ❌" in message
        assert "💬 Get-to-know: ✅" in message
        assert "⏳ Waiting for review" in message


class TestReminderService:
    """Test the ReminderService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.reminder_service = ReminderService()
    
    def test_reminder_service_initialization(self):
        """Test that ReminderService initializes correctly"""
        assert self.reminder_service is not None
        assert hasattr(self.reminder_service, 'sheets_service')
        assert hasattr(self.reminder_service, 'message_service')
        assert hasattr(self.reminder_service, 'reminder_intervals')
    
    @pytest.mark.asyncio
    async def test_send_partner_reminder(self):
        """Test sending partner reminder"""
        with patch.object(self.reminder_service, 'sheets_service') as mock_sheets:
            mock_sheets.find_submission_by_id.return_value = MockData.get_parsed_incomplete_user()
            
            result = await self.reminder_service.send_partner_reminder(
                user_id=123456789,
                partner_names=['Jane Smith'],
                language='en'
            )
            
            assert isinstance(result, dict)
            assert 'success' in result
    
    def test_parse_multiple_partners(self):
        """Test parsing multiple partner names"""
        # Test single partner
        result = self.reminder_service.parse_multiple_partners("John Doe")
        assert result == ["John Doe"]
        
        # Test multiple partners with comma
        result = self.reminder_service.parse_multiple_partners("John Doe, Jane Smith")
        assert result == ["John Doe", "Jane Smith"]
        
        # Test Hebrew connector
        result = self.reminder_service.parse_multiple_partners("יוחנן ו מרים")
        assert result == ["יוחנן", "מרים"]
    
    def test_check_partner_registration_status(self):
        """Test checking partner registration status"""
        with patch.object(self.reminder_service, 'sheets_service') as mock_sheets:
            mock_sheets.get_all_registrations.return_value = [
                MockData.get_parsed_complete_user(),
                MockData.get_parsed_incomplete_user()
            ]
            
            result = self.reminder_service.check_partner_registration_status(['John Doe', 'Alice Johnson'])
            
            assert isinstance(result, dict)
            assert 'registered_partners' in result
            assert 'missing_partners' in result


class TestConversationService:
    """Test the ConversationService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.conversation_service = ConversationService()
    
    def test_conversation_service_initialization(self):
        """Test that ConversationService initializes correctly"""
        assert self.conversation_service is not None
        assert hasattr(self.conversation_service, 'sheets_service')
        assert hasattr(self.conversation_service, 'message_service')
        assert hasattr(self.conversation_service, 'conversation_states')
    
    @pytest.mark.asyncio
    async def test_start_get_to_know_flow(self):
        """Test starting the get-to-know conversation flow"""
        user_id = 123456789
        
        with patch.object(self.conversation_service, 'sheets_service') as mock_sheets:
            mock_sheets.find_submission_by_telegram_id.return_value = MockData.get_parsed_incomplete_user()
            
            result = await self.conversation_service.start_get_to_know_flow(user_id, 'he')
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'message' in result
            
            if result['success']:
                assert user_id in self.conversation_service.conversation_states
    
    def test_is_boring_answer(self):
        """Test boring answer detection"""
        # Test boring answers
        boring_answers = ["לא יודע", "רגיל", "כמו כולם", "לא", "כן", "אין דעה"]
        for answer in boring_answers:
            assert self.conversation_service.is_boring_answer(answer) is True
        
        # Test good answers
        good_answers = [
            "אני מפתח תוכנה ואוהב לבשל",
            "I love hiking and photography",
            "אני מורה ואוהב לקרוא ספרים"
        ]
        for answer in good_answers:
            assert self.conversation_service.is_boring_answer(answer) is False
    
    @pytest.mark.asyncio
    async def test_handle_conversation_response(self):
        """Test handling conversation responses"""
        user_id = 123456789
        
        # Set up conversation state
        self.conversation_service.conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'first_question',
            'language': 'he',
            'submission_id': 'SUBM_12345'
        }
        
        with patch.object(self.conversation_service, 'sheets_service') as mock_sheets:
            mock_sheets.store_get_to_know_response.return_value = True
            mock_sheets.update_step_status.return_value = True
            
            result = await self.conversation_service.handle_conversation_response(
                user_id, "אני מפתח תוכנה ואוהב לבשל"
            )
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'message' in result


class TestAdminService:
    """Test the AdminService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.admin_service = AdminService()
    
    def test_admin_service_initialization(self):
        """Test that AdminService initializes correctly"""
        assert self.admin_service is not None
        assert hasattr(self.admin_service, 'sheets_service')
        assert hasattr(self.admin_service, 'message_service')
    
    def test_is_admin(self):
        """Test admin user validation"""
        # Test with configured admin user
        assert self.admin_service.is_admin(332883645) is True  # Configured admin
        
        # Test with non-admin user
        assert self.admin_service.is_admin(999999999) is False
    
    def test_require_admin(self):
        """Test admin requirement checking"""
        # Should not raise for admin
        try:
            self.admin_service.require_admin(332883645)
        except Exception:
            pytest.fail("require_admin raised exception for valid admin")
        
        # Should raise for non-admin
        with pytest.raises(Exception):
            self.admin_service.require_admin(999999999)
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        with patch.object(self.admin_service, 'sheets_service') as mock_sheets:
            mock_sheets.get_all_registrations.return_value = [
                MockData.get_parsed_complete_user(),
                MockData.get_parsed_incomplete_user()
            ]
            
            result = await self.admin_service.get_dashboard_stats(332883645)
            
            assert isinstance(result, dict)
            assert 'stats' in result
            assert 'pending_approvals' in result
            
            stats = result['stats']
            assert 'total' in stats
            assert stats['total'] == 2
    
    @pytest.mark.asyncio
    async def test_approve_registration(self):
        """Test registration approval"""
        with patch.object(self.admin_service, 'sheets_service') as mock_sheets:
            mock_sheets.update_admin_approval.return_value = True
            mock_sheets.find_submission_by_id.return_value = MockData.get_parsed_incomplete_user()
            
            result = await self.admin_service.approve_registration(
                'SUBM_12345', 332883645, 'Admin'
            )
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert result['success'] is True


class TestCancellationService:
    """Test the CancellationService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.cancellation_service = CancellationService()
    
    def test_cancellation_service_initialization(self):
        """Test that CancellationService initializes correctly"""
        assert self.cancellation_service is not None
        assert hasattr(self.cancellation_service, 'sheets_service')
        assert hasattr(self.cancellation_service, 'message_service')
    
    @pytest.mark.asyncio
    async def test_cancel_user_registration(self):
        """Test user registration cancellation"""
        user_id = 123456789
        reason = "sudden illness"
        
        with patch.object(self.cancellation_service, '_find_user_registration') as mock_find, \
             patch.object(self.cancellation_service, 'sheets_service') as mock_sheets:
            
            mock_find.return_value = MockData.get_parsed_complete_user()
            mock_sheets.update_cancellation_status.return_value = True
            
            result = await self.cancellation_service.cancel_user_registration(
                user_id, reason, 'en'
            )
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'message' in result
    
    def test_is_last_minute_cancellation(self):
        """Test last-minute cancellation detection"""
        # Paid registration should be last minute
        paid_registration = MockData.get_parsed_complete_user()
        paid_registration['paid'] = True
        
        assert self.cancellation_service._is_last_minute_cancellation(paid_registration) is True
        
        # Early stage registration should not be last minute
        early_registration = MockData.get_parsed_incomplete_user()
        early_registration['paid'] = False
        early_registration['approved'] = False
        
        assert self.cancellation_service._is_last_minute_cancellation(early_registration) is False
    
    @pytest.mark.asyncio
    async def test_get_cancellation_statistics(self):
        """Test getting cancellation statistics"""
        with patch.object(self.cancellation_service, 'sheets_service') as mock_sheets:
            registrations = [
                MockData.get_parsed_complete_user(),
                MockData.get_parsed_cancelled_user()
            ]
            mock_sheets.get_all_registrations.return_value = registrations
            
            stats = await self.cancellation_service.get_cancellation_statistics()
            
            assert isinstance(stats, dict)
            assert 'total_registrations' in stats
            assert 'total_cancellations' in stats
            assert 'cancellation_rate' in stats


class TestMonitoringService:
    """Test the MonitoringService microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.monitoring_service = MonitoringService()
    
    def test_monitoring_service_initialization(self):
        """Test that MonitoringService initializes correctly"""
        assert self.monitoring_service is not None
        assert hasattr(self.monitoring_service, 'sheets_service')
        assert hasattr(self.monitoring_service, 'admin_service')
        assert hasattr(self.monitoring_service, 'monitoring_interval')
        assert self.monitoring_service.monitoring_interval == 300  # 5 minutes
    
    def test_column_mapping_configuration(self):
        """Test column mapping configuration"""
        assert len(self.monitoring_service.column_mappings) > 0
        assert 'Submission ID' in self.monitoring_service.column_mappings
        assert 'שם מלא' in self.monitoring_service.column_mappings
    
    def test_map_sheet1_to_managed(self):
        """Test mapping Sheet1 data to managed sheet format"""
        sheet1_headers = ['Submission ID', 'שם מלא', 'שם הפרטנר']
        sheet1_data = ['SUBM_001', 'John Doe', 'Jane Smith']
        
        mapped = self.monitoring_service._map_sheet1_to_managed(sheet1_data, sheet1_headers)
        
        assert isinstance(mapped, list)
        assert len(mapped) == 30  # Fixed length for managed sheet
        assert mapped[0] == 'SUBM_001'  # Submission ID
        assert mapped[1] == 'John Doe'  # Full name
        assert mapped[2] == 'Jane Smith'  # Partner name
    
    @pytest.mark.asyncio
    async def test_get_monitoring_status(self):
        """Test getting monitoring status"""
        status = await self.monitoring_service.get_monitoring_status()
        
        assert isinstance(status, dict)
        assert 'is_monitoring' in status
        assert 'monitoring_interval' in status
        assert 'sheet1_range' in status
        assert 'has_bot_application' in status
    
    def test_update_monitoring_interval(self):
        """Test updating monitoring interval"""
        original = self.monitoring_service.monitoring_interval
        
        # Test valid update
        self.monitoring_service.update_monitoring_interval(600)
        assert self.monitoring_service.monitoring_interval == 600
        
        # Test invalid update (too small)
        self.monitoring_service.update_monitoring_interval(30)
        assert self.monitoring_service.monitoring_interval == 600  # Should remain unchanged
        
        # Reset
        self.monitoring_service.update_monitoring_interval(original)


class TestBackgroundScheduler:
    """Test the BackgroundScheduler microservice"""
    
    def setup_method(self):
        """Setup for each test"""
        self.scheduler = BackgroundScheduler()
    
    def test_background_scheduler_initialization(self):
        """Test that BackgroundScheduler initializes correctly"""
        assert self.scheduler is not None
        assert hasattr(self.scheduler, 'sheets_service')
        assert hasattr(self.scheduler, 'reminder_service')
        assert hasattr(self.scheduler, 'admin_service')
        assert hasattr(self.scheduler, 'intervals')
    
    def test_scheduler_intervals_configuration(self):
        """Test scheduler intervals are properly configured"""
        intervals = self.scheduler.intervals
        
        assert 'reminder_check' in intervals
        assert 'partner_pending' in intervals
        assert 'payment_pending' in intervals
        assert 'weekly_digest' in intervals
        
        # Check reasonable intervals
        assert intervals['reminder_check'] == 3600  # 1 hour
        assert intervals['partner_pending'] == 24 * 60 * 60  # 24 hours
        assert intervals['payment_pending'] == 3 * 24 * 60 * 60  # 3 days
    
    def test_needs_reminders_logic(self):
        """Test logic for determining if user needs reminders"""
        # Complete user should not need reminders
        complete_user = MockData.get_parsed_complete_user()
        assert not self.scheduler._needs_reminders(complete_user)
        
        # Incomplete user should need reminders
        incomplete_user = MockData.get_parsed_incomplete_user()
        assert self.scheduler._needs_reminders(incomplete_user)
    
    @pytest.mark.asyncio
    async def test_get_scheduler_status(self):
        """Test getting scheduler status"""
        status = await self.scheduler.get_scheduler_status()
        
        assert isinstance(status, dict)
        assert 'is_running' in status
        assert 'intervals' in status
        assert 'last_check_times' in status


# Integration Tests for Service Interactions

class TestServiceIntegration:
    """Test integration between different services"""
    
    def setup_method(self):
        """Setup services for integration testing"""
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.admin_service = AdminService()
        self.reminder_service = ReminderService()
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_integration(self):
        """Test admin dashboard integration with multiple services"""
        with patch.object(self.sheets_service, 'get_all_registrations') as mock_get_all:
            mock_get_all.return_value = [
                MockData.get_parsed_complete_user(),
                MockData.get_parsed_incomplete_user()
            ]
            
            # Test admin service uses sheets service
            result = await self.admin_service.get_dashboard_stats(332883645)
            
            assert result['stats']['total'] == 2
            assert 'pending_approvals' in result
    
    @pytest.mark.asyncio
    async def test_reminder_service_integration(self):
        """Test reminder service integration with sheets and message services"""
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = MockData.get_parsed_incomplete_user()
            
            result = await self.reminder_service.send_partner_reminder(
                123456789, ['Jane Smith'], 'en'
            )
            
            assert isinstance(result, dict)
            # Test that the services interact correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 