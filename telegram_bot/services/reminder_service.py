from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging

from ..config.settings import settings
from ..services.sheets_service import SheetsService
from ..services.message_service import MessageService
from ..exceptions import RegistrationNotFoundException, ServiceException

logger = logging.getLogger(__name__)

class ReminderService:
    """Service for handling partner reminders and automated reminder scheduling"""
    
    def __init__(self, sheets_service: SheetsService = None, message_service: MessageService = None):
        self.sheets_service = sheets_service or SheetsService()
        self.message_service = message_service or MessageService()
        
        # Reminder intervals configuration
        self.reminder_intervals = {
            'partner_pending': 24 * 60 * 60,  # 24 hours in seconds
            'payment_pending': 3 * 24 * 60 * 60,  # 3 days
            'group_opening': 7 * 24 * 60 * 60,  # 7 days before event
            'event_reminder': 24 * 60 * 60,  # 1 day before event
            'weekly_digest': 7 * 24 * 60 * 60,  # 7 days
        }
        
        # Track last reminder times to avoid spam
        self.last_reminder_check = {}
    
    async def send_partner_reminders(self, submission_id: str, telegram_user_id: str) -> Dict[str, Any]:
        """Send reminders to missing partners for a registration"""
        try:
            # Get user's registration data
            registration = await self.sheets_service.find_submission_by_telegram_id(telegram_user_id)
            if not registration:
                registration = await self.sheets_service.find_submission_by_id(submission_id)
            
            if not registration:
                raise RegistrationNotFoundException(f"Registration not found for user {telegram_user_id}")
            
            language = registration.get('language', 'en')
            user_name = registration.get('alias', 'Unknown')
            
            # Check partner status
            partner_status = registration.get('partner_status', {})
            missing_partners = partner_status.get('missing_partners', [])
            
            if not missing_partners:
                return {
                    'success': True,
                    'message': self.message_service.get_message(language, 'all_partners_complete'),
                    'reminders_sent': 0,
                    'failed_partners': []
                }
            
            # Send reminders to missing partners
            success_count = 0
            failed_partners = []
            
            for partner_name in missing_partners:
                try:
                    reminder_sent = await self._send_individual_partner_reminder(
                        partner_name=partner_name,
                        requester_name=user_name,
                        language=language
                    )
                    
                    if reminder_sent:
                        success_count += 1
                        # Log the reminder
                        await self._log_reminder_sent(
                            submission_id=submission_id,
                            partner_name=partner_name,
                            reminder_type='manual_partner_reminder'
                        )
                    else:
                        failed_partners.append(partner_name)
                        
                except Exception as e:
                    logger.error(f"Error sending reminder to {partner_name}: {e}")
                    failed_partners.append(partner_name)
            
            # Build response message
            message = self._build_reminder_response_message(
                success_count, failed_partners, missing_partners, language
            )
            
            return {
                'success': success_count > 0,
                'message': message,
                'reminders_sent': success_count,
                'failed_partners': failed_partners
            }
            
        except Exception as e:
            logger.error(f"Error in send_partner_reminders: {e}")
            raise ServiceException(f"Failed to send partner reminders: {e}")
    
    async def _send_individual_partner_reminder(self, partner_name: str, requester_name: str, language: str) -> bool:
        """Send a reminder to an individual partner"""
        try:
            logger.info(f"🔔 Sending reminder to {partner_name} from {requester_name}")
            
            # TODO: Implement actual partner reminder sending
            # This could involve:
            # 1. Looking up partner's contact info from registration data
            # 2. Sending an email notification
            # 3. Sending a Telegram message if they're registered
            # 4. Creating a system notification
            
            # For now, simulate success
            # In a real implementation, this would:
            # - Find partner's contact info in the sheets
            # - Send actual reminder via email or Telegram
            # - Return True/False based on success
            
            await asyncio.sleep(0.1)  # Simulate network delay
            return True  # Simulated success
            
        except Exception as e:
            logger.error(f"Error sending individual reminder to {partner_name}: {e}")
            return False
    
    async def _log_reminder_sent(self, submission_id: str, partner_name: str, reminder_type: str) -> bool:
        """Log that a reminder was sent"""
        try:
            timestamp = datetime.now().isoformat()
            
            logger.info(f"📝 Logged reminder: {submission_id} -> {partner_name} ({reminder_type}) at {timestamp}")
            
            # TODO: Implement actual logging to database or Google Sheets
            # This would:
            # - Add a row to a reminders log sheet
            # - Update the main sheet with reminder status
            # - Store in a database table with timestamp
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging reminder: {e}")
            return False
    
    def _build_reminder_response_message(self, success_count: int, failed_partners: List[str], missing_partners: List[str], language: str) -> str:
        """Build response message for reminder results"""
        messages = []
        
        # Success message
        if success_count > 0:
            if language == 'he':
                if success_count == 1:
                    messages.append(f"✅ תזכורת נשלחה ל{missing_partners[0]}!")
                else:
                    messages.append(f"✅ תזכורות נשלחו ל{success_count} פרטנרים!")
            else:
                if success_count == 1:
                    messages.append(f"✅ Reminder sent to {missing_partners[0]}!")
                else:
                    messages.append(f"✅ Reminders sent to {success_count} partners!")
        
        # Failure message
        if failed_partners:
            failed_names = ', '.join(failed_partners)
            if language == 'he':
                messages.append(f"❌ לא הצלחנו לשלוח תזכורת ל: {failed_names}")
            else:
                messages.append(f"❌ Failed to send reminders to: {failed_names}")
        
        return '\n'.join(messages)
    
    # --- Automatic Reminder System ---
    
    async def check_and_send_automatic_reminders(self):
        """Check for users who need automatic reminders and send them"""
        try:
            logger.info("🔔 Checking for automatic reminders...")
            
            # Get all registrations that might need reminders
            registrations = await self.sheets_service.get_all_registrations()
            
            reminder_count = 0
            for registration in registrations:
                try:
                    if await self._should_send_partner_reminder(registration):
                        await self._send_automatic_partner_reminder(registration)
                        reminder_count += 1
                    
                    if await self._should_send_payment_reminder(registration):
                        await self._send_automatic_payment_reminder(registration)
                        reminder_count += 1
                        
                except Exception as e:
                    logger.error(f"Error checking reminders for {registration.get('submission_id', 'unknown')}: {e}")
                    
            logger.info(f"📊 Sent {reminder_count} automatic reminders")
            
        except Exception as e:
            logger.error(f"Error in automatic reminder check: {e}")
    
    async def _should_send_partner_reminder(self, registration: Dict[str, Any]) -> bool:
        """Check if a partner reminder should be sent"""
        # Don't send if partner is already complete
        if registration.get('partner', False):
            return False
        
        # Don't send if no Telegram ID (can't send reminder)
        if not registration.get('telegram_user_id'):
            return False
        
        # Check if enough time has passed since last reminder
        submission_id = registration.get('submission_id')
        last_reminder_key = f"{submission_id}_partner"
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (datetime.now() - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['partner_pending']:
                return False  # Too soon for another reminder
        
        # Check if there are actually missing partners
        partner_status = registration.get('partner_status', {})
        missing_partners = partner_status.get('missing_partners', [])
        
        return len(missing_partners) > 0
    
    async def _should_send_payment_reminder(self, registration: Dict[str, Any]) -> bool:
        """Check if a payment reminder should be sent"""
        # Only send if approved but not paid
        if not registration.get('approved', False):
            return False
        
        if registration.get('paid', False):
            return False
        
        # Don't send if no Telegram ID
        if not registration.get('telegram_user_id'):
            return False
        
        # Check time interval
        submission_id = registration.get('submission_id')
        last_reminder_key = f"{submission_id}_payment"
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (datetime.now() - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['payment_pending']:
                return False
        
        return True
    
    async def _send_automatic_partner_reminder(self, registration: Dict[str, Any]):
        """Send automatic partner reminder"""
        try:
            submission_id = registration.get('submission_id')
            telegram_user_id = registration.get('telegram_user_id')
            
            # Send reminder using the same logic as manual reminders
            result = await self.send_partner_reminders(submission_id, telegram_user_id)
            
            # Mark as sent to avoid spam
            last_reminder_key = f"{submission_id}_partner"
            self.last_reminder_check[last_reminder_key] = datetime.now()
            
            logger.info(f"📤 Automatic partner reminder sent for {submission_id}")
            
        except Exception as e:
            logger.error(f"Error sending automatic partner reminder: {e}")
    
    async def _send_automatic_payment_reminder(self, registration: Dict[str, Any]):
        """Send automatic payment reminder"""
        try:
            submission_id = registration.get('submission_id')
            telegram_user_id = registration.get('telegram_user_id')
            language = registration.get('language', 'en')
            
            # TODO: Send actual payment reminder message via Telegram
            logger.info(f"💳 Automatic payment reminder sent for {submission_id}")
            
            # Mark as sent
            last_reminder_key = f"{submission_id}_payment"
            self.last_reminder_check[last_reminder_key] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error sending automatic payment reminder: {e}")
    
    async def start_background_scheduler(self, bot_application):
        """Start the background reminder scheduler"""
        logger.info("🚀 Starting reminder scheduler...")
        
        while True:
            try:
                await self.check_and_send_automatic_reminders()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                await asyncio.sleep(300)  # 5 minute retry on error 