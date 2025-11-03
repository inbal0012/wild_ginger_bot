"""
Wild Ginger Bot - Refactored Main Entry Point

This is the main bot file using the new modular architecture.
All services are now properly separated and use dependency injection.
"""

import asyncio
import logging
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters


# Import our refactored components
from .config import settings
from .services import SheetsService, MessageService, ReminderService, ConversationService, AdminService, BackgroundScheduler, CancellationService, MonitoringService
from .models.registration import RegistrationStatus
from .exceptions import RegistrationNotFoundException, SheetsConnectionException
from .handlers import reminder_handler, conversation_handler, admin_handler, cancellation_handler, monitoring_handler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WildGingerBot:
    def __init__(self):
        # Initialize services
        self.sheets_service = SheetsService()
        self.message_service = MessageService()
        self.background_scheduler = BackgroundScheduler()
        self.monitoring_service = MonitoringService()
        
        # Initialize bot application
        if not settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
            
        self.application = ApplicationBuilder().token(settings.telegram_bot_token).build()
        
        # Set bot application for background services
        self.background_scheduler.set_bot_application(self.application)
        self.monitoring_service.set_bot_application(self.application)
        monitoring_handler.set_bot_application(self.application)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all bot command handlers"""
        # User commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("remind_partner", reminder_handler.remind_partner_command))
        self.application.add_handler(CommandHandler("get_to_know", conversation_handler.get_to_know_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin_dashboard", admin_handler.admin_dashboard_command))
        self.application.add_handler(CommandHandler("admin_approve", admin_handler.admin_approve_command))
        self.application.add_handler(CommandHandler("admin_reject", admin_handler.admin_reject_command))
        self.application.add_handler(CommandHandler("admin_status", admin_handler.admin_status_command))
        self.application.add_handler(CommandHandler("admin_digest", admin_handler.admin_digest_command))
        self.application.add_handler(CommandHandler("admin_cancel", cancellation_handler.admin_cancel_registration_command))
        self.application.add_handler(CommandHandler("admin_cancel_stats", cancellation_handler.get_cancellation_stats_command))
        
        # Monitoring admin commands
        self.application.add_handler(CommandHandler("admin_monitoring_status", monitoring_handler.admin_monitoring_status_command))
        self.application.add_handler(CommandHandler("admin_manual_check", monitoring_handler.admin_manual_check_command))
        self.application.add_handler(CommandHandler("admin_start_monitoring", monitoring_handler.admin_start_monitoring_command))
        self.application.add_handler(CommandHandler("admin_stop_monitoring", monitoring_handler.admin_stop_monitoring_command))
        
        # User commands
        self.application.add_handler(CommandHandler("cancel", cancellation_handler.cancel_registration_command))
        
        # Message handler for conversation flow (must be after command handlers)
        from telegram.ext import MessageHandler, filters
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            conversation_handler.handle_conversation_message
        ))
        
        # Log registered admin users
        for admin_id in settings.admin_user_ids:
            logger.info(f"Admin user registered: {admin_id}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            
            # Check if submission ID was provided
            args = context.args
            if args and args[0].startswith('SUBM_'):
                submission_id = args[0]
                try:
                    # Try to link the user to their submission
                    await self.sheets_service.update_telegram_user_id(submission_id, user_id)
                    
                    # Get the submission data
                    submission = await self.sheets_service.find_submission_by_id(submission_id)
                    if submission:
                        language = submission.get('language', 'en')
                        name = submission.get('alias', user.first_name)
                        welcome_message = self.message_service.get_welcome_message(language, name)
                    else:
                        welcome_message = self.message_service.get_submission_not_found_message('en', submission_id)
                        
                except SheetsConnectionException as e:
                    logger.error(f"Sheets connection error: {e}")
                    welcome_message = "⚠️ Connection to registration system failed. Please try again later."
            else:
                # No submission ID provided, try to find existing registration
                try:
                    submission = await self.sheets_service.find_submission_by_telegram_id(user_id)
                    if submission:
                        language = submission.get('language', 'en')
                        name = submission.get('alias', user.first_name)
                        welcome_message = self.message_service.get_welcome_message(language, name)
                    else:
                        welcome_message = self.message_service.get_no_submission_linked_message('en')
                except SheetsConnectionException:
                    welcome_message = self.message_service.get_no_submission_linked_message('en')
            
            await update.message.reply_text(welcome_message)
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again later.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            
            # Find user's registration
            submission = await self.sheets_service.find_submission_by_telegram_id(user_id)
            
            if not submission:
                message = self.message_service.get_no_submission_linked_message('en')
                await update.message.reply_text(message)
                return
            
            # Build status message
            language = submission.get('language', 'en')
            status_message = self.message_service.build_status_message(submission, language)
            
            await update.message.reply_text(status_message)
            
        except SheetsConnectionException as e:
            logger.error(f"Sheets connection error in status: {e}")
            await update.message.reply_text("⚠️ Connection to registration system failed. Please try again later.")
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again later.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            # Try to get user's language preference
            user_id = str(update.effective_user.id)
            language = 'en'
            
            try:
                submission = await self.sheets_service.find_submission_by_telegram_id(user_id)
                if submission:
                    language = submission.get('language', 'en')
            except SheetsConnectionException:
                pass  # Use default language
            
            help_message = self.message_service.get_help_message(language)
            await update.message.reply_text(help_message)
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            # Fallback to English help
            help_message = self.message_service.get_help_message('en')
            await update.message.reply_text(help_message)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in settings.admin_user_ids
    
    async def setup_bot_commands(self):
        """Set up bot command menu"""
        commands = [
            BotCommand("start", "Link your registration"),
            BotCommand("status", "Check registration progress"),
            BotCommand("remind_partner", "Send reminder to partner"),
            BotCommand("get_to_know", "Complete get-to-know section"),
            BotCommand("cancel", "Cancel your registration"),
            BotCommand("admin_dashboard", "Admin: View dashboard"),
            BotCommand("admin_approve", "Admin: Approve registration"),
            BotCommand("admin_reject", "Admin: Reject registration"),
            BotCommand("admin_status", "Admin: Check status"),
            BotCommand("admin_digest", "Admin: Weekly digest"),
            BotCommand("admin_cancel", "Admin: Cancel registration"),
            BotCommand("admin_cancel_stats", "Admin: Cancellation statistics"),
            BotCommand("admin_monitoring_status", "Admin: Sheet monitoring status"),
            BotCommand("admin_manual_check", "Admin: Manual monitoring check"),
            BotCommand("admin_start_monitoring", "Admin: Start monitoring"),
            BotCommand("admin_stop_monitoring", "Admin: Stop monitoring"),
            BotCommand("help", "Show available commands"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands set up successfully")
    
    async def run(self):
        """Start the bot"""
        try:
            # Set up bot commands
            await self.setup_bot_commands()
            
            # Start the bot
            logger.info("🤖 Starting Wild Ginger Bot...")
            logger.info(f"🔧 Google Sheets: {'✅ Connected' if self.sheets_service.spreadsheet else '❌ Not connected'}")
            logger.info(f"👑 Admins configured: {len(settings.admin_user_ids)}")
            
            # Start background services
            await self.background_scheduler.start_background_scheduler()
            logger.info("🔄 Background scheduler started")
            
            await self.monitoring_service.start_monitoring()
            logger.info("🔍 Sheet monitoring started")
            
            # Use run_polling without await to avoid event loop issues
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            # Clean up background services
            await self.background_scheduler.stop_background_scheduler()
            await self.monitoring_service.stop_monitoring()
            raise
        finally:
            # Ensure background services are stopped on exit
            await self.background_scheduler.stop_background_scheduler()
            await self.monitoring_service.stop_monitoring()

    def start_simple(self):
        """Simple start method that avoids async issues"""
        try:
            # Set up bot commands synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Set up commands
            loop.run_until_complete(self.setup_bot_commands())
            
            logger.info("🤖 Starting Wild Ginger Bot...")
            logger.info(f"🔧 Google Sheets: {'✅ Connected' if self.sheets_service.spreadsheet else '❌ Not connected'}")
            logger.info(f"👑 Admins configured: {len(settings.admin_user_ids)}")
            logger.info("🔄 Background services will start after bot initialization")
            logger.info("🔍 Sheet monitoring will be active")
            
            # Start the bot polling (this will handle its own event loop)
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            raise

async def main():
    """Main entry point"""
    try:
        bot = WildGingerBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

def run_bot():
    """Entry point that handles event loop properly"""
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            logger.info("🔄 Detected running event loop, using alternative approach...")
            try:
                # Try to install and use nest-asyncio
                import nest_asyncio
                nest_asyncio.apply()
                asyncio.run(main())
            except ImportError:
                logger.error("❌ nest-asyncio not available")
                logger.info("💡 Install it with: pip install nest-asyncio")
                raise e
            except Exception as nested_e:
                logger.error(f"❌ Alternative approach failed: {nested_e}")
                raise e
        else:
            raise e
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")
        raise e

if __name__ == "__main__":
    run_bot() 