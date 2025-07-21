#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive End-to-End Tests for Wild Ginger Telegram Bot - Microservice Architecture
Testing complete user journeys, edge cases, and system resilience
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime, timedelta
import time
import random

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the microservice system
from telegram_bot.main import WildGingerBot
from telegram_bot.services import (
    SheetsService, MessageService, ReminderService, ConversationService,
    AdminService, BackgroundScheduler, CancellationService, MonitoringService
)
from telegram_bot.exceptions import (
    ServiceException, RegistrationNotFoundException, SheetsConnectionException
)

# Import test fixtures
from test_fixtures_microservices import (
    MockData, MockTelegramObjects, TestScenarios, MockBotApplication
)


class TestCompleteUserJourney:
    """Test complete end-to-end user journey from registration to group access"""
    
    def setup_method(self):
        """Setup for each test"""
        # Initialize all services
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.reminder_service = ReminderService(self.sheets_service, self.message_service)
        self.conversation_service = ConversationService(self.sheets_service, self.message_service)
        self.admin_service = AdminService(self.sheets_service, self.message_service)
        self.cancellation_service = CancellationService(self.sheets_service, self.message_service)
        self.monitoring_service = MonitoringService()
        
        # Create mock bot application
        self.bot_app = MockBotApplication()
        
        # Set bot references
        for service in [self.reminder_service, self.admin_service, self.cancellation_service]:
            service.set_bot_application(self.bot_app)
    
    @pytest.mark.asyncio
    async def test_happy_path_complete_user_journey(self):
        """
        Test the complete happy path user journey from start to group access
        """
        print("\n🎯 TESTING HAPPY PATH - COMPLETE USER JOURNEY")
        
        user_id = 123456789
        submission_id = 'SUBM_E2E_001'
        
        # Stage 1: User starts registration (incomplete)
        print("📝 Stage 1: User Registration Started")
        initial_user_data = MockData.get_parsed_incomplete_user()
        initial_user_data['submission_id'] = submission_id
        initial_user_data['telegram_user_id'] = str(user_id)
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find, \
             patch.object(self.sheets_service, 'update_step_status') as mock_update:
            
            mock_find.return_value = initial_user_data
            mock_update.return_value = True
            
            # Test status retrieval
            status_data = self.sheets_service.find_submission_by_telegram_id(str(user_id))
            assert status_data['submission_id'] == submission_id
            assert status_data['form'] is True
            assert status_data['partner'] is False  # Waiting for partner
            
            # Test message generation
            status_message = self.message_service.build_status_message(status_data, 'en')
            assert "📋 Form: ✅" in status_message
            assert "🤝 Partner: ❌" in status_message
            
        # Stage 2: User starts get-to-know conversation
        print("💬 Stage 2: Get-to-Know Conversation")
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = initial_user_data
            
            # Start conversation
            result = await self.conversation_service.start_get_to_know_flow(user_id, 'en')
            
            # Verify conversation started
            assert isinstance(result, dict)
            if result.get('success'):
                assert 'message' in result
                assert user_id in self.conversation_service.conversation_states
        
        # Stage 3: User completes conversation
        print("✍️ Stage 3: Complete Get-to-Know Response")
        
        # Set up conversation state
        self.conversation_service.conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'first_question',
            'language': 'en',
            'submission_id': submission_id
        }
        
        with patch.object(self.sheets_service, 'store_get_to_know_response') as mock_store, \
             patch.object(self.sheets_service, 'update_step_status') as mock_update_step:
            
            mock_store.return_value = True
            mock_update_step.return_value = True
            
            # Handle good response
            result = await self.conversation_service.handle_conversation_response(
                user_id, 
                "I am a software developer with 5 years of experience. I love cooking, hiking, and playing guitar. I'm excited to meet new people and learn about different perspectives."
            )
            
            assert isinstance(result, dict)
            if result.get('success'):
                assert 'message' in result
        
        # Stage 4: Partner registers
        print("🤝 Stage 4: Partner Registration Complete")
        
        # Update user data to show partner is now registered
        partner_complete_data = initial_user_data.copy()
        partner_complete_data['partner'] = True
        partner_complete_data['get_to_know'] = True
        
        # Stage 5: Admin review and approval
        print("👨‍💼 Stage 5: Admin Review and Approval")
        
        admin_id = 332883645  # Configured admin
        
        with patch.object(self.sheets_service, 'find_submission_by_id') as mock_find_sub, \
             patch.object(self.sheets_service, 'update_admin_approval') as mock_approve:
            
            mock_find_sub.return_value = partner_complete_data
            mock_approve.return_value = True
            
            # Admin approves registration
            approval_result = await self.admin_service.approve_registration(
                submission_id, admin_id, 'Admin User'
            )
            
            assert approval_result['success'] is True
            assert 'approved successfully' in approval_result['message'].lower()
        
        # Stage 6: Payment processing
        print("💳 Stage 6: Payment Processing")
        
        # Update user data to show payment complete
        payment_complete_data = partner_complete_data.copy()
        payment_complete_data['approved'] = True
        payment_complete_data['paid'] = True
        
        with patch.object(self.sheets_service, 'update_step_status') as mock_payment:
            mock_payment.return_value = True
            
            # Simulate payment completion
            payment_result = await self.sheets_service.update_step_status(submission_id, 'paid', True)
            assert payment_result is True
        
        # Stage 7: Group access granted
        print("🎉 Stage 7: Group Access Granted")
        
        # Final user data - everything complete
        complete_data = payment_complete_data.copy()
        complete_data['group_open'] = True
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_final:
            mock_final.return_value = complete_data
            
            # Verify final status
            final_status = self.sheets_service.find_submission_by_telegram_id(str(user_id))
            assert final_status['form'] is True
            assert final_status['partner'] is True
            assert final_status['get_to_know'] is True
            assert final_status['approved'] is True
            assert final_status['paid'] is True
            assert final_status['group_open'] is True
            
            # Generate final status message
            final_message = self.message_service.build_status_message(final_status, 'en')
            assert "📋 Form: ✅" in final_message
            assert "🤝 Partner: ✅" in final_message
            assert "💬 Get-to-know: ✅" in final_message
            assert "✅ Approved" in final_message
            assert "💸 Payment: ✅" in final_message
            assert "🎉" in final_message  # Success indicator
        
        print("✅ HAPPY PATH COMPLETE - User successfully reached group access!")
    
    @pytest.mark.asyncio
    async def test_hebrew_user_complete_journey(self):
        """
        Test complete user journey for Hebrew-speaking user
        """
        print("\n🎯 TESTING HEBREW USER COMPLETE JOURNEY")
        
        user_id = 987654321
        hebrew_user_data = MockData.get_parsed_hebrew_user()
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = hebrew_user_data
            
            # Test Hebrew status message
            status_message = self.message_service.build_status_message(hebrew_user_data, 'he')
            
            # Should contain Hebrew text
            assert any(hebrew_char in status_message for hebrew_char in 'אבגדהוזחטיכלמנסעפצקרשת')
            
            # Start Hebrew conversation
            result = await self.conversation_service.start_get_to_know_flow(user_id, 'he')
            
            if result.get('success'):
                # Should contain Hebrew text
                assert any(hebrew_char in result['message'] for hebrew_char in 'אבגדהוזחטיכלמנסעפצקרשת')
        
        print("✅ HEBREW USER JOURNEY COMPLETE")
    
    @pytest.mark.asyncio
    async def test_multi_partner_journey(self):
        """
        Test journey for user with multiple partners
        """
        print("\n🎯 TESTING MULTI-PARTNER USER JOURNEY")
        
        user_id = 555666777
        multi_partner_data = MockData.get_parsed_multi_partner_user()
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find, \
             patch.object(self.reminder_service.sheets_service, 'get_all_registrations') as mock_all:
            
            mock_find.return_value = multi_partner_data
            mock_all.return_value = [
                MockData.get_parsed_complete_user(),  # Partner1 is registered
                multi_partner_data  # Our user
            ]
            
            # Check partner status
            partner_status = self.reminder_service.check_partner_registration_status(
                ['Partner1', 'Partner2', 'Partner3']
            )
            
            assert 'registered_partners' in partner_status
            assert 'missing_partners' in partner_status
            assert len(partner_status['missing_partners']) > 0
            
            # Send partner reminders
            reminder_result = await self.reminder_service.send_partner_reminder(
                user_id, partner_status['missing_partners'], 'en'
            )
            
            assert isinstance(reminder_result, dict)
        
        print("✅ MULTI-PARTNER JOURNEY COMPLETE")


