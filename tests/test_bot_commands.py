#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot command handler tests for the Wild Ginger Telegram Bot - Microservice Architecture
Testing command handlers that use the new microservice architecture
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new bot and services
from telegram_bot.main import WildGingerBot
from telegram_bot.services import (
    SheetsService, MessageService, ReminderService, ConversationService,
    AdminService, CancellationService, MonitoringService
)
from telegram_bot.handlers import (
    reminder_handler, conversation_handler, admin_handler, 
    cancellation_handler, monitoring_handler
)

# Import test fixtures
from test_fixtures_microservices import (
    MockData, MockTelegramObjects, TestScenarios, MockBotApplication
)


class TestBotCommandHandlers:
    """Test bot command handlers with microservice integration"""
    
    def setup_method(self):
        """Setup for each test"""
        self.mock_update = MockTelegramObjects.create_mock_update()
        self.mock_context = MockTelegramObjects.create_mock_context()
    
    @pytest.mark.asyncio
    async def test_reminder_command_handler(self):
        """Test /remind_partner command handler"""
        # Setup mock context with user submission
        self.mock_context.args = []
        
        with patch.object(reminder_handler.reminder_service, 'send_partner_reminder') as mock_send:
            mock_send.return_value = {
                'success': True,
                'message': '✅ Reminder sent to 1 partner!',
                'reminders_sent': 1
            }
            
            # Test the command handler
            await reminder_handler.remind_partner_command(self.mock_update, self.mock_context)
            
            # Verify response was sent
            self.mock_update.message.reply_text.assert_called()
            response_text = self.mock_update.message.reply_text.call_args[0][0]
            assert '✅' in response_text
    
    @pytest.mark.asyncio
    async def test_get_to_know_command_handler(self):
        """Test /get_to_know command handler"""
        with patch.object(conversation_handler.conversation_service, 'start_get_to_know_flow') as mock_start:
            mock_start.return_value = {
                'success': True,
                'message': 'אשמח לשמוע עליך קצת יותר! 😃',
                'conversation_started': True
            }
            
            # Test the command handler
            await conversation_handler.get_to_know_command(self.mock_update, self.mock_context)
            
            # Verify response was sent
            self.mock_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_command_handler(self):
        """Test /admin_dashboard command handler"""
        # Mock admin user
        self.mock_update.effective_user.id = 332883645  # Configured admin ID
        
        with patch.object(admin_handler.admin_service, 'get_dashboard_stats') as mock_dashboard:
            mock_dashboard.return_value = {
                'stats': {
                    'total': 10,
                    'ready_for_review': 2,
                    'approved': 5,
                    'paid': 3
                },
                'pending_approvals': [
                    {'name': 'John Doe', 'submission_id': 'SUBM_001', 'partner': 'Solo'}
                ]
            }
            
            # Test the command handler
            await admin_handler.admin_dashboard_command(self.mock_update, self.mock_context)
            
            # Verify response was sent
            self.mock_update.message.reply_text.assert_called()
            response_text = self.mock_update.message.reply_text.call_args[0][0]
            assert 'Dashboard' in response_text or 'Total' in response_text
    
    @pytest.mark.asyncio
    async def test_admin_approve_command_handler(self):
        """Test /admin_approve command handler"""
        # Mock admin user and submission ID
        self.mock_update.effective_user.id = 332883645
        self.mock_context.args = ['SUBM_12345']
        
        with patch.object(admin_handler.admin_service, 'approve_registration') as mock_approve:
            mock_approve.return_value = {
                'success': True,
                'message': '✅ Registration SUBM_12345 approved successfully!',
                'registration': MockData.get_parsed_complete_user()
            }
            
            # Test the command handler
            await admin_handler.admin_approve_command(self.mock_update, self.mock_context)
            
            # Verify success message was sent
            self.mock_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_cancel_command_handler(self):
        """Test /cancel command handler"""
        # Setup cancellation reason
        self.mock_context.args = ['sudden', 'illness']
        
        with patch.object(cancellation_handler.cancellation_service, 'cancel_user_registration') as mock_cancel:
            mock_cancel.return_value = {
                'success': True,
                'message': 'Your registration has been cancelled.\n\nReason: sudden illness',
                'is_last_minute': False
            }
            
            # Test the command handler
            await cancellation_handler.cancel_registration_command(self.mock_update, self.mock_context)
            
            # Verify cancellation message was sent
            self.mock_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_monitoring_status_command_handler(self):
        """Test /admin_monitoring_status command handler"""
        # Mock admin user
        self.mock_update.effective_user.id = 332883645
        
        with patch.object(monitoring_handler.monitoring_service, 'get_monitoring_status') as mock_status:
            mock_status.return_value = {
                'is_monitoring': True,
                'monitoring_interval': 300,
                'sheet1_range': 'Sheet1!A1:ZZ1000',
                'has_bot_application': True,
                'sheets_service_available': True,
                'admin_count': 1,
                'column_mappings_count': 5
            }
            
            # Test the command handler
            await monitoring_handler.admin_monitoring_status_command(self.mock_update, self.mock_context)
            
            # Verify status was displayed
            self.mock_update.message.reply_text.assert_called()


