from telegram import Update
from telegram.ext import ContextTypes
import logging

from ..services import AdminService, SheetsService, MessageService
from ..exceptions import UnauthorizedOperationException, ServiceException, RegistrationNotFoundException

logger = logging.getLogger(__name__)

class AdminCommandHandler:
    """Handler for admin-related commands"""
    
    def __init__(self):
        self.admin_service = AdminService()
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
    
    async def admin_dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_dashboard command"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Check admin privileges
            if not self.admin_service.is_admin(user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Show loading message
            status_message = await update.message.reply_text("🔄 Loading dashboard...")
            
            # Get dashboard data
            dashboard_data = await self.admin_service.get_dashboard_stats(user_id)
            
            # Format and send dashboard
            dashboard_message = self.admin_service.format_dashboard_message(dashboard_data)
            
            # Update the status message with dashboard
            await status_message.edit_text(dashboard_message)
            
            logger.info(f"Admin dashboard displayed for user {user_id} ({user.first_name})")
            
        except UnauthorizedOperationException as e:
            logger.warning(f"Unauthorized admin dashboard access attempt by {user_id}: {e}")
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            
        except ServiceException as e:
            logger.error(f"Service error in admin dashboard: {e}")
            await update.message.reply_text("❌ Error loading dashboard. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in admin dashboard: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")
    
    async def admin_approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_approve command"""
        try:
            user = update.effective_user
            user_id = user.id
            admin_name = user.first_name or "Admin"
            
            # Check admin privileges
            if not self.admin_service.is_admin(user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Check arguments
            if not context.args:
                await update.message.reply_text("❌ Usage: `/admin_approve SUBM_12345`")
                return
            
            submission_id = context.args[0]
            
            # Show processing message
            status_message = await update.message.reply_text(f"🔄 Processing approval for {submission_id}...")
            
            # Approve the registration
            result = await self.admin_service.approve_registration(submission_id, user_id, admin_name)
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            if result['success']:
                logger.info(f"Registration {submission_id} approved by admin {user_id} ({admin_name})")
            else:
                logger.warning(f"Failed to approve registration {submission_id} by admin {user_id}")
            
        except UnauthorizedOperationException as e:
            logger.warning(f"Unauthorized admin approve access attempt by {user_id}: {e}")
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            
        except ServiceException as e:
            logger.error(f"Service error in admin approve: {e}")
            await update.message.reply_text(f"❌ Error approving registration. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in admin approve: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")
    
    async def admin_reject_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_reject command"""
        try:
            user = update.effective_user
            user_id = user.id
            admin_name = user.first_name or "Admin"
            
            # Check admin privileges
            if not self.admin_service.is_admin(user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Check arguments
            if not context.args:
                await update.message.reply_text("❌ Usage: `/admin_reject SUBM_12345 [reason]`")
                return
            
            submission_id = context.args[0]
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
            
            # Show processing message
            status_message = await update.message.reply_text(f"🔄 Processing rejection for {submission_id}...")
            
            # Reject the registration
            result = await self.admin_service.reject_registration(submission_id, reason, user_id, admin_name)
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            if result['success']:
                logger.info(f"Registration {submission_id} rejected by admin {user_id} ({admin_name}) - Reason: {reason}")
            else:
                logger.warning(f"Failed to reject registration {submission_id} by admin {user_id}")
            
        except UnauthorizedOperationException as e:
            logger.warning(f"Unauthorized admin reject access attempt by {user_id}: {e}")
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            
        except ServiceException as e:
            logger.error(f"Service error in admin reject: {e}")
            await update.message.reply_text(f"❌ Error rejecting registration. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in admin reject: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")
    
    async def admin_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_status command"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Check admin privileges
            if not self.admin_service.is_admin(user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Check arguments
            if not context.args:
                await update.message.reply_text("❌ Usage: `/admin_status SUBM_12345`")
                return
            
            submission_id = context.args[0]
            
            # Show loading message
            status_message = await update.message.reply_text(f"🔄 Loading status for {submission_id}...")
            
            # Get registration status
            result = await self.admin_service.get_registration_status(submission_id, user_id)
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            if result['success']:
                logger.info(f"Admin {user_id} checked status for registration {submission_id}")
            else:
                logger.warning(f"Admin {user_id} failed to get status for registration {submission_id}")
            
        except UnauthorizedOperationException as e:
            logger.warning(f"Unauthorized admin status access attempt by {user_id}: {e}")
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            
        except ServiceException as e:
            logger.error(f"Service error in admin status: {e}")
            await update.message.reply_text(f"❌ Error loading registration status. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in admin status: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")
    
    async def admin_digest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_digest command"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Check admin privileges
            if not self.admin_service.is_admin(user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Show processing message
            status_message = await update.message.reply_text("📊 Generating weekly digest...")
            
            # Generate and send digest
            result = await self.admin_service.generate_weekly_digest(user_id)
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            if result['success']:
                logger.info(f"Weekly digest generated by admin {user_id} ({user.first_name})")
            else:
                logger.warning(f"Failed to generate weekly digest by admin {user_id}")
            
        except UnauthorizedOperationException as e:
            logger.warning(f"Unauthorized admin digest access attempt by {user_id}: {e}")
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            
        except ServiceException as e:
            logger.error(f"Service error in admin digest: {e}")
            await update.message.reply_text(f"❌ Error generating digest. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in admin digest: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")

# Create global instance for easy import
admin_handler = AdminCommandHandler() 