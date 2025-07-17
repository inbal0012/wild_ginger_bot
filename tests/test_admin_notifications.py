#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for admin notification system
Tests admin commands, notifications, and dashboard functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot_polling import (
    is_admin, notify_admins, notify_registration_ready_for_review,
    notify_partner_delay, notify_payment_overdue, admin_dashboard,
    admin_approve, admin_reject, admin_status, admin_digest,
    send_weekly_admin_digest, check_and_notify_ready_for_review,
    update_admin_approved, ADMIN_USER_IDS
)
from test_fixtures import MockData, MockGoogleSheetsService

class TestAdminUserManagement:
    """Test admin user identification and authentication"""
    
    def test_is_admin_with_configured_admins(self):
        """Test admin identification when admin IDs are configured"""
        with patch('telegram_bot_polling.ADMIN_USER_IDS', [123456789, 987654321]):
            assert is_admin(123456789) == True
            assert is_admin(987654321) == True
            assert is_admin(111111111) == False
    
    def test_is_admin_with_no_admins(self):
        """Test admin identification when no admin IDs are configured"""
        with patch('telegram_bot_polling.ADMIN_USER_IDS', []):
            assert is_admin(123456789) == False
            assert is_admin(987654321) == False

class TestAdminNotifications:
    """Test admin notification system"""
    
    @pytest.mark.asyncio
    async def test_notify_admins_success(self):
        """Test successful admin notification"""
        with patch('telegram_bot_polling.ADMIN_USER_IDS', [123456789, 987654321]):
            with patch('telegram_bot_polling.Bot') as mock_bot_class:
                mock_bot = Mock()
                mock_bot.send_message = AsyncMock()
                mock_bot_class.return_value = mock_bot
                
                await notify_admins("Test message", "test_type")
                
                # Verify Bot was instantiated
                mock_bot_class.assert_called_once()
                
                # Verify messages were sent to all admins
                assert mock_bot.send_message.call_count == 2
                calls = mock_bot.send_message.call_args_list
                
                # Check both admin IDs were called
                admin_ids = [call[1]['chat_id'] for call in calls]
                assert 123456789 in admin_ids
                assert 987654321 in admin_ids
                
                # Check message content
                for call in calls:
                    assert "Test message" in call[1]['text']
                    assert call[1]['parse_mode'] == 'Markdown'
    
    @pytest.mark.asyncio
    async def test_notify_admins_no_admins_configured(self):
        """Test notification when no admins are configured"""
        with patch('telegram_bot_polling.ADMIN_USER_IDS', []):
            with patch('telegram_bot_polling.Bot') as mock_bot_class:
                await notify_admins("Test message", "test_type")
                
                # Verify no Bot was instantiated
                mock_bot_class.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_notify_registration_ready_for_review(self):
        """Test new registration notification"""
        with patch('telegram_bot_polling.notify_admins') as mock_notify:
            await notify_registration_ready_for_review(
                submission_id="SUBM_12345",
                user_name="John Doe",
                partner_info="Jane Smith"
            )
            
            mock_notify.assert_called_once()
            message = mock_notify.call_args[0][0]
            assert "SUBM_12345" in message
            assert "John Doe" in message
            assert "Jane Smith" in message
            assert "Ready for approval" in message
    
    @pytest.mark.asyncio
    async def test_notify_partner_delay(self):
        """Test partner delay notification"""
        with patch('telegram_bot_polling.notify_admins') as mock_notify:
            await notify_partner_delay(
                submission_id="SUBM_12345",
                user_name="John Doe",
                missing_partners=["Jane Smith", "Bob Wilson"]
            )
            
            mock_notify.assert_called_once()
            message = mock_notify.call_args[0][0]
            assert "SUBM_12345" in message
            assert "John Doe" in message
            assert "Jane Smith, Bob Wilson" in message
            assert "24 hours" in message
    
    @pytest.mark.asyncio
    async def test_notify_payment_overdue(self):
        """Test payment overdue notification"""
        with patch('telegram_bot_polling.notify_admins') as mock_notify:
            await notify_payment_overdue(
                submission_id="SUBM_12345",
                user_name="John Doe",
                days_overdue=5
            )
            
            mock_notify.assert_called_once()
            message = mock_notify.call_args[0][0]
            assert "SUBM_12345" in message
            assert "John Doe" in message
            assert "5" in message
            assert "Payment Overdue" in message