class TestBotIntegration:
    """Test bot integration with all services"""
    
    @pytest.mark.asyncio
    async def test_bot_initialization_with_services(self):
        """Test that bot initializes with all microservices"""
        with patch('telegram_bot.main.ApplicationBuilder') as mock_builder:
            mock_app = Mock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app
            mock_app.add_handler = Mock()
            
            # Initialize bot
            bot = WildGingerBot()
            
            # Verify services are initialized
            assert hasattr(bot, 'sheets_service')
            assert hasattr(bot, 'message_service') 
            assert hasattr(bot, 'background_scheduler')
            assert hasattr(bot, 'monitoring_service')
            
            # Verify handlers are registered (check that add_handler was called multiple times)
            assert mock_app.add_handler.call_count > 10  # We have many commands
    
    def test_service_dependencies_injection(self):
        """Test that services are properly injected with dependencies"""
        # Test that services can be created independently
        sheets_service = SheetsService()
        message_service = MessageService()
        
        # Test that dependent services get their dependencies
        reminder_service = ReminderService(sheets_service, message_service)
        assert reminder_service.sheets_service is sheets_service
        assert reminder_service.message_service is message_service
        
        admin_service = AdminService(sheets_service, message_service)
        assert admin_service.sheets_service is sheets_service
        assert admin_service.message_service is message_service


