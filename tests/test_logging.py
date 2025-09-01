#!/usr/bin/env python3
"""
Test script to verify logging configuration is working.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_bot.services.base_service import BaseService

def test_logging():
    """Test the logging configuration."""
    print("Testing logging configuration...")
    
    # Create a test service
    test_service = BaseService()
    
    # Test different log levels
    test_service.log_info("This is an INFO message")
    test_service.log_warning("This is a WARNING message")
    test_service.log_error("This is an ERROR message")
    
    # Check if log file exists and has content
    log_file_path = "logs/wild_ginger_bot.log"
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Log file exists and contains {len(content)} characters")
            if content:
                print("Last few lines of log file:")
                lines = content.strip().split('\n')
                for line in lines[-5:]:
                    print(f"  {line}")
            else:
                print("Log file is empty!")
    else:
        print(f"Log file does not exist at {log_file_path}")
    
    print("Logging test completed.")

if __name__ == "__main__":
    test_logging() 