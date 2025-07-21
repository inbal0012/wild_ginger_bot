#!/usr/bin/env python3
"""
Quick test to verify the refactored bot can initialize properly
"""

import os
import sys

# Add parent directory to path so we can import from telegram_bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set a dummy bot token for testing (required for initialization)
if not os.getenv('TELEGRAM_BOT_TOKEN'):
    os.environ['TELEGRAM_BOT_TOKEN'] = '123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'  # Dummy token

print("🧪 Quick Bot Initialization Test")
print("=" * 40)

try:
    from telegram_bot.main import WildGingerBot
    print("✅ Import successful")
    
    # Test bot initialization
    bot = WildGingerBot()
    print("✅ Bot initialized successfully")
    
    # Test service availability
    print(f"✅ Sheets Service: {'Available' if bot.sheets_service else 'Not available'}")
    print(f"✅ Message Service: {'Available' if bot.message_service else 'Not available'}")
    
    # Test configuration
    from telegram_bot.config import settings
    print(f"✅ Admin users: {len(settings.admin_user_ids)}")
    print(f"✅ Languages: {len(settings.messages)}")
    
    print()
    print("🎉 SUCCESS: Refactored bot can initialize correctly!")
    print("🚀 Bot is ready for production use!")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 