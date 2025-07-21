from telegram import Update
from telegram.ext import ContextTypes
import logging

from ..services import ConversationService, MessageService, SheetsService
from ..exceptions import RegistrationNotFoundException, ServiceException, ConversationStateException

logger = logging.getLogger(__name__)

class ConversationCommandHandler:
    """Handler for conversation-related commands and responses"""
    
    def __init__(self):
        self.conversation_service = ConversationService()
        self.message_service = MessageService()
        self.sheets_service = SheetsService()
    
    async def get_to_know_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get_to_know command"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            
            # Start the get-to-know flow
            result = await self.conversation_service.start_get_to_know_flow(user_id)
            
            # Send response to user
            await update.message.reply_text(result['message'])
            
            if result['success']:
                logger.info(f"Get-to-know flow started for user {user_id}")
            else:
                logger.info(f"Get-to-know flow not started for user {user_id}: {result.get('reason', 'unknown')}")
            
        except RegistrationNotFoundException as e:
            logger.warning(f"Registration not found for user {user_id}: {e}")
            language = 'he' if update.effective_user.language_code == 'he' else 'en'
            message = self.message_service.get_no_submission_linked_message(language)
            await update.message.reply_text(message)
            
        except ServiceException as e:
            logger.error(f"Service error in get_to_know_command: {e}")
            await update.message.reply_text("❌ Sorry, there was an error starting the conversation. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in get_to_know_command: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")
    
    async def handle_conversation_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages that might be part of a conversation flow"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            message_text = update.message.text.strip()
            
            # Check if user is in a conversation flow
            if not self.conversation_service.is_in_conversation(user_id):
                # Not in conversation, don't handle
                return False
            
            # Handle the response based on conversation state
            result = await self.conversation_service.handle_get_to_know_response(
                user_id, message_text
            )
            
            if not result.get('success', False):
                # Not in conversation anymore or error
                return result.get('in_conversation', False)
            
            # Send response to user
            await update.message.reply_text(result['message'])
            
            # Check if conversation is completed and should continue to next step
            if result.get('completed', False) and result.get('should_continue_conversation', False):
                await self._continue_after_get_to_know(update, user_id)
            
            logger.info(f"Handled conversation message for user {user_id}: {result.get('state', 'unknown')}")
            return True
            
        except ServiceException as e:
            logger.error(f"Service error handling conversation message: {e}")
            await update.message.reply_text("❌ Sorry, there was an error processing your response. Please try again.")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error handling conversation message: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again.")
            return True
    
    async def _continue_after_get_to_know(self, update: Update, user_id: str):
        """Continue conversation after get-to-know completion"""
        try:
            # Get updated registration status
            registration = await self.sheets_service.find_submission_by_telegram_id(user_id)
            if not registration:
                return
            
            # Build next steps message using message service
            status_message = self.message_service.build_status_message(registration)
            next_steps = self.message_service.get_next_steps_message(registration)
            
            # Send next steps
            if next_steps:
                await update.message.reply_text(next_steps)
                
        except Exception as e:
            logger.error(f"Error continuing conversation after get-to-know: {e}")
            # Don't send error message to user as the main flow already completed successfully
    
    def is_user_in_conversation(self, user_id: str) -> bool:
        """Check if user is currently in a conversation"""
        return self.conversation_service.is_in_conversation(user_id)

# Create global instance for easy import
conversation_handler = ConversationCommandHandler() 