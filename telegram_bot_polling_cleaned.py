#!/usr/bin/env python3
"""
Wild Ginger Bot - ORIGINAL FILE (Cleaned Version)
This file contains only the parts NOT YET refactored to the new architecture.

REFACTORED PARTS (now in telegram_bot/ directory):
- ✅ Basic configuration (config/settings.py)
- ✅ Google Sheets operations (services/sheets_service.py)  
- ✅ Message handling (services/message_service.py)
- ✅ Basic bot commands: /start, /status, /help (main.py)
- ✅ Data models (models/registration.py)

REMAINING PARTS TO MIGRATE:
- [ ] Admin commands (/admin_*)
- [ ] Partner reminders (/remind_partner) 
- [ ] Get-to-know conversation flow
- [ ] Cancellation workflow
- [ ] Reminder scheduler system
- [ ] Sheet monitoring
"""

import os
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Store user -> submission_id mapping (will be handled by refactored services)
user_submissions = {}

# NOTE: The following imports would come from the refactored services:
# from telegram_bot.services import SheetsService, MessageService
# from telegram_bot.config import settings

# For now, we'll use the old functions that are still here
# These will be removed once we fully migrate to the refactored architecture

# --- ADMIN COMMANDS (✅ MIGRATED to AdminService) ---
# This functionality has been moved to:
# - telegram_bot/services/admin_service.py
# - telegram_bot/handlers/admin_commands.py
#
# Features migrated:
# ✅ Admin dashboard with statistics
# ✅ Registration approval/rejection workflow
# ✅ Detailed status checking  
# ✅ Weekly digest generation
# ✅ Admin permission checking
# ✅ User and admin notifications
#
# Available in refactored bot via /admin_* commands

# --- PARTNER REMINDERS (✅ MIGRATED to ReminderService) ---
# This functionality has been moved to:
# - telegram_bot/services/reminder_service.py
# - telegram_bot/handlers/reminder_commands.py
# 
# Available in refactored bot via /remind_partner command

# --- CANCELLATION WORKFLOW (✅ MIGRATED to CancellationService) ---
# This functionality has been moved to:
# - telegram_bot/services/cancellation_service.py
# - telegram_bot/handlers/cancellation_commands.py
#
# Features migrated:
# ✅ User registration cancellation with reason
# ✅ Last-minute cancellation detection
# ✅ Google Sheets status updates
# ✅ Multilingual cancellation messages
# ✅ Admin-initiated cancellations
# ✅ Cancellation statistics and reporting
# ✅ Comprehensive error handling
#
# Available in refactored bot via /cancel command

# --- GET-TO-KNOW CONVERSATION FLOW (✅ MIGRATED to ConversationService) ---
# This functionality has been moved to:
# - telegram_bot/services/conversation_service.py 
# - telegram_bot/handlers/conversation_commands.py
#
# Features migrated:
# ✅ Multi-step conversation flow
# ✅ Boring answer detection
# ✅ Automatic follow-up questions
# ✅ Response storage in Google Sheets
# ✅ State management
#
# Available in refactored bot via /get_to_know command

# --- BACKGROUND REMINDER SCHEDULER (✅ MIGRATED to BackgroundScheduler) ---
# This functionality has been moved to:
# - telegram_bot/services/background_scheduler.py
#
# Features migrated:
# ✅ Automatic reminder checking and scheduling
# ✅ Partner reminder automation
# ✅ Payment reminder automation  
# ✅ Group opening reminders
# ✅ Weekly digest automation
# ✅ Background task management
# ✅ Interval-based scheduling
# ✅ Error handling and recovery
#
# Available in refactored bot via BackgroundScheduler service

