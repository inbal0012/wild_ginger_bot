from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import logging

from ..config.settings import settings
from ..services.sheets_service import SheetsService
from ..services.message_service import MessageService
from ..services.reminder_service import ReminderService
from ..services.admin_service import AdminService
from ..exceptions import ServiceException

if TYPE_CHECKING:
    from telegram.ext import Application

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """Service for handling automated background tasks and reminders"""
    
    def __init__(self, bot_application: 'Application'):
        # Bot application reference
        self.bot = bot_application
        
        # Background task intervals (in seconds)
        self.reminder_intervals = {
            'reminder_check': 3600,  # 1 hour
            'partner_pending': 24 * 60 * 60,  # 24 hours
            'payment_pending': 3 * 24 * 60 * 60,  # 3 days
            'group_opening': 7 * 24 * 60 * 60,  # 7 days
            'event_reminder': 24 * 60 * 60,  # 1 day
            'weekly_digest': 7 * 24 * 60 * 60,  # 7 days
        }
        
        # Track last reminder times to avoid spam
        # TODO retrieve from the sheet
        self.last_reminder_check: Dict[str, datetime] = {}
        self.last_weekly_digest: Optional[datetime] = None
                
        # Background task management
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
    
    async def start_background_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Background scheduler is already running")
            return
        
        if not self.bot:
            raise ServiceException("Bot application must be set before starting scheduler")
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._background_scheduler_loop())
        logger.info("🚀 Background scheduler started")
    
    async def stop_background_scheduler(self):
        """Stop the background scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️ Background scheduler stopped")
    
    async def _background_scheduler_loop(self):
        """Main background scheduler loop"""
        logger.info("🔄 Background scheduler loop started")
        
        while self.is_running:
            try:
                await self.check_and_send_automatic_reminders()
                await asyncio.sleep(self.intervals['reminder_check'])
            except asyncio.CancelledError:
                logger.info("📴 Background scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background scheduler: {e}")
                # Wait shorter time on error, then retry
                await asyncio.sleep(300)  # 5 minutes
    
    async def check_and_send_automatic_reminders(self):
        """Check all users and send appropriate automatic reminders"""
        try:
            logger.info("🔔 Checking for pending automatic reminders...")
            
            # Get all registrations
            registrations = await self.sheets_service.get_all_registrations()
            
            # Counters for efficiency tracking
            total_users = len(registrations)
            skipped_users = 0
            processed_users = 0
            reminders_sent = 0
            
            # Process each registration
            for registration in registrations:
                try:
                    # Quick check if user needs any reminders
                    if not self._needs_reminders(registration):
                        skipped_users += 1
                        continue
                    
                    processed_users += 1
                    
                    # Check and send appropriate reminders
                    sent_count = await self._check_user_reminders(registration)
                    reminders_sent += sent_count
                    
                except Exception as e:
                    logger.error(f"Error processing reminder for {registration.get('submission_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"📊 Reminder check summary: {total_users} users total, {skipped_users} skipped (complete), {processed_users} processed, {reminders_sent} reminders sent")
            
            # Check if it's time for weekly digest
            await self._check_weekly_digest()
            
        except Exception as e:
            logger.error(f"Error in automatic reminder check: {e}")
            raise ServiceException(f"Failed to check automatic reminders: {e}")
    
    def _needs_reminders(self, registration: Dict[str, Any]) -> bool:
        """Quick check if user needs any reminders without expensive processing"""
        # User is fully complete - no reminders needed
        if (registration.get('partner', False) and 
            registration.get('approved', False) and 
            registration.get('paid', False) and 
            registration.get('group_open', False)):
            return False
        
        # No Telegram ID - can't send reminders
        if not registration.get('telegram_user_id'):
            return False
        
        return True
    
    async def _check_user_reminders(self, registration: Dict[str, Any]) -> int:
        """Check if a specific user needs any reminders and send them"""
        sent_count = 0
        submission_id = registration.get('submission_id')
        telegram_user_id = registration.get('telegram_user_id')
        user_name = registration.get('alias', 'Unknown')
        
        try:
            # Check partner reminders (if partner not complete)
            if not registration.get('partner', False):
                if await self._check_partner_reminder(registration):
                    sent_count += 1
            
            # Check payment reminders (if approved but not paid)
            if (registration.get('approved', False) and 
                not registration.get('paid', False)):
                if await self._check_payment_reminder(registration):
                    sent_count += 1
            
            # Check group reminders (if paid but group not open)
            if (registration.get('paid', False) and 
                not registration.get('group_open', False)):
                if await self._check_group_reminder(registration):
                    sent_count += 1
            
            # Check event reminders (if group is open)
            if registration.get('group_open', False):
                if await self._check_event_reminder(registration):
                    sent_count += 1
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error checking reminders for user {user_name}: {e}")
            return 0
    
    async def _check_partner_reminder(self, registration: Dict[str, Any]) -> bool:
        """Check if user needs a partner reminder"""
        submission_id = registration.get('submission_id')
        partner_status = registration.get('partner_status', {})
        missing_partners = partner_status.get('missing_partners', [])
        
        if not missing_partners:
            return False  # No missing partners
        
        # Check if enough time has passed since last reminder
        last_reminder_key = f"{submission_id}_partner"
        
        if self._is_too_soon_for_reminder(last_reminder_key, 'partner_pending'):
            return False
        
        # Send partner reminder
        success = await self._send_automatic_partner_reminder(registration, missing_partners)
        if success:
            self.last_reminder_check[last_reminder_key] = datetime.now()
            logger.info(f"📤 Sent partner reminder to {registration.get('alias', 'Unknown')}")
            
            # Notify admins about partner delay
            await self.admin_service.notify_admins(
                f"🔔 Partner delay: {registration.get('alias', 'Unknown')} still waiting for: {', '.join(missing_partners)}",
                "partner_delays"
            )
        
        return success
    
    async def _check_payment_reminder(self, registration: Dict[str, Any]) -> bool:
        """Check if user needs a payment reminder"""
        submission_id = registration.get('submission_id')
        last_reminder_key = f"{submission_id}_payment"
        
        if self._is_too_soon_for_reminder(last_reminder_key, 'payment_pending'):
            return False
        
        # Send payment reminder
        success = await self._send_automatic_payment_reminder(registration)
        if success:
            self.last_reminder_check[last_reminder_key] = datetime.now()
            logger.info(f"💳 Sent payment reminder to {registration.get('alias', 'Unknown')}")
            
            # Notify admins about payment overdue
            await self.admin_service.notify_admins(
                f"💸 Payment overdue: {registration.get('alias', 'Unknown')} has been approved but hasn't paid yet",
                "payment_overdue"
            )
        
        return success
    
    async def _check_group_reminder(self, registration: Dict[str, Any]) -> bool:
        """Check if user needs a group opening reminder"""
        submission_id = registration.get('submission_id')
        last_reminder_key = f"{submission_id}_group"
        
        # TODO: Check if it's actually 7 days before event
        # For now, use the interval check
        if self._is_too_soon_for_reminder(last_reminder_key, 'group_opening'):
            return False
        
        # Send group opening reminder
        success = await self._send_automatic_group_reminder(registration)
        if success:
            self.last_reminder_check[last_reminder_key] = datetime.now()
            logger.info(f"👥 Sent group reminder to {registration.get('alias', 'Unknown')}")
        
        return success
    
    async def _check_event_reminder(self, registration: Dict[str, Any]) -> bool:
        """Check if user needs an event reminder"""
        # TODO: Implement event reminder logic based on actual event date
        # This would check if it's 1 day before the event
        return False
    
    def _is_too_soon_for_reminder(self, reminder_key: str, interval_key: str) -> bool:
        """Check if enough time has passed since the last reminder"""
        if reminder_key not in self.last_reminder_check:
            return False
        
        time_since_last = (datetime.now() - self.last_reminder_check[reminder_key]).total_seconds()
        return time_since_last < self.intervals[interval_key]
    
    async def _check_weekly_digest(self):
        """Check if it's time to send weekly digest to admins"""
        now = datetime.now()
        
        # Check if enough time has passed since last digest
        if self.last_weekly_digest:
            time_since_last = (now - self.last_weekly_digest).total_seconds()
            if time_since_last < self.intervals['weekly_digest']:
                return  # Too soon for another digest
        
        # Generate and send weekly digest
        try:
            # Use a dummy admin ID - the admin service will handle sending to all admins
            if settings.admin_user_ids:
                admin_id = settings.admin_user_ids[0]
                result = await self.admin_service.generate_weekly_digest(admin_id)
                
                if result['success']:
                    self.last_weekly_digest = now
                    logger.info("📊 Weekly admin digest sent automatically")
                
        except Exception as e:
            logger.error(f"Error sending automatic weekly digest: {e}")
    
    async def _send_automatic_partner_reminder(self, registration: Dict[str, Any], missing_partners: List[str]) -> bool:
        """Send automatic partner reminder to user"""
        telegram_user_id = registration.get('telegram_user_id')
        language = registration.get('language', 'en')
        
        if not telegram_user_id or not self.bot:
            return False
        
        try:
            # Build reminder message
            if language == 'he':
                if len(missing_partners) == 1:
                    message = f"🔔 תזכורת: עדיין מחכים ל{missing_partners[0]} להשלים את הטופס. רוצה לשלוח להם תזכורת? השתמש ב /remind_partner"
                else:
                    missing_names = ', '.join(missing_partners)
                    message = f"🔔 תזכורת: עדיין מחכים ל{missing_names} להשלים את הטופס. השתמש ב /remind_partner"
            else:
                if len(missing_partners) == 1:
                    message = f"🔔 Reminder: Still waiting for {missing_partners[0]} to complete the form. Want to send them a reminder? Use /remind_partner"
                else:
                    missing_names = ', '.join(missing_partners)
                    message = f"🔔 Reminder: Still waiting for {missing_names} to complete the form. Use /remind_partner"
            
            # Send message
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await self._log_automatic_reminder(
                registration.get('submission_id'),
                ', '.join(missing_partners),
                'automatic_partner_reminder'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending automatic partner reminder: {e}")
            return False
    
    async def _send_automatic_payment_reminder(self, registration: Dict[str, Any]) -> bool:
        """Send automatic payment reminder to user"""
        telegram_user_id = registration.get('telegram_user_id')
        language = registration.get('language', 'en')
        
        if not telegram_user_id or not self.bot:
            return False
        
        try:
            # Build reminder message
            if language == 'he':
                message = "💸 תזכורת תשלום: הרשמתך אושרה! אנא השלם את התשלום כדי לאשר את מקומך באירוע."
            else:
                message = "💸 Payment reminder: Your registration has been approved! Please complete payment to confirm your spot at the event."
            
            # Send message
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await self._log_automatic_reminder(
                registration.get('submission_id'),
                '',
                'automatic_payment_reminder'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending automatic payment reminder: {e}")
            return False
    
    async def _send_automatic_group_reminder(self, registration: Dict[str, Any]) -> bool:
        """Send automatic group opening reminder to user"""
        telegram_user_id = registration.get('telegram_user_id')
        language = registration.get('language', 'en')
        
        if not telegram_user_id or not self.bot:
            return False
        
        try:
            # Build reminder message
            if language == 'he':
                message = "👥 הקבוצה פתוחה! קבוצת האירוע שלך פתוחה עכשיו. בואו להכיר או פשוט לצפות בשקט - מה שמתאים לכם! 🧘"
            else:
                message = "👥 Group is open! Your event group is now open. Come meet others, share vibes, or just lurk quietly if that's your vibe! 🧘"
            
            # Send message
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await self._log_automatic_reminder(
                registration.get('submission_id'),
                '',
                'automatic_group_reminder'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending automatic group reminder: {e}")
            return False
    
    async def _log_automatic_reminder(self, submission_id: str, partner_name: str, reminder_type: str) -> bool:
        """Log that an automatic reminder was sent"""
        try:
            timestamp = datetime.now().isoformat()
            
            logger.info(f"📝 Logged automatic reminder: {submission_id} -> {partner_name} ({reminder_type}) at {timestamp}")
            
            # TODO: Implement actual logging to database or Google Sheets
            # This would:
            # - Add a row to a reminders log sheet
            # - Update the main sheet with reminder status
            # - Store in a database table with timestamp
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging automatic reminder: {e}")
            return False
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current status of the background scheduler"""
        return {
            'is_running': self.is_running,
            'last_weekly_digest': self.last_weekly_digest.isoformat() if self.last_weekly_digest else None,
            'total_reminder_checks': len(self.last_reminder_check),
            'intervals': self.intervals,
            'has_bot_application': self.bot is not None
        } 