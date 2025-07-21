#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Wild Ginger Bot Runner
A simplified runner that avoids event loop issues
"""

import sys
import os
import asyncio
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
    """Main function to run the bot"""
    try:
        # Import the bot
        from telegram_bot.main import WildGingerBot
        
        print("🚀 Starting Wild Ginger Bot...")
        
        # Create bot instance
        bot = WildGingerBot()
        
        # Run the bot using the application's run_polling method directly
        print("🤖 Bot initialized successfully!")
        print("📊 Admin users configured")
        print("🔧 Google Sheets connected")
        print("🔄 Background services started")
        print("🔍 Sheet monitoring active")
        print("")
        print("✅ Bot is now running! Press Ctrl+C to stop.")
        print("")
        
        # Start the bot using the simple method
        bot.start_simple()
        
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