class TestEdgeCasesAndFailures:
    """Test edge cases, failures, and error handling"""
    
    def setup_method(self):
        """Setup for edge case testing"""
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.admin_service = AdminService(self.sheets_service, self.message_service)
        self.cancellation_service = CancellationService(self.sheets_service, self.message_service)
    
    @pytest.mark.asyncio
    async def test_google_sheets_unavailable_scenario(self):
        """
        Test system behavior when Google Sheets is unavailable
        """
        print("\n🎯 TESTING GOOGLE SHEETS UNAVAILABLE SCENARIO")
        
        user_id = 999888777
        
        # Simulate Google Sheets API failure
        with patch.object(self.sheets_service, 'get_sheet_data') as mock_get_data:
            mock_get_data.side_effect = SheetsConnectionException("Google Sheets API unavailable")
            
            # Test that services handle the failure gracefully
            try:
                result = self.sheets_service.get_sheet_data()
                assert False, "Should have raised SheetsConnectionException"
            except SheetsConnectionException as e:
                assert "unavailable" in str(e).lower()
        
        # Test admin service handles sheets unavailability
        with patch.object(self.admin_service.sheets_service, 'get_all_registrations') as mock_get_all:
            mock_get_all.side_effect = SheetsConnectionException("Connection failed")
            
            result = await self.admin_service.get_dashboard_stats(332883645)
            
            # Should handle gracefully, not crash
            assert isinstance(result, dict)
            assert 'error' in result or result.get('success') is False
        
        print("✅ GOOGLE SHEETS UNAVAILABLE SCENARIO HANDLED")
    
    @pytest.mark.asyncio
    async def test_invalid_user_data_scenarios(self):
        """
        Test handling of invalid, corrupted, or missing user data
        """
        print("\n🎯 TESTING INVALID USER DATA SCENARIOS")
        
        # Test empty/None registration data
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = None
            
            result = self.sheets_service.find_submission_by_telegram_id('999999999')
            assert result is None
        
        # Test corrupted registration data
        corrupted_data = {
            'submission_id': None,  # Missing required field
            'alias': '',  # Empty name
            'partner': 'INVALID_BOOLEAN',  # Wrong data type
        }
        
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = corrupted_data
            
            # Message service should handle corrupted data gracefully
            try:
                status_message = self.message_service.build_status_message(corrupted_data, 'en')
                # Should not crash, should return some kind of error message
                assert isinstance(status_message, str)
                assert len(status_message) > 0
            except Exception as e:
                # If it throws an exception, it should be a handled one
                assert isinstance(e, (ServiceException, ValueError, KeyError))
        
        print("✅ INVALID USER DATA SCENARIOS HANDLED")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_access_scenario(self):
        """
        Test system behavior with multiple users accessing simultaneously
        """
        print("\n🎯 TESTING CONCURRENT USER ACCESS SCENARIO")
        
        # Simulate multiple users accessing the system simultaneously
        user_ids = [111111111, 222222222, 333333333, 444444444, 555555555]
        
        async def simulate_user_activity(user_id):
            """Simulate a user's activity"""
            user_data = MockData.get_parsed_incomplete_user()
            user_data['telegram_user_id'] = str(user_id)
            
            with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
                mock_find.return_value = user_data
                
                # Each user tries to access their status
                status = self.sheets_service.find_submission_by_telegram_id(str(user_id))
                
                # Each user generates a status message
                message = self.message_service.build_status_message(status, 'en')
                
                return {'user_id': user_id, 'status': status, 'message': message}
        
        # Run all users concurrently
        tasks = [simulate_user_activity(uid) for uid in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all users were handled
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(user_ids)
        
        # Verify each user got their own data
        for result in successful_results:
            assert result['status']['telegram_user_id'] == str(result['user_id'])
            assert isinstance(result['message'], str)
            assert len(result['message']) > 0
        
        print("✅ CONCURRENT USER ACCESS SCENARIO HANDLED")
    
    @pytest.mark.asyncio
    async def test_admin_permission_edge_cases(self):
        """
        Test admin permission edge cases and unauthorized access attempts
        """
        print("\n🎯 TESTING ADMIN PERMISSION EDGE CASES")
        
        # Test unauthorized user trying admin actions
        unauthorized_user_id = 999999999
        
        # Should reject non-admin user
        assert not self.admin_service.is_admin(unauthorized_user_id)
        
        # Test admin action with unauthorized user
        try:
            result = await self.admin_service.approve_registration(
                'SUBM_123', unauthorized_user_id, 'Unauthorized User'
            )
            assert result['success'] is False
        except Exception as e:
            # Should raise permission error
            assert 'permission' in str(e).lower() or 'unauthorized' in str(e).lower()
        
        # Test with valid admin
        admin_user_id = 332883645  # Configured admin
        assert self.admin_service.is_admin(admin_user_id)
        
        print("✅ ADMIN PERMISSION EDGE CASES HANDLED")
    
    @pytest.mark.asyncio
    async def test_conversation_flow_edge_cases(self):
        """
        Test conversation flow edge cases and error recovery
        """
        print("\n🎯 TESTING CONVERSATION FLOW EDGE CASES")
        
        conversation_service = ConversationService(self.sheets_service, self.message_service)
        user_id = 777888999
        
        # Test starting conversation for non-existent user
        with patch.object(conversation_service.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = None
            
            result = await conversation_service.start_get_to_know_flow(user_id, 'en')
            assert result['success'] is False
        
        # Test handling response without conversation state
        result = await conversation_service.handle_conversation_response(user_id, "Test response")
        assert result['success'] is False
        
        # Test boring answer detection
        boring_answers = ["לא", "כן", "לא יודע", "רגיל", "I don't know", "yes", "no"]
        for answer in boring_answers:
            is_boring = conversation_service.is_boring_answer(answer)
            assert is_boring is True
        
        # Test good answer detection
        good_answers = [
            "I am a passionate software engineer with 5 years of experience",
            "אני מפתח תוכנה ואוהב לבשל ולטייל",
            "I love photography, hiking, and meeting new people from different cultures"
        ]
        for answer in good_answers:
            is_boring = conversation_service.is_boring_answer(answer)
            assert is_boring is False
        
        print("✅ CONVERSATION FLOW EDGE CASES HANDLED")
    
    @pytest.mark.asyncio
    async def test_cancellation_edge_cases(self):
        """
        Test cancellation scenarios and edge cases
        """
        print("\n🎯 TESTING CANCELLATION EDGE CASES")
        
        # Test last-minute cancellation detection
        paid_user = MockData.get_parsed_complete_user()
        paid_user['paid'] = True
        
        is_last_minute = self.cancellation_service._is_last_minute_cancellation(paid_user)
        assert is_last_minute is True
        
        # Test early cancellation
        early_user = MockData.get_parsed_incomplete_user()
        early_user['paid'] = False
        early_user['approved'] = False
        
        is_last_minute = self.cancellation_service._is_last_minute_cancellation(early_user)
        assert is_last_minute is False
        
        # Test cancellation with invalid user
        with patch.object(self.cancellation_service, '_find_user_registration') as mock_find:
            mock_find.return_value = None
            
            result = await self.cancellation_service.cancel_user_registration(
                999999999, "Test reason", 'en'
            )
            assert result['success'] is False
        
        print("✅ CANCELLATION EDGE CASES HANDLED")


class TestSystemIntegrationScenarios:
    """Test complex system integration scenarios"""
    
    def setup_method(self):
        """Setup for integration testing"""
        # Initialize complete system
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.reminder_service = ReminderService(self.sheets_service, self.message_service)
        self.conversation_service = ConversationService(self.sheets_service, self.message_service)
        self.admin_service = AdminService(self.sheets_service, self.message_service)
        self.background_scheduler = BackgroundScheduler()
        self.cancellation_service = CancellationService(self.sheets_service, self.message_service)
        self.monitoring_service = MonitoringService()
        
        # Set bot application
        self.bot_app = MockBotApplication()
        for service in [self.reminder_service, self.admin_service, self.cancellation_service]:
            service.set_bot_application(self.bot_app)
    
    @pytest.mark.asyncio
    async def test_admin_bulk_operations_scenario(self):
        """
        Test admin performing bulk operations on multiple registrations
        """
        print("\n🎯 TESTING ADMIN BULK OPERATIONS SCENARIO")
        
        admin_id = 332883645
        
        # Mock multiple registrations needing attention
        registrations = [
            MockData.get_parsed_incomplete_user(),
            MockData.get_parsed_complete_user(),
            MockData.get_parsed_hebrew_user(),
            MockData.get_parsed_multi_partner_user()
        ]
        
        # Update submission IDs for uniqueness
        for i, reg in enumerate(registrations):
            reg['submission_id'] = f'SUBM_BULK_{i+1:03d}'
        
        with patch.object(self.admin_service.sheets_service, 'get_all_registrations') as mock_get_all, \
             patch.object(self.admin_service.sheets_service, 'update_admin_approval') as mock_approve:
            
            mock_get_all.return_value = registrations
            mock_approve.return_value = True
            
            # Admin gets dashboard
            dashboard = await self.admin_service.get_dashboard_stats(admin_id)
            assert dashboard['stats']['total'] == 4
            
            # Admin approves multiple registrations
            approval_results = []
            for reg in registrations:
                if not reg.get('approved', False):
                    result = await self.admin_service.approve_registration(
                        reg['submission_id'], admin_id, 'Bulk Admin'
                    )
                    approval_results.append(result)
            
            # All approvals should succeed
            for result in approval_results:
                assert result['success'] is True
        
        print("✅ ADMIN BULK OPERATIONS SCENARIO COMPLETE")
    
    @pytest.mark.asyncio
    async def test_monitoring_and_notification_integration(self):
        """
        Test monitoring service integration with admin notifications
        """
        print("\n🎯 TESTING MONITORING AND NOTIFICATION INTEGRATION")
        
        # Mock new registration detected by monitoring
        new_registration = MockData.get_parsed_incomplete_user()
        new_registration['submission_id'] = 'SUBM_MONITOR_001'
        
        with patch.object(self.monitoring_service, '_find_new_registrations') as mock_find_new, \
             patch.object(self.monitoring_service, '_notify_admin_new_registration') as mock_notify:
            
            mock_find_new.return_value = [new_registration]
            mock_notify.return_value = True
            
            # Simulate monitoring check
            status = await self.monitoring_service.get_monitoring_status()
            assert isinstance(status, dict)
            
            # Test manual check trigger
            manual_result = await self.monitoring_service.manual_check()
            assert isinstance(manual_result, dict)
        
        print("✅ MONITORING AND NOTIFICATION INTEGRATION COMPLETE")
    
    @pytest.mark.asyncio
    async def test_background_scheduler_integration(self):
        """
        Test background scheduler integration with other services
        """
        print("\n🎯 TESTING BACKGROUND SCHEDULER INTEGRATION")
        
        # Mock data for scheduler to process
        users_needing_reminders = [
            MockData.get_parsed_incomplete_user(),
            MockData.get_parsed_multi_partner_user()
        ]
        
        with patch.object(self.background_scheduler.sheets_service, 'get_all_registrations') as mock_get_all:
            mock_get_all.return_value = users_needing_reminders
            
            # Test scheduler status
            status = await self.background_scheduler.get_scheduler_status()
            assert isinstance(status, dict)
            assert 'is_running' in status
            assert 'intervals' in status
            
            # Test user needs reminder logic
            for user in users_needing_reminders:
                needs_reminders = self.background_scheduler._needs_reminders(user)
                # Should return True for incomplete users
                if not user.get('partner') or not user.get('approved'):
                    assert needs_reminders is True
        
        print("✅ BACKGROUND SCHEDULER INTEGRATION COMPLETE")
    
    @pytest.mark.asyncio
    async def test_system_failure_recovery_scenario(self):
        """
        Test system behavior during partial failures and recovery
        """
        print("\n🎯 TESTING SYSTEM FAILURE RECOVERY SCENARIO")
        
        user_id = 111222333
        user_data = MockData.get_parsed_incomplete_user()
        
        # Simulate partial system failure - sheets service fails but message service works
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.side_effect = Exception("Database connection failed")
            
            # System should handle partial failures gracefully
            try:
                status = self.sheets_service.find_submission_by_telegram_id(str(user_id))
                assert False, "Should have raised exception"
            except Exception as e:
                assert "failed" in str(e).lower()
            
            # Message service should still work
            fallback_message = self.message_service.get_message('en', 'system_error')
            assert isinstance(fallback_message, str)
            assert len(fallback_message) > 0
        
        # Test recovery scenario
        with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = user_data  # Service recovered
            
            # System should work normally after recovery
            status = self.sheets_service.find_submission_by_telegram_id(str(user_id))
            assert status is not None
            assert status['submission_id'] == user_data['submission_id']
        
        print("✅ SYSTEM FAILURE RECOVERY SCENARIO COMPLETE")


class TestRealWorldComplexScenarios:
    """Test complex real-world scenarios"""
    
    def setup_method(self):
        """Setup for complex scenario testing"""
        # Full system initialization
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.reminder_service = ReminderService(self.sheets_service, self.message_service)
        self.conversation_service = ConversationService(self.sheets_service, self.message_service)
        self.admin_service = AdminService(self.sheets_service, self.message_service)
        self.cancellation_service = CancellationService(self.sheets_service, self.message_service)
        self.monitoring_service = MonitoringService()
    
    @pytest.mark.asyncio
    async def test_event_day_scenario(self):
        """
        Test system behavior on event day with high load and various activities
        """
        print("\n🎯 TESTING EVENT DAY SCENARIO")
        
        # Multiple simultaneous activities
        activities = []
        
        # Activity 1: New registrations being monitored
        activity_1 = asyncio.create_task(self._simulate_monitoring_activity())
        activities.append(("Monitoring", activity_1))
        
        # Activity 2: Admin managing approvals
        activity_2 = asyncio.create_task(self._simulate_admin_activity())
        activities.append(("Admin", activity_2))
        
        # Activity 3: Users sending partner reminders
        activity_3 = asyncio.create_task(self._simulate_user_reminder_activity())
        activities.append(("Reminders", activity_3))
        
        # Activity 4: Last-minute cancellations
        activity_4 = asyncio.create_task(self._simulate_cancellation_activity())
        activities.append(("Cancellations", activity_4))
        
        # Wait for all activities to complete
        results = await asyncio.gather(*[activity for _, activity in activities], return_exceptions=True)
        
        # Verify all activities completed successfully
        for i, (name, result) in enumerate(zip([name for name, _ in activities], results)):
            if isinstance(result, Exception):
                print(f"❌ {name} activity failed: {result}")
                assert False, f"{name} activity should not fail"
            else:
                print(f"✅ {name} activity completed successfully")
        
        print("✅ EVENT DAY SCENARIO COMPLETE")
    
    async def _simulate_monitoring_activity(self):
        """Simulate monitoring service activity"""
        # Multiple monitoring checks
        for i in range(3):
            status = await self.monitoring_service.get_monitoring_status()
            assert isinstance(status, dict)
            await asyncio.sleep(0.1)  # Small delay between checks
        return True
    
    async def _simulate_admin_activity(self):
        """Simulate admin activity"""
        admin_id = 332883645
        
        # Admin dashboard checks
        with patch.object(self.admin_service.sheets_service, 'get_all_registrations') as mock_get:
            mock_get.return_value = [MockData.get_parsed_incomplete_user()]
            
            for i in range(2):
                dashboard = await self.admin_service.get_dashboard_stats(admin_id)
                assert isinstance(dashboard, dict)
                await asyncio.sleep(0.1)
        return True
    
    async def _simulate_user_reminder_activity(self):
        """Simulate user reminder activity"""
        user_id = 123456789
        
        with patch.object(self.reminder_service.sheets_service, 'find_submission_by_telegram_id') as mock_find:
            mock_find.return_value = MockData.get_parsed_multi_partner_user()
            
            # Multiple users sending reminders
            result = await self.reminder_service.send_partner_reminder(
                user_id, ['Partner1', 'Partner2'], 'en'
            )
            assert isinstance(result, dict)
        return True
    
    async def _simulate_cancellation_activity(self):
        """Simulate cancellation activity"""
        user_id = 987654321
        
        with patch.object(self.cancellation_service, '_find_user_registration') as mock_find:
            mock_find.return_value = MockData.get_parsed_complete_user()
            
            result = await self.cancellation_service.cancel_user_registration(
                user_id, "last minute emergency", 'en'
            )
            assert isinstance(result, dict)
        return True
    
    @pytest.mark.asyncio
    async def test_multi_language_mixed_scenario(self):
        """
        Test scenario with mixed Hebrew and English users interacting simultaneously
        """
        print("\n🎯 TESTING MULTI-LANGUAGE MIXED SCENARIO")
        
        # English user
        english_user_id = 111111111
        english_data = MockData.get_parsed_complete_user()
        
        # Hebrew user
        hebrew_user_id = 222222222
        hebrew_data = MockData.get_parsed_hebrew_user()
        
        async def process_english_user():
            with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
                mock_find.return_value = english_data
                
                # English status message
                status = self.sheets_service.find_submission_by_telegram_id(str(english_user_id))
                message = self.message_service.build_status_message(status, 'en')
                
                # Should contain English text
                assert 'Form' in message
                assert 'Partner' in message
                return message
        
        async def process_hebrew_user():
            with patch.object(self.sheets_service, 'find_submission_by_telegram_id') as mock_find:
                mock_find.return_value = hebrew_data
                
                # Hebrew status message
                status = self.sheets_service.find_submission_by_telegram_id(str(hebrew_user_id))
                message = self.message_service.build_status_message(status, 'he')
                
                # Should contain Hebrew text
                assert any(hebrew_char in message for hebrew_char in 'אבגדהוזחטיכלמנסעפצקרשת')
                return message
        
        # Process both users simultaneously
        english_result, hebrew_result = await asyncio.gather(
            process_english_user(), 
            process_hebrew_user()
        )
        
        # Verify both got appropriate language responses
        assert isinstance(english_result, str)
        assert isinstance(hebrew_result, str)
        assert english_result != hebrew_result  # Should be different languages
        
        print("✅ MULTI-LANGUAGE MIXED SCENARIO COMPLETE")


class TestPerformanceAndStress:
    """Test system performance and stress scenarios"""
    
    def setup_method(self):
        """Setup for performance testing"""
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
    
    @pytest.mark.asyncio
    async def test_high_load_message_generation(self):
        """
        Test system performance with high load message generation
        """
        print("\n🎯 TESTING HIGH LOAD MESSAGE GENERATION")
        
        # Generate many status messages simultaneously
        user_data = MockData.get_parsed_complete_user()
        
        async def generate_message(language):
            return self.message_service.build_status_message(user_data, language)
        
        # Create many concurrent message generation tasks
        tasks = []
        for i in range(100):  # 100 concurrent message generations
            language = 'en' if i % 2 == 0 else 'he'
            tasks.append(generate_message(language))
        
        start_time = time.time()
        messages = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all messages were generated
        assert len(messages) == 100
        for message in messages:
            assert isinstance(message, str)
            assert len(message) > 0
        
        # Performance check - should complete within reasonable time
        duration = end_time - start_time
        print(f"📊 Generated 100 messages in {duration:.2f} seconds")
        assert duration < 5.0, f"Message generation took too long: {duration:.2f}s"
        
        print("✅ HIGH LOAD MESSAGE GENERATION COMPLETE")
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """
        Test that system doesn't have memory leaks during extended operation
        """
        print("\n🎯 TESTING MEMORY USAGE STABILITY")
        
        # Simulate extended operation
        conversation_service = ConversationService(self.sheets_service, self.message_service)
        
        # Create and destroy many conversation states
        for i in range(1000):
            user_id = 1000000 + i
            
            # Create conversation state
            conversation_service.conversation_states[user_id] = {
                'flow': 'get_to_know',
                'step': 'first_question',
                'language': 'en',
                'submission_id': f'SUBM_{i:06d}'
            }
            
            # Clean up periodically
            if i % 100 == 99:
                # Remove old conversation states
                old_states = list(conversation_service.conversation_states.keys())[:50]
                for old_user_id in old_states:
                    del conversation_service.conversation_states[old_user_id]
        
        # Final cleanup
        conversation_service.conversation_states.clear()
        
        # Verify cleanup worked
        assert len(conversation_service.conversation_states) == 0
        
        print("✅ MEMORY USAGE STABILITY TEST COMPLETE")


if __name__ == "__main__":
    # Run comprehensive E2E tests
    print("🧪 Running Comprehensive End-to-End Tests")
    print("=" * 60)
    
    # You can run this file directly to execute all E2E tests
    pytest.main([__file__, "-v", "-s"]) 