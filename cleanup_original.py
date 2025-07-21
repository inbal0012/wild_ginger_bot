#!/usr/bin/env python3
"""
Safe cleanup script to replace the original telegram_bot_polling.py
with the cleaned version that removes refactored parts.
"""

import os
import shutil
from datetime import datetime

def main():
    print("🧹 Telegram Bot Cleanup Script")
    print("=" * 40)
    
    original_file = "telegram_bot_polling.py"
    cleaned_file = "telegram_bot_polling_cleaned.py"
    backup_file = f"telegram_bot_polling_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    # Check if files exist
    if not os.path.exists(original_file):
        print(f"❌ Error: {original_file} not found!")
        return False
    
    if not os.path.exists(cleaned_file):
        print(f"❌ Error: {cleaned_file} not found!")
        print("Please run this script from the project root directory.")
        return False
    
    # Show file sizes for comparison
    original_size = os.path.getsize(original_file)
    cleaned_size = os.path.getsize(cleaned_file)
    
    print(f"📊 File size comparison:")
    print(f"  Original: {original_size:,} bytes ({original_size // 1024} KB)")
    print(f"  Cleaned:  {cleaned_size:,} bytes ({cleaned_size // 1024} KB)")
    print(f"  Reduced by: {((original_size - cleaned_size) / original_size * 100):.1f}%")
    
    # Ask for confirmation
    print(f"\n🔄 This will:")
    print(f"  1. Backup original file as: {backup_file}")
    print(f"  2. Replace {original_file} with cleaned version")
    print(f"  3. Keep {cleaned_file} for reference")
    
    response = input(f"\nProceed with cleanup? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Operation cancelled.")
        return False
    
    try:
        # Step 1: Create backup
        print(f"\n📋 Creating backup: {backup_file}")
        shutil.copy2(original_file, backup_file)
        print("✅ Backup created successfully")
        
        # Step 2: Replace original with cleaned version
        print(f"\n🔄 Replacing {original_file} with cleaned version")
        shutil.copy2(cleaned_file, original_file)
        print("✅ File replaced successfully")
        
        # Step 3: Verify
        new_size = os.path.getsize(original_file)
        if new_size == cleaned_size:
            print("✅ Verification passed - file sizes match")
        else:
            print("⚠️  Warning: File sizes don't match, but replacement completed")
        
        print(f"\n🎉 Cleanup completed successfully!")
        print(f"📁 Files:")
        print(f"  - {original_file} (cleaned - ready to use)")
        print(f"  - {backup_file} (backup of original)")  
        print(f"  - {cleaned_file} (template - can be deleted)")
        
        print(f"\n📋 What was removed:")
        print(f"  ✅ Configuration setup (now in telegram_bot/config/)")
        print(f"  ✅ Google Sheets functions (now in telegram_bot/services/)")
        print(f"  ✅ Message functions (now in telegram_bot/services/)")
        print(f"  ✅ Basic bot commands (now in telegram_bot/main.py)")
        
        print(f"\n📋 What remains (to be migrated):")
        print(f"  🚧 Admin commands")
        print(f"  🚧 Partner reminders")
        print(f"  🚧 Get-to-know flow")
        print(f"  🚧 Reminder scheduler")
        print(f"  🚧 Sheet monitoring")
        
        print(f"\n🚀 Next steps:")
        print(f"  1. Test the refactored bot: cd telegram_bot && python main.py")
        print(f"  2. Test the legacy bot: python telegram_bot_polling.py")
        print(f"  3. Read MIGRATION_GUIDE.md for next steps")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        
        # Try to restore from backup if replacement failed
        if os.path.exists(backup_file):
            try:
                print("🔄 Attempting to restore from backup...")
                shutil.copy2(backup_file, original_file)
                print("✅ Original file restored from backup")
            except:
                print("❌ Could not restore from backup - please restore manually")
        
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n💡 If you encounter issues:")
        print("  1. Make sure you're in the project root directory")
        print("  2. Ensure both files exist")
        print("  3. Check file permissions")
        print("  4. Try running with administrator privileges")
    
    input("\nPress Enter to exit...") 