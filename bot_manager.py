#!/usr/bin/env python3
"""
Bot Manager Utility
Helps manage and troubleshoot Telegram bot conflicts
"""

import os
import requests
from dotenv import load_dotenv
import psutil
import sys

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
    sys.exit(1)

def check_webhook_info():
    """Check if the bot has a webhook configured"""
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
        if response.status_code == 200:
            data = response.json()
            webhook_url = data.get('result', {}).get('url', '')
            
            if webhook_url:
                print(f"⚠️  Webhook is configured: {webhook_url}")
                print("   This might conflict with polling mode!")
                return True
            else:
                print("✅ No webhook configured")
                return False
        else:
            print(f"❌ Failed to check webhook: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
        return None

def delete_webhook():
    """Delete any configured webhook"""
    try:
        response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        if response.status_code == 200:
            print("✅ Webhook deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete webhook: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")
        return False

def find_python_processes():
    """Find running Python processes"""
    python_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_info = proc.info
            if 'python' in proc_info['name'].lower():
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                if 'telegram_bot_polling.py' in cmdline:
                    python_processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cmdline': cmdline
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return python_processes

def kill_bot_processes():
    """Kill any running bot processes"""
    processes = find_python_processes()
    
    if not processes:
        print("✅ No bot processes found running")
        return
    
    print(f"Found {len(processes)} bot process(es):")
    for proc in processes:
        print(f"  PID: {proc['pid']} - {proc['cmdline']}")
    
    try:
        for proc in processes:
            psutil.Process(proc['pid']).terminate()
            print(f"✅ Terminated process {proc['pid']}")
    except Exception as e:
        print(f"❌ Error terminating processes: {e}")

def main():
    print("🤖 Telegram Bot Manager")
    print("======================")
    
    while True:
        print("\nChoose an option:")
        print("1. Check webhook status")
        print("2. Delete webhook (if configured)")
        print("3. Find running bot processes")
        print("4. Kill running bot processes")
        print("5. Full cleanup (delete webhook + kill processes)")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            print("\n🔍 Checking webhook status...")
            check_webhook_info()
            
        elif choice == '2':
            print("\n🗑️  Deleting webhook...")
            delete_webhook()
            
        elif choice == '3':
            print("\n🔍 Finding running bot processes...")
            processes = find_python_processes()
            if processes:
                print(f"Found {len(processes)} bot process(es):")
                for proc in processes:
                    print(f"  PID: {proc['pid']} - {proc['cmdline']}")
            else:
                print("✅ No bot processes found")
                
        elif choice == '4':
            print("\n🔪 Killing running bot processes...")
            kill_bot_processes()
            
        elif choice == '5':
            print("\n🧹 Full cleanup...")
            print("Deleting webhook...")
            delete_webhook()
            print("Killing processes...")
            kill_bot_processes()
            print("✅ Cleanup complete!")
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 