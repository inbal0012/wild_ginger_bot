from telegram import Update
from telegram.ext import ContextTypes
import logging

from ..services import CancellationService, SheetsService, MessageService
from ..exceptions import ServiceException, RegistrationNotFoundException

logger = logging.getLogger(__name__)

class CancellationCommandHandler:
    """Handler for cancellation-related commands"""
    
    def __init__(self):
        self.cancellation_service = CancellationService()
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
    
    async def cancel_registration_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command for user registration cancellation"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Get reason from command arguments
            reason = " ".join(context.args) if context.args else ""
            
            # Determine user language
            language_code = 'he' if user.language_code == 'he' else 'en'
            
            # Show processing message
            status_message = await update.message.reply_text("🔄 Processing cancellation...")
            
            # Process cancellation
            result = await self.cancellation_service.cancel_user_registration(
                user_id=user_id,
                reason=reason,
                language_code=language_code
            )
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            # Log the result
            if result['success']:
                logger.info(f"User {user_id} successfully cancelled registration: {reason}")
                
                # If it was last minute, log additional details
                if result.get('is_last_minute'):
                    logger.warning(f"Last-minute cancellation by user {user_id} for {result.get('submission_id')}")
            else:
                logger.warning(f"Failed cancellation attempt by user {user_id}")
                
                # If they need to provide a reason, give helpful hint
                if result.get('requires_reason'):
                    logger.info(f"User {user_id} needs to provide cancellation reason")
            
        except ServiceException as e:
            logger.error(f"Service error in cancellation: {e}")
            await update.message.reply_text("❌ An error occurred while processing your cancellation. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in cancel command: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    async def admin_cancel_registration_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_cancel command for admin-initiated cancellations"""
        try:
            user = update.effective_user
            admin_user_id = user.id
            admin_name = user.first_name or "Admin"
            
            # Check if admin provided submission ID and reason
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Usage: `/admin_cancel SUBM_12345 reason for cancellation`"
                )
                return
            
            submission_id = context.args[0]
            reason = " ".join(context.args[1:])
            
            # Show processing message
            status_message = await update.message.reply_text(f"🔄 Processing admin cancellation for {submission_id}...")
            
            # Process admin cancellation
            result = await self.cancellation_service.admin_cancel_registration(
                submission_id=submission_id,
                reason=reason,
                admin_user_id=admin_user_id,
                is_last_minute=True  # Admin cancellations are often last minute
            )
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            if result['success']:
                logger.info(f"Admin {admin_name} ({admin_user_id}) cancelled registration {submission_id}: {reason}")
            else:
                logger.warning(f"Admin {admin_name} failed to cancel registration {submission_id}")
            
        except ServiceException as e:
            logger.error(f"Service error in admin cancellation: {e}")
            await update.message.reply_text("❌ Error processing admin cancellation. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in admin cancel command: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    async def get_cancellation_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_cancel_stats command to show cancellation statistics"""
        try:
            user = update.effective_user
            admin_user_id = user.id
            
            # TODO: Add admin permission check here
            # For now, anyone can see stats
            
            # Show loading message
            status_message = await update.message.reply_text("📊 Loading cancellation statistics...")
            
            # Get statistics
            stats = await self.cancellation_service.get_cancellation_statistics()
            
            # Format statistics message
            stats_message = self._format_cancellation_stats(stats)
            
            # Update message with statistics
            await status_message.edit_text(stats_message)
            
            logger.info(f"Cancellation statistics requested by {admin_user_id}")
            
        except ServiceException as e:
            logger.error(f"Service error getting cancellation stats: {e}")
            await update.message.reply_text("❌ Error loading statistics. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error getting cancellation stats: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    def _format_cancellation_stats(self, stats: dict) -> str:
        """Format cancellation statistics into a readable message"""
        message = f"📊 **Cancellation Statistics**\n\n"
        message += f"**Overview:**\n"
        message += f"• Total Registrations: {stats['total_registrations']}\n"
        message += f"• Total Cancellations: {stats['total_cancellations']}\n"
        message += f"• Last-Minute Cancellations: {stats['last_minute_cancellations']}\n\n"
        
        message += f"**Rates:**\n"
        message += f"• Cancellation Rate: {stats['cancellation_rate']:.1%}\n"
        message += f"• Last-Minute Rate: {stats['last_minute_rate']:.1%}\n\n"
        
        if stats['cancellation_reasons']:
            message += f"**Top Cancellation Reasons:**\n"
            # Sort reasons by frequency
            sorted_reasons = sorted(
                stats['cancellation_reasons'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            for reason, count in sorted_reasons[:5]:  # Show top 5
                message += f"• {reason}: {count}\n"
        
        return message

# Create global instance for easy import
cancellation_handler = CancellationCommandHandler() 