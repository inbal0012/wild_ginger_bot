#!/usr/bin/env python3
"""
Test script to verify Google Sheets integration
Run this to check if your Google Sheets configuration is working correctly.
"""

import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

def test_google_sheets():
    """Test Google Sheets connectivity and data reading"""
    
    # Get configuration
    credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    range_name = os.getenv("GOOGLE_SHEETS_RANGE", "Sheet1!A1:Z1000")
    
    print("🔍 Testing Google Sheets Integration...")
    print(f"📄 Credentials file: {credentials_file}")
    print(f"📊 Spreadsheet ID: {spreadsheet_id}")
    print(f"📋 Range: {range_name}")
    print()
    
    # Check if files exist
    if not credentials_file or not os.path.exists(credentials_file):
        print("❌ Credentials file not found!")
        print("Please check your GOOGLE_SHEETS_CREDENTIALS_FILE path in .env")
        return False
    
    if not spreadsheet_id:
        print("❌ Spreadsheet ID not configured!")
        print("Please set GOOGLE_SHEETS_SPREADSHEET_ID in .env")
        return False
    
    try:
        # Initialize credentials
        print("🔐 Loading credentials...")
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        # Build service
        print("🔗 Connecting to Google Sheets...")
        service = build('sheets', 'v4', credentials=credentials)
        
        # First, get sheet metadata to see available tabs
        print("📋 Getting sheet metadata...")
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        sheets = sheet_metadata.get('sheets', [])
        print(f"📊 Available sheet tabs:")
        for sheet in sheets:
            sheet_name = sheet['properties']['title']
            print(f"  - {sheet_name}")
        
        # Try to read data from the first sheet
        if sheets:
            first_sheet_name = sheets[0]['properties']['title']
            test_range = f"{first_sheet_name}!A1:Z1000"
            print(f"📖 Reading data from sheet: {test_range}")
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=test_range
            ).execute()
        else:
            print("❌ No sheets found!")
            return False
        
        values = result.get('values', [])
        
        if not values:
            print("⚠️  No data found in the specified range!")
            return False
        
        print(f"✅ Successfully read {len(values)} rows from Google Sheets!")
        print()
        
        # Show headers
        if values:
            headers = values[0]
            print("📋 Headers found:")
            for i, header in enumerate(headers):
                print(f"  {i+1}. {header}")
            print()
        
        # Look for expected columns
        expected_columns = [
            'Status', 'Submission ID', 'שם מלא', 
            'מגיע.ה לבד או באיזון', 'שם הפרטנר'
        ]
        
        found_columns = []
        for expected in expected_columns:
            for header in headers:
                if expected in header:
                    found_columns.append(expected)
                    break
        
        print(f"✅ Found {len(found_columns)}/{len(expected_columns)} expected columns:")
        for col in found_columns:
            print(f"  ✅ {col}")
        
        missing_columns = [col for col in expected_columns if col not in found_columns]
        if missing_columns:
            print(f"⚠️  Missing columns:")
            for col in missing_columns:
                print(f"  ❌ {col}")
        
        # Show sample data
        if len(values) > 1:
            print(f"\n📄 Sample data (first row):")
            sample_row = values[1]
            for i, value in enumerate(sample_row):
                if i < len(headers):
                    print(f"  {headers[i]}: {value}")
        
        print("\n🎉 Google Sheets integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Google Sheets: {e}")
        return False

if __name__ == "__main__":
    success = test_google_sheets()
    if success:
        print("\n✅ Your Google Sheets integration is working correctly!")
        print("You can now run the Telegram bot with: python telegram_bot_polling.py")
    else:
        print("\n❌ Please fix the issues above before running the bot.") 