#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wild Ginger Bot Launcher
Simple launcher script to run the bot with proper package imports
"""

import sys
import os
import asyncio

# Add the current directory to Python path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main launcher function"""
    try:
        # Import and run the bot
        from telegram_bot.main import run_bot
        run_bot()
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("🔧 Make sure you're in the correct directory and all dependencies are installed")
        print("📁 Current directory:", os.getcwd())
        print("📦 Try: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 