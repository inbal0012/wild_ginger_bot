#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wild Ginger Bot - Direct Runner
This version can be run directly without package imports
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Import our refactored components (absolute imports)
from telegram_bot.config import settings
from telegram_bot.services import SheetsService, MessageService, ReminderService, ConversationService, AdminService, BackgroundScheduler, CancellationService, MonitoringService
from telegram_bot.models.registration import RegistrationStatus
from telegram_bot.exceptions import RegistrationNotFoundException, SheetsConnectionException
from telegram_bot.handlers import reminder_handler, conversation_handler, admin_handler, cancellation_handler, monitoring_handler

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
                    
                    # Get user status
                    status_data = await self.sheets_service.find_submission_by_telegram_id(user_id)
                    if status_data:
                        # Continue conversation with status
                        await self._continue_conversation(update, status_data)
                    else:
                        await update.message.reply_text(
                            self.message_service.get_message('en', 'submission_not_found', submission_id=submission_id)
                        )
                except Exception as e:
                    logger.error(f"Error linking user {user_id} to submission {submission_id}: {e}")
                    await update.message.reply_text(
                        self.message_service.get_message('en', 'error_linking_submission')
                    )
            else:
                # No submission ID provided, check if user is already linked
                status_data = await self.sheets_service.find_submission_by_telegram_id(user_id)
                if status_data:
                    await self._continue_conversation(update, status_data)
                else:
                    await update.message.reply_text(
                        self.message_service.get_message('en', 'no_submission_linked')
                    )
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                self.message_service.get_message('en', 'general_error')
            )
    
    async def _continue_conversation(self, update: Update, status_data: dict):
        """Continue conversation based on user status"""
        user = update.effective_user
        language = user.language_code or 'en'
        
        # Welcome message
        welcome_msg = self.message_service.get_message(
            language, 'welcome', name=status_data.get('alias', 'User')
        )
        
        # Build status message
        status_msg = self.message_service.build_status_message(status_data, language)
        
        # Combine messages
        full_message = f"{welcome_msg}\n\n{status_msg}"
        await update.message.reply_text(full_message)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            language = user.language_code or 'en'
            
            status_data = await self.sheets_service.find_submission_by_telegram_id(user_id)
            if status_data:
                status_msg = self.message_service.build_status_message(status_data, language)
                await update.message.reply_text(status_msg)
            else:
                await update.message.reply_text(
                    self.message_service.get_message(language, 'no_submission_linked')
                )
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(
                self.message_service.get_message('en', 'general_error')
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            user = update.effective_user
            language = user.language_code or 'en'
            
            help_msg = self.message_service.get_message(language, 'help')
            await update.message.reply_text(help_msg)
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text(
                self.message_service.get_message('en', 'general_error')
            )
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in settings.admin_user_ids
    
    async def setup_bot_commands(self):
        """Set up bot commands"""
        commands = [
            BotCommand("start", "Start the bot and link your registration"),
            BotCommand("status", "Check your registration status"),
            BotCommand("help", "Show help information"),
            BotCommand("remind_partner", "Send reminder to your partner"),
            BotCommand("get_to_know", "Start get-to-know conversation"),
            BotCommand("cancel", "Cancel your registration"),
        ]
        
        # Add admin commands
        admin_commands = [
            BotCommand("admin_dashboard", "Admin dashboard"),
            BotCommand("admin_approve", "Approve registration"),
            BotCommand("admin_reject", "Reject registration"),
            BotCommand("admin_status", "Check admin status"),
            BotCommand("admin_digest", "Generate weekly digest"),
            BotCommand("admin_cancel", "Admin cancel registration"),
            BotCommand("admin_cancel_stats", "Cancellation statistics"),
            BotCommand("admin_monitoring_status", "Monitoring status"),
            BotCommand("admin_manual_check", "Manual monitoring check"),
            BotCommand("admin_start_monitoring", "Start monitoring"),
            BotCommand("admin_stop_monitoring", "Stop monitoring"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        logger.info("Bot commands set up successfully")
    
    async def run(self):
        """Run the bot"""
        try:
            # Set up bot commands
            await self.setup_bot_commands()
            
            # Start background services
            await self.background_scheduler.start()
            await self.monitoring_service.start_monitoring()
            
            logger.info("🚀 Wild Ginger Bot starting...")
            logger.info(f"📊 Admin users: {settings.admin_user_ids}")
            logger.info(f"📋 Google Sheets enabled: {settings.google_sheets_enabled}")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Error running bot: {e}")
            raise
        finally:
            # Cleanup
            try:
                await self.background_scheduler.stop()
                await self.monitoring_service.stop_monitoring()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

async def main():
    """Main async function"""
    bot = WildGingerBot()
    await bot.run()

def run_bot():
    """Entry point for running the bot"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_bot() 