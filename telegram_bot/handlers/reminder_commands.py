from telegram import Update
from telegram.ext import ContextTypes
import logging

from ..services import ReminderService, MessageService, SheetsService
from ..exceptions import RegistrationNotFoundException, ServiceException

logger = logging.getLogger(__name__)

class ReminderCommandHandler:
    """Handler for reminder-related commands"""
    
    def __init__(self):
        self.reminder_service = ReminderService()
        self.message_service = MessageService()
        self.sheets_service = SheetsService()
        
        # Store user -> submission_id mapping (will be handled better in future)
        self.user_submissions = {}
    
    async def remind_partner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remind_partner command"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            
            # Get the submission ID for this user
            submission_id = self.user_submissions.get(user_id)
            
            # Try to find registration by Telegram User ID or submission ID
            registration = None
            if submission_id:
                registration = await self.sheets_service.find_submission_by_id(submission_id)
            
            if not registration:
                registration = await self.sheets_service.find_submission_by_telegram_id(user_id)
                if registration:
                    submission_id = registration.get('submission_id')
                    self.user_submissions[user_id] = submission_id
            
            if not registration:
                # Use user's language preference or default to English
                language = 'he' if user.language_code == 'he' else 'en'
                message = self.message_service.get_no_submission_linked_message(language)
                await update.message.reply_text(message)
                return
            
            # Send partner reminders using the service
            result = await self.reminder_service.send_partner_reminders(
                submission_id=submission_id,
                telegram_user_id=user_id
            )
            
            # Send response to user
            await update.message.reply_text(result['message'])
            
            logger.info(f"Partner reminder command processed for user {user_id}: "
                       f"{result['reminders_sent']} reminders sent")
            
        except RegistrationNotFoundException as e:
            logger.warning(f"Registration not found for user {user_id}: {e}")
            language = 'he' if update.effective_user.language_code == 'he' else 'en'
            message = self.message_service.get_no_submission_linked_message(language)
            await update.message.reply_text(message)
            
        except ServiceException as e:
            logger.error(f"Service error in remind_partner_command: {e}")
            await update.message.reply_text("❌ Sorry, there was an error processing your request. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in remind_partner_command: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")

# Create global instance for easy import
reminder_handler = ReminderCommandHandler() 