class TestAdminCommands:
    """Test admin command handlers"""
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object"""
        update = Mock()
        update.effective_user.id = 123456789
        update.effective_user.first_name = "Admin"
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object"""
        context = Mock()
        context.args = []
        context.bot.send_message = AsyncMock()
        return context
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_access_denied(self, mock_update, mock_context):
        """Test admin dashboard access denied for non-admin"""
        mock_update.effective_user.id = 999999999  # Non-admin ID
        
        with patch('telegram_bot_polling.is_admin', return_value=False):
            await admin_dashboard(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once_with(
                "❌ Access denied. Admin privileges required."
            )
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_no_sheets(self, mock_update, mock_context):
        """Test admin dashboard when Google Sheets is not available"""
        with patch('telegram_bot_polling.is_admin', return_value=True):
            with patch('telegram_bot_polling.sheets_service', None):
                await admin_dashboard(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once_with(
                    "❌ Google Sheets not available. Cannot access registration data."
                )
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_success(self, mock_update, mock_context):
        """Test successful admin dashboard generation"""
        mock_sheet_data = MockData.get_sheet_data()
        
        with patch('telegram_bot_polling.is_admin', return_value=True):
            with patch('telegram_bot_polling.sheets_service', Mock()):
                with patch('telegram_bot_polling.get_sheet_data', return_value=mock_sheet_data):
                    await admin_dashboard(mock_update, mock_context)
                    
                    mock_update.message.reply_text.assert_called_once()
                    message = mock_update.message.reply_text.call_args[0][0]
                    assert "Admin Dashboard" in message
                    assert "Registration Statistics" in message
                    assert "Total:" in message
    
    @pytest.mark.asyncio
    async def test_admin_approve_success(self, mock_update, mock_context):
        """Test successful registration approval"""
        mock_context.args = ["SUBM_12345"]
        
        with patch('telegram_bot_polling.is_admin', return_value=True):
            with patch('telegram_bot_polling.update_admin_approved', return_value=True):
                with patch('telegram_bot_polling.get_status_data', return_value={
                    'telegram_user_id': '987654321',
                    'language': 'en',
                    'alias': 'John Doe'
                }):
                    with patch('telegram_bot_polling.notify_admins') as mock_notify:
                        await admin_approve(mock_update, mock_context)
                        
                        # Check success message
                        mock_update.message.reply_text.assert_called_once()
                        message = mock_update.message.reply_text.call_args[0][0]
                        assert "approved successfully" in message
                        
                        # Check user notification
                        mock_context.bot.send_message.assert_called_once()
                        user_msg = mock_context.bot.send_message.call_args[1]['text']
                        assert "approved" in user_msg
                        
                        # Check admin notification
                        mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_admin_reject_success(self, mock_update, mock_context):
        """Test successful registration rejection"""
        mock_context.args = ["SUBM_12345", "Not", "suitable"]
        
        with patch('telegram_bot_polling.is_admin', return_value=True):
            with patch('telegram_bot_polling.update_admin_approved', return_value=True):
                with patch('telegram_bot_polling.get_status_data', return_value={
                    'telegram_user_id': '987654321',
                    'language': 'en',
                    'alias': 'John Doe'
                }):
                    with patch('telegram_bot_polling.notify_admins') as mock_notify:
                        await admin_reject(mock_update, mock_context)
                        
                        # Check success message
                        mock_update.message.reply_text.assert_called_once()
                        message = mock_update.message.reply_text.call_args[0][0]
                        assert "rejected successfully" in message
                        
                        # Check user notification
                        mock_context.bot.send_message.assert_called_once()
                        user_msg = mock_context.bot.send_message.call_args[1]['text']
                        assert "rejected" in user_msg
                        assert "Not suitable" in user_msg
    
    @pytest.mark.asyncio
    async def test_admin_status_success(self, mock_update, mock_context):
        """Test successful admin status check"""
        mock_context.args = ["SUBM_12345"]
        
        with patch('telegram_bot_polling.is_admin', return_value=True):
            with patch('telegram_bot_polling.get_status_data', return_value={
                'submission_id': 'SUBM_12345',
                'alias': 'John Doe',
                'language': 'en',
                'telegram_user_id': '987654321',
                'form': True,
                'partner': True,
                'get_to_know': True,
                'approved': False,
                'paid': False,
                'group_open': False,
                'partner_alias': 'Jane Smith',
                'is_returning_participant': False,
                'cancelled': False
            }):
                await admin_status(mock_update, mock_context)
                
                mock_update.message.reply_text.assert_called_once()
                message = mock_update.message.reply_text.call_args[0][0]
                assert "SUBM_12345" in message
                assert "John Doe" in message
                assert "Jane Smith" in message
                assert "Progress:" in message

class TestWeeklyDigest:
    """Test weekly digest functionality"""
    
    @pytest.mark.asyncio
    async def test_send_weekly_admin_digest_success(self):
        """Test successful weekly digest generation"""
        mock_sheet_data = MockData.get_sheet_data()
        
        with patch('telegram_bot_polling.sheets_service', Mock()):
            with patch('telegram_bot_polling.get_sheet_data', return_value=mock_sheet_data):
                with patch('telegram_bot_polling.notify_admins') as mock_notify:
                    await send_weekly_admin_digest()
                    
                    mock_notify.assert_called_once()
                    message = mock_notify.call_args[0][0]
                    assert "Weekly Registration Digest" in message
                    assert "Total Registrations:" in message
                    assert "Pending Approval:" in message
    
    @pytest.mark.asyncio
    async def test_send_weekly_admin_digest_no_sheets(self):
        """Test weekly digest when Google Sheets is not available"""
        with patch('telegram_bot_polling.sheets_service', None):
            with patch('telegram_bot_polling.notify_admins') as mock_notify:
                await send_weekly_admin_digest()
                
                # Should not send notification when sheets unavailable
                mock_notify.assert_not_called()

class TestReadyForReviewNotification:
    """Test ready for review notification logic"""
    
    @pytest.mark.asyncio
    async def test_check_and_notify_ready_for_review_success(self):
        """Test notification when registration is ready for review"""
        status_data = {
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': False,
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'partner_alias': 'Jane Smith'
        }
        
        with patch('telegram_bot_polling.notify_registration_ready_for_review') as mock_notify:
            await check_and_notify_ready_for_review(status_data)
            
            mock_notify.assert_called_once_with(
                submission_id='SUBM_12345',
                user_name='John Doe',
                partner_info='Jane Smith'
            )
    
    @pytest.mark.asyncio
    async def test_check_and_notify_ready_for_review_not_ready(self):
        """Test no notification when registration is not ready"""
        status_data = {
            'form': True,
            'partner': False,  # Not complete
            'get_to_know': True,
            'approved': False,
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe'
        }
        
        with patch('telegram_bot_polling.notify_registration_ready_for_review') as mock_notify:
            await check_and_notify_ready_for_review(status_data)
            
            mock_notify.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_and_notify_ready_for_review_already_approved(self):
        """Test no notification when registration is already approved"""
        status_data = {
            'form': True,
            'partner': True,
            'get_to_know': True,
            'approved': True,  # Already approved
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe'
        }
        
        with patch('telegram_bot_polling.notify_registration_ready_for_review') as mock_notify:
            await check_and_notify_ready_for_review(status_data)
            
            mock_notify.assert_not_called()

class TestUpdateAdminApproved:
    """Test admin approval update function"""
    
    def test_update_admin_approved_no_sheets(self):
        """Test update when Google Sheets is not available"""
        with patch('telegram_bot_polling.sheets_service', None):
            result = update_admin_approved("SUBM_12345", True)
            assert result == False
    
    def test_update_admin_approved_success(self):
        """Test successful admin approval update"""
        mock_sheet_data = MockData.get_sheet_data()
        mock_sheets_service = MockGoogleSheetsService(mock_sheet_data)
        
        with patch('telegram_bot_polling.sheets_service', mock_sheets_service):
            with patch('telegram_bot_polling.get_sheet_data', return_value=mock_sheet_data):
                with patch('telegram_bot_polling.column_index_to_letter', return_value='F'):
                    result = update_admin_approved("SUBM_12345", True)
                    assert result == True

if __name__ == '__main__':
    print("🧪 Running admin notification system tests...")
    
    # Run specific test categories
    async def run_async_tests():
        """Run all async tests"""
        test_classes = [
            TestAdminNotifications,
            TestAdminCommands,
            TestWeeklyDigest,
            TestReadyForReviewNotification
        ]
        
        for test_class in test_classes:
            instance = test_class()
            print(f"\n📋 Testing {test_class.__name__}...")
            
            # Get all test methods
            methods = [method for method in dir(instance) if method.startswith('test_')]
            
            for method_name in methods:
                method = getattr(instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    try:
                        await method()
                        print(f"✅ {method_name}: PASSED")
                    except Exception as e:
                        print(f"❌ {method_name}: FAILED - {e}")
                else:
                    try:
                        method()
                        print(f"✅ {method_name}: PASSED")
                    except Exception as e:
                        print(f"❌ {method_name}: FAILED - {e}")
    
    # Run sync tests
    test_user_mgmt = TestAdminUserManagement()
    test_update = TestUpdateAdminApproved()
    
    print("\n📋 Testing TestAdminUserManagement...")
    try:
        test_user_mgmt.test_is_admin_with_configured_admins()
        print("✅ test_is_admin_with_configured_admins: PASSED")
    except Exception as e:
        print(f"❌ test_is_admin_with_configured_admins: FAILED - {e}")
    
    try:
        test_user_mgmt.test_is_admin_with_no_admins()
        print("✅ test_is_admin_with_no_admins: PASSED")
    except Exception as e:
        print(f"❌ test_is_admin_with_no_admins: FAILED - {e}")
    
    print("\n📋 Testing TestUpdateAdminApproved...")
    try:
        test_update.test_update_admin_approved_no_sheets()
        print("✅ test_update_admin_approved_no_sheets: PASSED")
    except Exception as e:
        print(f"❌ test_update_admin_approved_no_sheets: FAILED - {e}")
    
    try:
        test_update.test_update_admin_approved_success()
        print("✅ test_update_admin_approved_success: PASSED")
    except Exception as e:
        print(f"❌ test_update_admin_approved_success: FAILED - {e}")
    
    # Run async tests
    asyncio.run(run_async_tests())
    
    print("\n🎉 Admin notification system tests completed!") 