class TestEndToEndFlows:
    """Test complete end-to-end flows with microservices"""
    
    def setup_method(self):
        """Setup services for testing"""
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.reminder_service = ReminderService(self.sheets_service, self.message_service)
        self.admin_service = AdminService(self.sheets_service, self.message_service)
        self.conversation_service = ConversationService(self.sheets_service, self.message_service)
        self.cancellation_service = CancellationService(self.sheets_service, self.message_service)
    
    @pytest.mark.asyncio
    async def test_complete_registration_flow(self):
        """Test complete user registration flow through multiple services"""
        user_id = 123456789
        submission_id = 'SUBM_TEST'
        
        # Mock sheets service responses for progression
        initial_data = MockData.get_parsed_incomplete_user()
        complete_data = MockData.get_parsed_complete_user()
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find, \
             patch.object(self.sheets_service, 'update_step_status') as mock_update:
            
            # Stage 1: User starts get-to-know flow
            mock_find.return_value = initial_data
            mock_update.return_value = True
            
            result = await self.conversation_service.start_get_to_know_flow(user_id, 'en')
            assert result['success'] is True
            
            # Stage 2: Admin approves registration  
            mock_find.return_value = initial_data
            result = await self.admin_service.approve_registration(submission_id, 332883645, 'Admin')
            assert result['success'] is True
            
            # Stage 3: User requests partner reminder
            result = await self.reminder_service.send_partner_reminder(
                user_id, ['Partner Name'], 'en'
            )
            assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_admin_workflow_integration(self):
        """Test admin workflow using multiple services"""
        admin_id = 332883645
        
        with patch.object(self.sheets_service, 'get_all_registrations') as mock_get_all, \
             patch.object(self.sheets_service, 'update_admin_approval') as mock_update, \
             patch.object(self.sheets_service, 'find_submission_by_id') as mock_find:
            
            # Setup mock data
            mock_get_all.return_value = [
                MockData.get_parsed_incomplete_user(),
                MockData.get_parsed_complete_user()
            ]
            mock_update.return_value = True
            mock_find.return_value = MockData.get_parsed_incomplete_user()
            
            # Test dashboard
            dashboard = await self.admin_service.get_dashboard_stats(admin_id)
            assert dashboard['stats']['total'] == 2
            
            # Test approval
            approval = await self.admin_service.approve_registration('SUBM_12346', admin_id, 'Admin')
            assert approval['success'] is True
            
            # Test digest generation  
            digest = await self.admin_service.generate_weekly_digest(admin_id)
            assert isinstance(digest, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling_across_services(self):
        """Test error handling when services interact"""
        user_id = 999999999  # Non-existent user
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = None  # No registration found
            
            # Test conversation service handles missing user
            result = await self.conversation_service.start_get_to_know_flow(user_id, 'en')
            assert result['success'] is False
            
            # Test reminder service handles missing user
            result = await self.reminder_service.send_partner_reminder(user_id, [], 'en')
            assert isinstance(result, dict)
            # Should handle gracefully, not crash
    
    @pytest.mark.asyncio
    async def test_multilingual_support_integration(self):
        """Test multilingual support across services"""
        hebrew_user = MockData.get_parsed_hebrew_user()
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = hebrew_user
            
            # Test Hebrew conversation flow
            result = await self.conversation_service.start_get_to_know_flow(
                int(hebrew_user['telegram_user_id']), 'he'
            )
            
            if result['success']:
                assert any(hebrew_char in result['message'] for hebrew_char in 'אבגדהוזחטיכלמנסעפצקרשת')
            
            # Test Hebrew status message
            status_message = self.message_service.build_status_message(hebrew_user, 'he')
            assert any(hebrew_char in status_message for hebrew_char in 'אבגדהוזחטיכלמנסעפצקרשת')


class TestServiceErrorHandling:
    """Test error handling in service interactions"""
    
    @pytest.mark.asyncio
    async def test_sheets_service_unavailable(self):
        """Test behavior when Google Sheets service is unavailable"""
        # Create service with None sheets service to simulate unavailability
        message_service = MessageService()
        
        with patch('telegram_bot.services.sheets_service.SheetsService.sheets_service', None):
            sheets_service = SheetsService()
            reminder_service = ReminderService(sheets_service, message_service)
            
            # Test that service handles unavailable sheets gracefully
            result = await reminder_service.send_partner_reminder(123456789, ['Partner'], 'en')
            assert isinstance(result, dict)
            # Should not crash, should return error status
    
    @pytest.mark.asyncio 
    async def test_invalid_user_data(self):
        """Test handling of invalid or corrupted user data"""
        sheets_service = SheetsService()
        message_service = MessageService()
        admin_service = AdminService(sheets_service, message_service)
        
        with patch.object(sheets_service, 'get_all_registrations') as mock_get:
            # Return corrupted data
            mock_get.return_value = [
                {},  # Empty registration
                {'submission_id': None},  # Missing required fields
                MockData.get_parsed_complete_user()  # One valid registration
            ]
            
            # Test that service handles corrupted data gracefully
            result = await admin_service.get_dashboard_stats(332883645)
            assert isinstance(result, dict)
            assert 'stats' in result
            # Should still process the valid registration


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 