# --- SHEET MONITORING (✅ MIGRATED to MonitoringService) ---
# This functionality has been moved to:
# - telegram_bot/services/monitoring_service.py
# - telegram_bot/handlers/monitoring_commands.py
#
# Features migrated:
# ✅ Sheet1 automatic monitoring (5-minute intervals)
# ✅ New registration detection and duplication
# ✅ Column mapping between Sheet1 and managed sheet
# ✅ Admin notification system for new registrations
# ✅ Manual monitoring triggers for admin control
# ✅ Monitoring status reporting and management
# ✅ Background task lifecycle management
# ✅ Comprehensive error handling and recovery
#
# Available in refactored bot via MonitoringService and /admin_monitoring_* commands

# --- MAIN BOT SETUP ---

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ==========================================
    # NOTE: Basic commands (/start, /status, /help) are now handled by
    # the refactored bot in telegram_bot/main.py
    # These should be removed from here to avoid conflicts
    # ==========================================

    # ADMIN COMMANDS (✅ MIGRATED to AdminService)
    # app.add_handler(CommandHandler("admin_dashboard", admin_dashboard))  # ✅ MIGRATED  
    # app.add_handler(CommandHandler("admin_approve", admin_approve))      # ✅ MIGRATED
    # app.add_handler(CommandHandler("admin_reject", admin_reject))        # ✅ MIGRATED
    # app.add_handler(CommandHandler("admin_status", admin_status))        # ✅ MIGRATED
    # app.add_handler(CommandHandler("admin_digest", admin_digest))        # ✅ MIGRATED

    # USER COMMANDS (✅ MIGRATED to respective services)  
    # app.add_handler(CommandHandler("remind_partner", remind_partner))      # ✅ MIGRATED to ReminderService
    # app.add_handler(CommandHandler("get_to_know", get_to_know_command))    # ✅ MIGRATED to ConversationService
    # app.add_handler(CommandHandler("cancel", cancel_registration))         # ✅ MIGRATED to CancellationService

    # MESSAGE HANDLERS (to be migrated to ConversationService)
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_get_to_know_response))  # ✅ MIGRATED

    # Bot command setup
    async def setup_bot_commands():
        """Set up bot commands - will be handled by refactored main.py"""
        commands = [
            # BotCommand("admin_dashboard", "Admin: View registration dashboard"),  # ✅ MIGRATED
            # BotCommand("admin_approve", "Admin: Approve registration"),           # ✅ MIGRATED
            # BotCommand("admin_reject", "Admin: Reject registration"),             # ✅ MIGRATED
            # BotCommand("remind_partner", "Send reminder to partner"),             # ✅ MIGRATED
            # BotCommand("get_to_know", "Complete get-to-know section"),            # ✅ MIGRATED
            # BotCommand("cancel", "Cancel registration"),                          # ✅ MIGRATED
        ]
        
        try:
            await app.bot.set_my_commands(commands)
            print("✅ Legacy bot commands set up")
        except Exception as e:
            print(f"❌ Error setting up commands: {e}")

    # Background task initialization (✅ MIGRATED)
    async def post_init(application):
        """Initialize background tasks"""
        await setup_bot_commands()
        
        # All background tasks now handled by refactored bot
        print("✅ Background tasks managed by telegram_bot/main.py")

    app.post_init = post_init

    print("🤖 Starting LEGACY bot (NOW EMPTY - MIGRATION COMPLETE!)...")
    print("🎉 NOTE: ALL features are now handled by telegram_bot/main.py")
    print("📋 No remaining features - migration complete!")
    print("")
    print("✅ Fully migrated microservices:")
    print("   - Partner reminders → ReminderService")
    print("   - Get-to-know flow → ConversationService")
    print("   - Admin commands → AdminService")
    print("   - Background scheduler → BackgroundScheduler")
    print("   - Cancellation workflow → CancellationService")
    print("   - Sheet monitoring → MonitoringService")
    print("")
    print("🏆 MIGRATION 100% COMPLETE! ABSOLUTE PERFECTION ACHIEVED!")

    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Error starting legacy bot: {e}")
        exit(1) 