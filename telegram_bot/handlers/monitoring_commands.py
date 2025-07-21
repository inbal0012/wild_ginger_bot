from telegram import Update
from telegram.ext import ContextTypes
import logging

from ..services import MonitoringService, AdminService
from ..exceptions import ServiceException

logger = logging.getLogger(__name__)

class MonitoringCommandHandler:
    """Handler for sheet monitoring admin commands"""
    
    def __init__(self):
        self.monitoring_service = MonitoringService()
        self.admin_service = AdminService()
    
    def set_bot_application(self, bot_application):
        """Set bot application for the monitoring service"""
        self.monitoring_service.set_bot_application(bot_application)
    
    async def admin_monitoring_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_monitoring_status command to show monitoring status"""
        try:
            user = update.effective_user
            admin_user_id = user.id
            
            # Check admin permissions
            if not self.admin_service.is_admin(admin_user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Show loading message
            status_message = await update.message.reply_text("📊 Loading monitoring status...")
            
            # Get monitoring status
            status = await self.monitoring_service.get_monitoring_status()
            
            # Format status message
            status_text = self._format_monitoring_status(status)
            
            # Update message with status
            await status_message.edit_text(status_text)
            
            logger.info(f"Monitoring status requested by admin {admin_user_id}")
            
        except ServiceException as e:
            logger.error(f"Service error getting monitoring status: {e}")
            await update.message.reply_text("❌ Error loading monitoring status. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in monitoring status command: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    async def admin_manual_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_manual_check command to manually trigger monitoring check"""
        try:
            user = update.effective_user
            admin_user_id = user.id
            admin_name = user.first_name or "Admin"
            
            # Check admin permissions
            if not self.admin_service.is_admin(admin_user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Show processing message
            status_message = await update.message.reply_text("🔍 Manually checking for new registrations...")
            
            # Perform manual check
            result = await self.monitoring_service.manual_check()
            
            # Update message with result
            await status_message.edit_text(result['message'])
            
            if result['success']:
                logger.info(f"Manual monitoring check triggered by admin {admin_name} ({admin_user_id})")
            else:
                logger.warning(f"Manual monitoring check failed for admin {admin_name} ({admin_user_id})")
            
        except ServiceException as e:
            logger.error(f"Service error in manual check: {e}")
            await update.message.reply_text("❌ Error performing manual check. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error in manual check command: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    async def admin_start_monitoring_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_start_monitoring command to start sheet monitoring"""
        try:
            user = update.effective_user
            admin_user_id = user.id
            admin_name = user.first_name or "Admin"
            
            # Check admin permissions
            if not self.admin_service.is_admin(admin_user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Show processing message
            status_message = await update.message.reply_text("🔄 Starting sheet monitoring...")
            
            # Start monitoring
            await self.monitoring_service.start_monitoring()
            
            # Update message
            await status_message.edit_text("✅ Sheet monitoring started successfully! Checking every 5 minutes for new registrations.")
            
            logger.info(f"Sheet monitoring started by admin {admin_name} ({admin_user_id})")
            
        except ServiceException as e:
            logger.error(f"Service error starting monitoring: {e}")
            await update.message.reply_text("❌ Error starting monitoring. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error starting monitoring: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    async def admin_stop_monitoring_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_stop_monitoring command to stop sheet monitoring"""
        try:
            user = update.effective_user
            admin_user_id = user.id
            admin_name = user.first_name or "Admin"
            
            # Check admin permissions
            if not self.admin_service.is_admin(admin_user_id):
                await update.message.reply_text("❌ Access denied. Admin privileges required.")
                return
            
            # Show processing message
            status_message = await update.message.reply_text("⏹️ Stopping sheet monitoring...")
            
            # Stop monitoring
            await self.monitoring_service.stop_monitoring()
            
            # Update message
            await status_message.edit_text("⏹️ Sheet monitoring stopped successfully.")
            
            logger.info(f"Sheet monitoring stopped by admin {admin_name} ({admin_user_id})")
            
        except ServiceException as e:
            logger.error(f"Service error stopping monitoring: {e}")
            await update.message.reply_text("❌ Error stopping monitoring. Please try again later.")
            
        except Exception as e:
            logger.error(f"Unexpected error stopping monitoring: {e}")
            await update.message.reply_text("❌ An unexpected error occurred. Please contact support.")
    
    def _format_monitoring_status(self, status: dict) -> str:
        """Format monitoring status into a readable message"""
        message = f"📊 **Sheet Monitoring Status**\n\n"
        
        # Basic status
        status_emoji = "🟢" if status['is_monitoring'] else "🔴"
        status_text = "Active" if status['is_monitoring'] else "Stopped"
        message += f"**Status:** {status_emoji} {status_text}\n\n"
        
        # Configuration details
        message += f"**Configuration:**\n"
        message += f"• Check Interval: {status['monitoring_interval']//60} minutes\n"
        message += f"• Sheet1 Range: {status['sheet1_range']}\n"
        message += f"• Admin Count: {status['admin_count']}\n"
        message += f"• Column Mappings: {status['column_mappings_count']}\n\n"
        
        # System status
        message += f"**System Status:**\n"
        sheets_emoji = "✅" if status['sheets_service_available'] else "❌"
        message += f"• Google Sheets: {sheets_emoji}\n"
        
        bot_emoji = "✅" if status['has_bot_application'] else "❌"
        message += f"• Bot Notifications: {bot_emoji}\n\n"
        
        # Help text
        message += f"**Commands:**\n"
        message += f"• `/admin_manual_check` - Check now\n"
        message += f"• `/admin_start_monitoring` - Start monitoring\n"
        message += f"• `/admin_stop_monitoring` - Stop monitoring"
        
        return message

# Create global instance for easy import
monitoring_handler = MonitoringCommandHandler() 