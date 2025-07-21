#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal Wild Ginger Bot Runner
Starts only the core bot functionality without background services
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the minimal bot"""
    try:
        # Import the bot components
        from telegram_bot.config import settings
        from telegram_bot.services import SheetsService, MessageService
        from telegram_bot.handlers import reminder_handler, conversation_handler, admin_handler, cancellation_handler, monitoring_handler
        
        from telegram import Update, BotCommand
        from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
        
        print("🚀 Starting Minimal Wild Ginger Bot...")
        
        # Initialize core services only
        sheets_service = SheetsService()
        message_service = MessageService()
        
        # Initialize bot application
        if not settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
            
        application = ApplicationBuilder().token(settings.telegram_bot_token).build()
        
        # Register handlers
        def register_handlers():
            # User commands
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("status", status_command))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("remind_partner", reminder_handler.remind_partner_command))
            application.add_handler(CommandHandler("get_to_know", conversation_handler.get_to_know_command))
            
            # Admin commands
            application.add_handler(CommandHandler("admin_dashboard", admin_handler.admin_dashboard_command))
            application.add_handler(CommandHandler("admin_approve", admin_handler.admin_approve_command))
            application.add_handler(CommandHandler("admin_reject", admin_handler.admin_reject_command))
            application.add_handler(CommandHandler("admin_status", admin_handler.admin_status_command))
            application.add_handler(CommandHandler("admin_digest", admin_handler.admin_digest_command))
            application.add_handler(CommandHandler("admin_cancel", cancellation_handler.admin_cancel_registration_command))
            application.add_handler(CommandHandler("admin_cancel_stats", cancellation_handler.get_cancellation_stats_command))
            
            # Monitoring admin commands
            application.add_handler(CommandHandler("admin_monitoring_status", monitoring_handler.admin_monitoring_status_command))
            application.add_handler(CommandHandler("admin_manual_check", monitoring_handler.admin_manual_check_command))
            application.add_handler(CommandHandler("admin_start_monitoring", monitoring_handler.admin_start_monitoring_command))
            application.add_handler(CommandHandler("admin_stop_monitoring", monitoring_handler.admin_stop_monitoring_command))
            
            # User commands
            application.add_handler(CommandHandler("cancel", cancellation_handler.cancel_registration_command))
            
            # Message handler for conversation flow
            application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                conversation_handler.handle_conversation_message
            ))
            
            # Log registered admin users
            for admin_id in settings.admin_user_ids:
                logger.info(f"Admin user registered: {admin_id}")
        
        async def setup_bot_commands():
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
            
            await application.bot.set_my_commands(commands)
            logger.info("✅ Bot commands set up successfully")
        
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                        await sheets_service.update_telegram_user_id(submission_id, user_id)
                        
                        # Get user status
                        status_data = await sheets_service.find_submission_by_telegram_id(user_id)
                        if status_data:
                            # Continue conversation with status
                            await continue_conversation(update, status_data)
                        else:
                            await update.message.reply_text(
                                message_service.get_message('en', 'submission_not_found', submission_id=submission_id)
                            )
                    except Exception as e:
                        logger.error(f"Error linking user {user_id} to submission {submission_id}: {e}")
                        await update.message.reply_text(
                            message_service.get_message('en', 'error_linking_submission')
                        )
                else:
                    # No submission ID provided, check if user is already linked
                    status_data = await sheets_service.find_submission_by_telegram_id(user_id)
                    if status_data:
                        await continue_conversation(update, status_data)
                    else:
                        await update.message.reply_text(
                            message_service.get_message('en', 'no_submission_linked')
                        )
            except Exception as e:
                logger.error(f"Error in start command: {e}")
                await update.message.reply_text(
                    message_service.get_message('en', 'general_error')
                )
        
        async def continue_conversation(update: Update, status_data: dict):
            """Continue conversation based on user status"""
            user = update.effective_user
            language = user.language_code or 'en'
            
            # Welcome message
            welcome_msg = message_service.get_message(
                language, 'welcome', name=status_data.get('alias', 'User')
            )
            
            # Build status message
            status_msg = message_service.build_status_message(status_data, language)
            
            # Combine messages
            full_message = f"{welcome_msg}\n\n{status_msg}"
            await update.message.reply_text(full_message)
        
        async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /status command"""
            try:
                user = update.effective_user
                user_id = str(user.id)
                language = user.language_code or 'en'
                
                status_data = await sheets_service.find_submission_by_telegram_id(user_id)
                if status_data:
                    status_msg = message_service.build_status_message(status_data, language)
                    await update.message.reply_text(status_msg)
                else:
                    await update.message.reply_text(
                        message_service.get_message(language, 'no_submission_linked')
                    )
            except Exception as e:
                logger.error(f"Error in status command: {e}")
                await update.message.reply_text(
                    message_service.get_message('en', 'general_error')
                )
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /help command"""
            try:
                user = update.effective_user
                language = user.language_code or 'en'
                
                help_msg = message_service.get_message(language, 'help')
                await update.message.reply_text(help_msg)
            except Exception as e:
                logger.error(f"Error in help command: {e}")
                await update.message.reply_text(
                    message_service.get_message('en', 'general_error')
                )
        
        # Register handlers
        register_handlers()
        
        # Set up commands
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_bot_commands())
        
        print("🤖 Bot initialized successfully!")
        print("📊 Admin users configured")
        print("🔧 Google Sheets connected")
        print("✅ Bot is now running! Press Ctrl+C to stop.")
        print("")
        
        # Start the bot polling
        application.run_polling()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("🔧 Make sure you're in the correct directory and all dependencies are installed")
        print("📦 Try: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 