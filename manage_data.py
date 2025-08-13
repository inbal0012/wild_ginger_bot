#!/usr/bin/env python3
"""
Data Management Utility for Wild Ginger Bot
Helps manage stored data files for development and testing.
"""

import os
import sys
import json
from datetime import datetime
from telegram_bot.services.file_storage_service import FileStorageService


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n--- {title} ---")


def main():
    """Main function for data management utility."""
    storage = FileStorageService()
    
    print_header("Wild Ginger Bot - Data Management Utility")
    
    while True:
        print("\nAvailable actions:")
        print("1. List all data files")
        print("2. View data file contents")
        print("3. Backup data file")
        print("4. Delete data file")
        print("5. Show file info")
        print("6. Clean up old backups")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == "0":
            print("Goodbye!")
            break
            
        elif choice == "1":
            list_data_files(storage)
            
        elif choice == "2":
            view_data_file(storage)
            
        elif choice == "3":
            backup_data_file(storage)
            
        elif choice == "4":
            delete_data_file(storage)
            
        elif choice == "5":
            show_file_info(storage)
            
        elif choice == "6":
            cleanup_backups(storage)
            
        else:
            print("❌ Invalid choice. Please try again.")


def list_data_files(storage: FileStorageService):
    """List all data files."""
    print_section("Data Files")
    
    files = storage.list_data_files()
    
    if not files:
        print("📁 No data files found.")
        return
    
    print(f"Found {len(files)} data file(s):")
    for i, filename in enumerate(files, 1):
        info = storage.get_file_info(filename)
        if info:
            size_kb = info['size_bytes'] / 1024
            print(f"{i}. {filename} ({size_kb:.1f} KB, modified: {info['modified_at'][:19]})")
        else:
            print(f"{i}. {filename}")


def view_data_file(storage: FileStorageService):
    """View contents of a data file."""
    print_section("View Data File")
    
    files = storage.list_data_files()
    if not files:
        print("📁 No data files found.")
        return
    
    print("Available files:")
    for i, filename in enumerate(files, 1):
        print(f"{i}. {filename}")
    
    try:
        choice = int(input("\nEnter file number to view: ")) - 1
        if 0 <= choice < len(files):
            filename = files[choice]
            data = storage.load_data(filename)
            
            print(f"\n📄 Contents of '{filename}':")
            print("-" * 40)
            
            if isinstance(data, dict):
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(data)
                
        else:
            print("❌ Invalid file number.")
    except ValueError:
        print("❌ Please enter a valid number.")


def backup_data_file(storage: FileStorageService):
    """Backup a data file."""
    print_section("Backup Data File")
    
    files = storage.list_data_files()
    if not files:
        print("📁 No data files found.")
        return
    
    print("Available files:")
    for i, filename in enumerate(files, 1):
        print(f"{i}. {filename}")
    
    try:
        choice = int(input("\nEnter file number to backup: ")) - 1
        if 0 <= choice < len(files):
            filename = files[choice]
            
            # Create backup with timestamp
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            success = storage.backup_data(filename, backup_suffix)
            
            if success:
                print(f"✅ Backup created: {filename}_backup_{backup_suffix}")
            else:
                print("❌ Failed to create backup.")
        else:
            print("❌ Invalid file number.")
    except ValueError:
        print("❌ Please enter a valid number.")


def delete_data_file(storage: FileStorageService):
    """Delete a data file."""
    print_section("Delete Data File")
    
    files = storage.list_data_files()
    if not files:
        print("📁 No data files found.")
        return
    
    print("Available files:")
    for i, filename in enumerate(files, 1):
        print(f"{i}. {filename}")
    
    try:
        choice = int(input("\nEnter file number to delete: ")) - 1
        if 0 <= choice < len(files):
            filename = files[choice]
            
            confirm = input(f"⚠️  Are you sure you want to delete '{filename}'? (yes/no): ").lower()
            if confirm == "yes":
                success = storage.delete_data(filename)
                if success:
                    print(f"✅ Deleted: {filename}")
                else:
                    print("❌ Failed to delete file.")
            else:
                print("❌ Deletion cancelled.")
        else:
            print("❌ Invalid file number.")
    except ValueError:
        print("❌ Please enter a valid number.")


def show_file_info(storage: FileStorageService):
    """Show detailed information about a data file."""
    print_section("File Information")
    
    files = storage.list_data_files()
    if not files:
        print("📁 No data files found.")
        return
    
    print("Available files:")
    for i, filename in enumerate(files, 1):
        print(f"{i}. {filename}")
    
    try:
        choice = int(input("\nEnter file number for info: ")) - 1
        if 0 <= choice < len(files):
            filename = files[choice]
            info = storage.get_file_info(filename)
            
            if info:
                print(f"\n📊 File Information for '{filename}':")
                print(f"   Path: {info['file_path']}")
                print(f"   Size: {info['size_bytes']} bytes ({info['size_bytes']/1024:.1f} KB)")
                print(f"   Created: {info['created_at']}")
                print(f"   Modified: {info['modified_at']}")
            else:
                print("❌ Could not retrieve file information.")
        else:
            print("❌ Invalid file number.")
    except ValueError:
        print("❌ Please enter a valid number.")


def cleanup_backups(storage: FileStorageService):
    """Clean up old backup files."""
    print_section("Clean Up Backups")
    
    files = storage.list_data_files()
    backup_files = [f for f in files if "_backup_" in f]
    
    if not backup_files:
        print("📁 No backup files found.")
        return
    
    print(f"Found {len(backup_files)} backup file(s):")
    for i, filename in enumerate(backup_files, 1):
        info = storage.get_file_info(filename)
        if info:
            size_kb = info['size_bytes'] / 1024
            print(f"{i}. {filename} ({size_kb:.1f} KB, modified: {info['modified_at'][:19]})")
    
    confirm = input(f"\n⚠️  Delete all {len(backup_files)} backup files? (yes/no): ").lower()
    if confirm == "yes":
        deleted_count = 0
        for filename in backup_files:
            if storage.delete_data(filename):
                deleted_count += 1
                print(f"🗑️  Deleted: {filename}")
        
        print(f"✅ Cleaned up {deleted_count} backup files.")
    else:
        print("❌ Cleanup cancelled.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 