from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# --- Multilingual Messages ---
MESSAGES = {
    'en': {
        'welcome': "Hi {name}! 👋\nI'm your registration assistant. You can check your status anytime with /status.",
        'welcome_no_name': "Hi there! 👋\nI'm your registration assistant.\n\nTo link your form submission, please use the link provided after filling out the registration form.\nYou can check your status anytime with /status.",
        'submission_not_found': "❌ Could not find submission {submission_id}.\nPlease check your submission ID and try again.",
        'no_submission_linked': "❌ No submission linked to your account.\n\nTo link your form submission, please use the link provided after filling out the registration form.\nIt should look like: `/start SUBM_12345`",
        'status_labels': {
            'form': "📋 Form",
            'partner': "🤝 Partner",
            'get_to_know': "💬 Get-to-know",
            'status': "🛠️ Status",
            'payment': "💸 Payment",
            'group': "👥 Group",
            'approved': "✅ Approved",
            'waiting_review': "⏳ Waiting for review",
            'paid': "✅",
            'not_paid': "❌ Not yet paid",
            'group_open': "✅ Open",
            'group_not_open': "❌ Not open yet"
        },
        'help': "🤖 Wild Ginger Bot Help\n\n"
                "Available commands:\n"
                "/start - Link your registration or welcome message\n"
                "/status - Check your registration progress\n"
                "/help - Show this help message\n"
                "/cancel <reason> - Cancel your registration with reason\n\n"
                "To link your registration, use the link provided after filling out the form.\n"
                "Example: /start SUBM_12345"
    },
    'he': {
        'welcome': "שלום {name}! 👋\nאני עוזר הרשמה שלך. אתה יכול לבדוק את הסטטוס שלך בכל זמן עם /status.",
        'welcome_no_name': "שלום! 👋\nאני עוזר הרשמה שלך.\n\nכדי לקשר את הטופס שלך, אנא השתמש בקישור שניתן לאחר מילוי טופס הרשמה.\nאתה יכול לבדוק את הסטטוס שלך בכל זמן עם /status.",
        'submission_not_found': "❌ לא הצלחתי למצוא הגשה {submission_id}.\nאנא בדוק את מזהה ההגשה ונסה שוב.",
        'no_submission_linked': "❌ אין הגשה מקושרת לחשבון שלך.\n\nכדי לקשר את הטופס שלך, אנא השתמש בקישור שניתן לאחר מילוי טופס הרשמה.\nזה צריך להראות כך: `/start SUBM_12345`",
        'status_labels': {
            'form': "📋 טופס",
            'partner': "🤝 שותף",
            'get_to_know': "💬 היכרות",
            'status': "🛠️ סטטוס",
            'payment': "💸 תשלום",
            'group': "👥 קבוצה",
            'approved': "✅ מאושר",
            'waiting_review': "⏳ מחכה לאישור",
            'paid': "✅",
            'not_paid': "❌ עדיין לא שולם",
            'group_open': "✅ פתוחה",
            'group_not_open': "❌ עדיין לא פתוחה"
        },
        'help': "🤖 עזרה לבוט Wild Ginger\n\n"
                "פקודות זמינות:\n"
                "/start - קישור הרשמה או הודעת ברוך הבא\n"
                "/status - בדיקת התקדמות הרשמה\n"
                "/help - הצגת הודעת עזרה זו\n"
                "/cancel <סיבה> - ביטול הרשמה עם סיבה\n\n"
                "כדי לקשר את הרשמתך, השתמש בקישור שניתן לאחר מילוי הטופס.\n"
                "דוגמה: /start SUBM_12345"
    }
}

def get_message(language, key, **kwargs):
    """Get a message in the specified language with optional formatting"""
    try:
        message = MESSAGES[language][key]
        if kwargs:
            return message.format(**kwargs)
        return message
    except KeyError:
        # Fallback to English if key not found
        try:
            message = MESSAGES['en'][key]
            if kwargs:
                return message.format(**kwargs)
            return message
        except KeyError:
            return f"Message key '{key}' not found"

def build_partner_status_text(status_data, language):
    """Build detailed partner status text"""
    labels = MESSAGES[language]['status_labels']
    
    # Check if user has partners
    partner_names = status_data.get('partner_names', [])
    partner_status = status_data.get('partner_status', {})
    partner_complete = status_data.get('partner', False)  # Boolean from Google Sheets
    
    if not partner_names:
        # No partners - coming alone
        if language == 'he':
            return f"{labels['partner']}: מגיע.ה לבד"
        else:
            return f"{labels['partner']}: Coming alone"
    
    # Has partners - show detailed status
    registered_partners = partner_status.get('registered_partners', [])
    missing_partners = partner_status.get('missing_partners', [])
    
    # If we have detailed partner status, show it
    if len(partner_names) > 1:
        if language == 'he':
            partner_header = f"{labels['partner']}: סטטוס הפרטנרים שלך:"
        else:
            partner_header = f"{labels['partner']}: Your partners' status:"
        
        partner_lines = [partner_header]
        
        # Show registered partners
        if registered_partners:
            registered_text = ', '.join(registered_partners)
            completed_text = 'השלמו' if len(registered_partners) > 1 else 'השלים'
            if language == 'he':
                partner_lines.append(f"    ✅ {registered_text} {completed_text} את הטופס")
            else:
                partner_lines.append(f"    ✅ {registered_text} completed the form")
        
        # Show missing partners
        if missing_partners:
            missing_text = ', '.join(missing_partners)
            if language == 'he':
                partner_lines.append(f"    ❌ {missing_text} עוד לא השלים את הטופס")
            else:
                partner_lines.append(f"    ❌ {missing_text} hasn't completed the form yet")
        
        return '\n'.join(partner_lines)
    
    # Fallback to simple partner status when no detailed info available
    else:
        partner_alias = status_data.get('partner_alias', '')
        if partner_complete:
            if partner_alias:
                return f"{labels['partner']}: ✅ ({partner_alias})"
            else:
                return f"{labels['partner']}: ✅"
        else:
            if partner_alias:
                return f"{labels['partner']}: ❌ ({partner_alias})"
            else:
                return f"{labels['partner']}: ❌"

def get_status_message(status_data):
    """Build a status message in the user's preferred language"""
    language = status_data.get('language', 'en')
    labels = MESSAGES[language]['status_labels']
    
    # Build detailed partner text
    partner_text = build_partner_status_text(status_data, language)
    
    # Build status text
    status_text = labels['approved'] if status_data['approved'] else labels['waiting_review']
    
    # Build payment text
    payment_text = labels['paid'] if status_data['paid'] else labels['not_paid']
    
    # Build group text
    group_text = labels['group_open'] if status_data['group_open'] else labels['group_not_open']
    
    # Construct the message
    message = (
        f"{labels['form']}: {'✅' if status_data['form'] else '❌'}\n"
        f"{partner_text}\n"
        f"{labels['get_to_know']}: {'✅' if status_data['get_to_know'] else '❌'}\n"
        f"{labels['status']}: {status_text}\n"
        f"{labels['payment']}: {payment_text}\n"
        f"{labels['group']}: {group_text}\n\n"
    )
    
    return message

# --- Google Sheets configuration ---
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
GOOGLE_SHEETS_RANGE = os.getenv("GOOGLE_SHEETS_RANGE", "managed!A3:GG1000")  # Start from row 3 (headers)

# Initialize Google Sheets service
sheets_service = None
if GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID:
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']  # Read and write permissions
        )
        sheets_service = build('sheets', 'v4', credentials=credentials)
        print("✅ Google Sheets integration enabled")
    except Exception as e:
        print(f"❌ Google Sheets integration failed: {e}")
        sheets_service = None
else:
    print("⚠️  Google Sheets not configured - using mock data")

# --- Google Sheets functions ---
def get_sheet_data():
    """Fetch all data from the Google Sheets"""
    if not sheets_service:
        return None
    
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
            range=GOOGLE_SHEETS_RANGE
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return None
            
        # First row should be headers
        headers = values[0] if values else []
        rows = values[1:] if len(values) > 1 else []
        
        return {'headers': headers, 'rows': rows}
    except Exception as e:
        print(f"❌ Error reading Google Sheets: {e}")
        return None

def get_column_indices(headers):
    """Get column indices for all important fields from headers"""
    column_indices = {}
    for i, header in enumerate(headers):
        if 'Submission ID' in header and 'time' not in header.lower():
            column_indices['submission_id'] = i
        elif 'שם מלא' in header:  # Full name in Hebrew
            column_indices['full_name'] = i
        elif 'מגיע.ה לבד או באיזון' in header:  # Coming alone or in balance
            column_indices['coming_alone_or_balance'] = i
        elif 'שם הפרטנר' in header:  # Partner name in Hebrew
            column_indices['partner_name'] = i
        # Language preference column
        elif 'האם תרצו להמשיך בעברית או באנגלית' in header or 'Language Preference' in header:
            column_indices['language_preference'] = i
        # Returning participant column
        elif 'האם השתתפת בעבר באחד מאירועי Wild Ginger' in header or 'Previous Wild Ginger Participation' in header:
            column_indices['returning_participant'] = i
        # New dedicated status columns
        elif 'Form Complete' in header or 'טופס הושלם' in header:
            column_indices['form_complete'] = i
        elif 'Partner Complete' in header or 'פרטנר הושלם' in header:
            column_indices['partner_complete'] = i
        elif 'Get To Know Complete' in header or 'היכרות הושלמה' in header:
            column_indices['get_to_know_complete'] = i
        elif 'Admin Approved' in header or 'מאושר' in header:
            column_indices['admin_approved'] = i
        elif 'Payment Complete' in header or 'תשלום הושלם' in header:
            column_indices['payment_complete'] = i
        elif 'Group Access' in header or 'גישה לקבוצה' in header:
            column_indices['group_access'] = i
        # Keep the old status column as fallback
        elif 'Status' in header or 'status' in header.lower():
            column_indices['status'] = i
        # New: Telegram User ID column
        elif 'Telegram User Id' in header or 'מזהה משתמש טלגרם' in header:
            column_indices['telegram_user_id'] = i
        # Cancellation tracking columns
        elif 'Cancelled' in header or 'בוטל' in header or 'מבוטל' in header:
            column_indices['cancelled'] = i
        elif 'Cancellation Date' in header or 'תאריך ביטול' in header:
            column_indices['cancellation_date'] = i
        elif 'Cancellation Reason' in header or 'סיבת ביטול' in header:
            column_indices['cancellation_reason'] = i
        elif 'Last Minute Cancellation' in header or 'ביטול ברגע האחרון' in header:
            column_indices['last_minute_cancellation'] = i
    return column_indices

def find_submission_by_field(field_name: str, field_value: str):
    """Generic function to find a submission by any field value"""
    sheet_data = get_sheet_data()
    if not sheet_data:
        return None
    
    headers = sheet_data['headers']
    rows = sheet_data['rows']
    
    column_indices = get_column_indices(headers)
    
    # Look for the field value in the rows
    field_column_index = column_indices.get(field_name)
    if field_column_index is None:
        return None
    
    for row in rows:
        if len(row) > field_column_index:
            if row[field_column_index] == field_value:
                return parse_submission_row(row, column_indices)
    
    return None

def find_submission_by_id(submission_id: str):
    """Find a submission by its ID in the Google Sheets"""
    result = find_submission_by_field('submission_id', submission_id)
    print(result)
    return result

def find_submission_by_telegram_id(telegram_user_id: str):
    """Find a submission by Telegram User ID in the Google Sheets"""
    return find_submission_by_field('telegram_user_id', telegram_user_id)

def column_index_to_letter(col_index):
    """Convert a column index (0-based) to Excel column letter format (A, B, ..., Z, AA, AB, ...)"""
    result = ""
    while col_index >= 0:
        result = chr(ord('A') + (col_index % 26)) + result
        col_index = col_index // 26 - 1
    return result

def update_telegram_user_id(submission_id: str, telegram_user_id: str):
    """Update the Telegram User ID for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Telegram User ID")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        telegram_user_id_col = column_indices.get('telegram_user_id')
        
        if submission_id_col is None or telegram_user_id_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the Telegram User ID
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Convert column index to letter using proper function
                col_letter = column_index_to_letter(telegram_user_id_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell
                result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[telegram_user_id]]}
                ).execute()
                
                print(f"✅ Updated Telegram User ID for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Telegram User ID: {e}")
        return False

def update_form_complete(submission_id: str, form_complete: bool = True):
    """Update the Form Complete field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Form Complete")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        form_complete_col = column_indices.get('form_complete')
        
        if submission_id_col is None or form_complete_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the Form Complete field
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Convert column index to letter using proper function
                col_letter = column_index_to_letter(form_complete_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if form_complete else "FALSE"
                result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[value]]}
                ).execute()
                
                print(f"✅ Updated Form Complete to {value} for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Form Complete: {e}")
        return False

def update_get_to_know_complete(submission_id: str, get_to_know_complete: bool = True):
    """Update the Get To Know Complete field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Get To Know Complete")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        get_to_know_complete_col = column_indices.get('get_to_know_complete')
        
        if submission_id_col is None or get_to_know_complete_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the Get To Know Complete field
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Convert column index to letter using proper function
                col_letter = column_index_to_letter(get_to_know_complete_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if get_to_know_complete else "FALSE"
                result = sheets_service.spreadsheets().values().update(
                    spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[value]]}
                ).execute()
                
                print(f"✅ Updated Get To Know Complete to {value} for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Get To Know Complete: {e}")
        return False

def parse_submission_row(row, column_indices):
    """Parse a row from the sheet into our status format"""
    def get_cell_value(key, default=""):
        index = column_indices.get(key)
        if index is not None and index < len(row):
            return row[index]
        return default
    
    def get_boolean_value(key, default=False):
        """Get a boolean value from the sheet, handling various formats"""
        value = get_cell_value(key, "").strip().upper()
        if value in ['TRUE', 'YES', 'כן', '1', 'V', '✓']:
            return True
        elif value in ['FALSE', 'NO', 'לא', '0', '', 'X']:
            return False
        return default
    
    def get_language_preference(response):
        """Determine language preference from form response"""
        if not response:
            return 'en'  # Default to English if no response
        
        response_lower = response.lower().strip()
        
        # Check for Hebrew indicators
        hebrew_indicators = ['עברית', 'hebrew', 'he', 'heb', 'עב']
        english_indicators = ['english', 'אנגלית', 'en', 'eng', 'אנג']
        
        for indicator in hebrew_indicators:
            if indicator in response_lower:
                return 'he'
        
        for indicator in english_indicators:
            if indicator in response_lower:
                return 'en'
        
        # Default to Hebrew if contains Hebrew characters
        if any('\u0590' <= char <= '\u05FF' for char in response):
            return 'he'
        
        return 'en'  # Default to English
    
    # Get basic info
    submission_id = get_cell_value('submission_id')
    full_name = get_cell_value('full_name')
    coming_alone_or_balance = get_cell_value('coming_alone_or_balance')
    partner_name = get_cell_value('partner_name')
    
    # Parse status into our flow steps - no assumptions, use dedicated columns
    form_complete = get_boolean_value('form_complete', False)
    partner_complete = get_boolean_value('partner_complete', False)
    get_to_know_complete = get_boolean_value('get_to_know_complete', False)
    approved = get_boolean_value('admin_approved', False)
    paid = get_boolean_value('payment_complete', False)
    group_open = get_boolean_value('group_access', False)
    
    # Only do expensive operations if needed
    partner_names = []
    partner_status = {"all_registered": True, "registered_partners": [], "missing_partners": []}
    has_partner = coming_alone_or_balance != 'לבד' and partner_name and partner_name.strip()
    
    # Only parse partners if partner is not complete
    if not partner_complete and has_partner:
        print(f"🔍 Parsing partners for {full_name} (partner not complete)")
        partner_names = parse_multiple_partners(partner_name)
        if partner_names:
            partner_status = check_partner_registration_status(partner_names)
    elif has_partner:
        print(f"⏭️  Skipping partner parsing for {full_name} (partner already complete)")
        partner_names = [partner_name]  # Just store the raw name, no parsing needed
    
    # Only determine language preference if we need it for reminders
    language_response = get_cell_value('language_preference')
    preferred_language = get_language_preference(language_response)
    
    # Only check returning participant status if get_to_know is not complete
    is_returning_participant = False
    if not get_to_know_complete:
        returning_participant_response = get_cell_value('returning_participant')
        is_returning_participant = get_boolean_value('returning_participant', False)
    else:
        print(f"⏭️  Skipping returning participant check for {full_name} (get_to_know already complete)")
    
    return {
        "submission_id": submission_id,
        "alias": full_name,
        "form": form_complete,
        "partner": partner_complete,
        "get_to_know": get_to_know_complete,
        "approved": approved,
        "paid": paid,
        "group_open": group_open,
        "partner_alias": partner_name if has_partner else None,
        "partner_names": partner_names,  # List of all partner names
        "partner_status": partner_status,  # Registration status of all partners
        "coming_alone_or_balance": coming_alone_or_balance,
        "raw_status": get_cell_value('status', ''),  # Keep as fallback/reference
        "telegram_user_id": get_cell_value('telegram_user_id', ''),
        "language": preferred_language,  # Add language preference
        "is_returning_participant": is_returning_participant  # Add returning participant info
    }

def parse_multiple_partners(partner_names_string):
    """Parse multiple partner names from a single string field"""
    if not partner_names_string or partner_names_string.strip() == '':
        return []
    
    print(f"🔍 Parsing partners from: '{partner_names_string}'")
    
    # Common separators for multiple names
    separators = [',', '&', '+', ' ו ', ' and ', '\n', ';']
    
    # Start with the original string
    names = [partner_names_string]
    
    # Split by each separator
    for separator in separators:
        new_names = []
        for name in names:
            split_names = [n.strip() for n in name.split(separator) if n.strip()]
            new_names.extend(split_names)
        names = new_names
        if len(names) > 1:
            print(f"   After splitting by '{separator}': {names}")
    
    # Filter out empty strings and duplicates
    unique_names = []
    for name in names:
        cleaned_name = name.strip()
        if cleaned_name and cleaned_name not in unique_names:
            unique_names.append(cleaned_name)
    
    print(f"✅ Final parsed partner names: {unique_names}")
    return unique_names

def check_partner_registration_status(partner_names):
    """Check if all partners are registered by searching for their names in the sheet"""
    if not partner_names:
        return {"all_registered": True, "registered_partners": [], "missing_partners": []}
    
    if not sheets_service:
        return {"all_registered": False, "registered_partners": [], "missing_partners": partner_names}
    
    try:
        sheet_data = get_sheet_data()
        if not sheet_data:
            return {"all_registered": False, "registered_partners": [], "missing_partners": partner_names}
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = get_column_indices(headers)
        
        full_name_col = column_indices.get('full_name')
        if full_name_col is None:
            return {"all_registered": False, "registered_partners": [], "missing_partners": partner_names}
        
        # Get all registered names from the sheet
        registered_names = []
        for row in rows:
            if len(row) > full_name_col and row[full_name_col].strip():
                registered_names.append(row[full_name_col].strip())
        
        print(f"🔍 Checking {len(partner_names)} partners against {len(registered_names)} registered names")
        print(f"   Partners to check: {partner_names}")
        
        # Check each partner
        registered_partners = []
        missing_partners = []
        
        for partner_name in partner_names:
            print(f"   Checking partner: '{partner_name}'")
            found = False
            
            # Try exact match first
            for registered_name in registered_names:
                if partner_name.strip().lower() == registered_name.strip().lower():
                    print(f"     ✅ Exact match found: '{registered_name}'")
                    registered_partners.append(partner_name)
                    found = True
                    break
            
            # If no exact match, try partial match (more conservative)
            if not found:
                for registered_name in registered_names:
                    # Check if the partner name is a substantial part of the registered name
                    partner_words = partner_name.strip().lower().split()
                    registered_words = registered_name.strip().lower().split()
                    
                    # At least 80% of partner name words should match
                    if len(partner_words) >= 2:
                        matching_words = sum(1 for word in partner_words if word in registered_words)
                        if matching_words >= len(partner_words) * 0.8:
                            print(f"     ✅ Partial match found: '{registered_name}' (matches {matching_words}/{len(partner_words)} words)")
                            registered_partners.append(partner_name)
                            found = True
                            break
                    else:
                        # For single word names, be more strict
                        if partner_name.strip().lower() in registered_name.strip().lower():
                            print(f"     ✅ Single word match found: '{registered_name}'")
                            registered_partners.append(partner_name)
                            found = True
                            break
            
            if not found:
                print(f"     ❌ No match found for: '{partner_name}'")
                missing_partners.append(partner_name)
        
        result = {
            "all_registered": len(missing_partners) == 0,
            "registered_partners": registered_partners,
            "missing_partners": missing_partners
        }
        
        print(f"📊 Partner status result: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error checking partner registration: {e}")
        return {"all_registered": False, "registered_partners": [], "missing_partners": partner_names}

def update_cancellation_status(submission_id: str, cancelled: bool = True, reason: str = "", is_last_minute: bool = False):
    """Update cancellation status with reason and timing information"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update cancellation status")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        cancelled_col = column_indices.get('cancelled')
        cancellation_date_col = column_indices.get('cancellation_date')
        cancellation_reason_col = column_indices.get('cancellation_reason')
        last_minute_col = column_indices.get('last_minute_cancellation')
        
        if submission_id_col is None:
            print("❌ Could not find submission_id column in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update cancellation fields
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Prepare updates
                updates = []
                
                # Update cancelled status
                if cancelled_col is not None:
                    col_letter = column_index_to_letter(cancelled_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    value = "TRUE" if cancelled else "FALSE"
                    updates.append((range_name, value))
                
                # Update cancellation date (current date)
                if cancellation_date_col is not None and cancelled:
                    from datetime import datetime
                    col_letter = column_index_to_letter(cancellation_date_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updates.append((range_name, current_date))
                
                # Update cancellation reason
                if cancellation_reason_col is not None and reason:
                    col_letter = column_index_to_letter(cancellation_reason_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    updates.append((range_name, reason))
                
                # Update last minute flag
                if last_minute_col is not None:
                    col_letter = column_index_to_letter(last_minute_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    value = "TRUE" if is_last_minute else "FALSE"
                    updates.append((range_name, value))
                
                # Execute all updates
                for range_name, value in updates:
                    result = sheets_service.spreadsheets().values().update(
                        spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                        range=range_name,
                        valueInputOption='RAW',
                        body={'values': [[value]]}
                    ).execute()
                
                print(f"✅ Updated cancellation status for submission {submission_id}")
                if reason:
                    print(f"   Reason: {reason}")
                if is_last_minute:
                    print(f"   ⚠️ Last minute cancellation noted")
                
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating cancellation status: {e}")
        return False

def is_last_minute_cancellation(event_date_str: str, cancellation_date_str: str = None, threshold_days: int = 7):
    """Check if cancellation is considered last minute (within threshold days of event)"""
    try:
        from datetime import datetime, timedelta
        
        if not event_date_str:
            return False
        
        # Parse event date
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        
        # Use current date if no cancellation date provided
        if cancellation_date_str:
            cancellation_date = datetime.strptime(cancellation_date_str, "%Y-%m-%d")
        else:
            cancellation_date = datetime.now()
        
        # Check if cancellation is within threshold days of event
        days_before_event = (event_date - cancellation_date).days
        
        return days_before_event <= threshold_days
        
    except Exception as e:
        print(f"❌ Error checking last minute cancellation: {e}")
        return False

# --- Get status data (Google Sheets or mock) ---
def get_status_data(submission_id: str = None, telegram_user_id: str = None):
    """Get status data from Google Sheets or fallback to mock data"""
    if sheets_service and submission_id:
        # Try to get real data from Google Sheets
        sheet_data = find_submission_by_id(submission_id)
        if sheet_data:
            return sheet_data
    
    if sheets_service and telegram_user_id:
        # Try to get real data from Google Sheets by Telegram User ID
        sheet_data = find_submission_by_telegram_id(telegram_user_id)
        if sheet_data:
            return sheet_data
    
    return None

# Store user -> submission_id mapping (in production, use a database)
user_submissions = {}

# --- /start command handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    # Check if a submission ID was provided
    if context.args:
        submission_id = context.args[0]
        
        # Store the user -> submission_id mapping
        user_submissions[user_id] = submission_id
        
        # Get status data (from Google Sheets or mock data)
        status_data = get_status_data(submission_id=submission_id)
        
        if status_data:
            # Link the Telegram User ID to the submission in Google Sheets
            update_telegram_user_id(submission_id, user_id)
            
            # TASK: new registers - automatically mark them as 'Form Complete' TRUE
            # If I have a record, that means they filled out the form
            update_form_complete(submission_id, True)
            
            # TASK: returning participant - auto mark 'Get To Know Complete' as TRUE
            # If they participated in a previous event, they already know the process
            if status_data.get('is_returning_participant'):
                update_get_to_know_complete(submission_id, True)
            
            # Send welcome message
            await update.message.reply_text(
                get_message(status_data['language'], 'welcome', name=status_data['alias'])
            )
            
            # TASK: chat continues - keep the conversation going after /start
            # Guide user to their next step instead of letting conversation fade
            await continue_conversation(update, context, status_data)
        else:
            # Default to English if no submission found
            await update.message.reply_text(
                get_message('en', 'submission_not_found', submission_id=submission_id)
            )
    else:
        # No submission ID provided
        # Use Telegram user's language if available, otherwise default to English
        user_language = 'he' if user.language_code == 'he' else 'en'
        await update.message.reply_text(
            get_message(user_language, 'welcome_no_name')
        )

# --- /status command handler ---
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # Get the submission ID for this user (from local storage)
    submission_id = user_submissions.get(user_id)
    
    # Get status data from Google Sheets - try submission ID first, then Telegram User ID
    status_data = None
    if submission_id:
        status_data = get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = get_status_data(telegram_user_id=user_id)
    
    if not status_data:
        # Use Telegram user's language if available, otherwise default to English
        user_language = 'he' if update.effective_user.language_code == 'he' else 'en'
        await update.message.reply_text(
            get_message(user_language, 'no_submission_linked')
        )
        return
    
    # Build the status message
    message = get_status_message(status_data)
    
    await update.message.reply_text(message)

# --- /help command handler ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    # Try to get user's language from their submission data first
    submission_id = user_submissions.get(user_id)
    status_data = None
    
    if submission_id:
        status_data = get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = get_status_data(telegram_user_id=user_id)
    
    # Determine language
    if status_data and 'language' in status_data:
        language = status_data['language']
    else:
        # Fallback to Telegram user's language
        language = 'he' if user.language_code == 'he' else 'en'
    
    await update.message.reply_text(
        get_message(language, 'help')
    )

async def continue_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, status_data):
    """Continue the conversation by guiding user to their next step"""
    language = status_data.get('language', 'en')
    
    # TASK: 'Partner Complete' and 'Get To Know' parallel
    # We can nudge about partner form and get to know a new register simultaneously
    parallel_tasks = []
    
    # TASK: multi partner - check if all partners are registered and remind about missing ones
    partner_status = status_data.get('partner_status', {})
    missing_partners = partner_status.get('missing_partners', [])
    
    if missing_partners:
        # User has multiple partners and some are missing
        if language == 'he':
            if len(missing_partners) == 1:
                parallel_tasks.append(f"👥 רוצה שאשלח ל{missing_partners[0]} תזכורת להשלים את הטופס?")
            else:
                missing_names = ', '.join(missing_partners)
                parallel_tasks.append(f"👥 רוצה שאשלח תזכורת ל{missing_names} להשלים את הטופס?")
        else:
            if len(missing_partners) == 1:
                parallel_tasks.append(f"👥 Would you like me to send a reminder to {missing_partners[0]} to complete the form?")
            else:
                missing_names = ', '.join(missing_partners)
                parallel_tasks.append(f"👥 Would you like me to send reminders to {missing_names} to complete the form?")
    
    # Check for get-to-know tasks (for non-returning participants)
    if not status_data.get('get_to_know') and not status_data.get('is_returning_participant'):
        # User needs to complete get-to-know section
        if language == 'he':
            parallel_tasks.append("💬 אתה יכול להשלים את חלק ההיכרות. זה עוזר לנו ליצור סביבה בטוחה ונוחה לכולם.")
        else:
            parallel_tasks.append("💬 You can complete the get-to-know section. This helps us create a safe and comfortable environment for everyone.")
    
    # Send parallel tasks if any exist
    if parallel_tasks:
        if language == 'he':
            intro_message = "הצעדים הבאים שלך:"
        else:
            intro_message = "Your next steps:"
        
        await update.message.reply_text(intro_message)
        
        for task in parallel_tasks:
            await update.message.reply_text(task)
    
    # Handle sequential steps (can't be done in parallel)
    elif not status_data.get('approved'):
        # User is waiting for approval
        if language == 'he':
            message = "⏳ כל הטפסים שלך הושלמו! הבקשה שלך ממתינה לאישור מהמארגנים. נעדכן אותך ברגע שנקבל החלטה."
        else:
            message = "⏳ All your forms are complete! Your application is now waiting for organizer approval. We'll update you as soon as we have a decision."
        await update.message.reply_text(message)
        
    elif not status_data.get('paid'):
        # User is approved but needs to pay
        if language == 'he':
            message = "🎉 בקשתך אושרה! הצעד הבא הוא לבצע תשלום כדי לאשר את מקומך באירוע."
        else:
            message = "🎉 Your application has been approved! The next step is to complete payment to confirm your spot at the event."
        await update.message.reply_text(message)
        
    elif not status_data.get('group_open'):
        # User is fully registered, waiting for group to open
        if language == 'he':
            message = "✅ הרשמתך הושלמה! קבוצת האירוע תיפתח שבוע לפני האירוע. נעדכן אותך ברגע שהקבוצה תהיה מוכנה."
        else:
            message = "✅ Your registration is complete! The event group will open one week before the event. We'll let you know as soon as the group is ready."
        await update.message.reply_text(message)
        
    else:
        # User is fully registered and group is open
        if language == 'he':
            message = "🎊 מעולה! הרשמתך הושלמה וקבוצת האירוע פתוחה. אתה מוכן לאירוע!"
        else:
            message = "🎊 Perfect! Your registration is complete and the event group is open. You're all set for the event!"
        await update.message.reply_text(message)
        
    # Always offer to check status or get help
    if language == 'he':
        help_message = "💡 תוכל לבדוק את הסטטוס שלך בכל זמן עם /status או לקבל עזרה עם /help"
    else:
        help_message = "💡 You can check your status anytime with /status or get help with /help"
    await update.message.reply_text(help_message)

# --- /remind_partner command handler ---
async def remind_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a reminder to partner(s) to complete their form"""
    user_id = str(update.effective_user.id)
    
    # Get the submission ID for this user
    submission_id = user_submissions.get(user_id)
    
    # Get status data from Google Sheets
    status_data = None
    if submission_id:
        status_data = get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = get_status_data(telegram_user_id=user_id)
    
    if not status_data:
        # Use Telegram user's language if available, otherwise default to English
        user_language = 'he' if update.effective_user.language_code == 'he' else 'en'
        await update.message.reply_text(
            get_message(user_language, 'no_submission_linked')
        )
        return
    
    language = status_data.get('language', 'en')
    
    # Check if user has partners and if any are missing
    partner_status = status_data.get('partner_status', {})
    missing_partners = partner_status.get('missing_partners', [])
    
    if not missing_partners:
        # No missing partners
        if language == 'he':
            message = "✅ כל הפרטנרים שלך כבר השלימו את הטופס!"
        else:
            message = "✅ All your partners have already completed the form!"
        await update.message.reply_text(message)
        return
    
    # Send reminders to missing partners
    success_count = 0
    failed_partners = []
    
    for partner_name in missing_partners:
        try:
            # Try to send reminder (this would normally involve finding partner's contact info)
            # For now, we'll simulate sending and track the reminder
            reminder_sent = await send_partner_reminder(
                partner_name=partner_name,
                requester_name=status_data.get('alias', 'your partner'),
                language=language
            )
            
            if reminder_sent:
                success_count += 1
                # Log the reminder in the system
                await log_reminder_sent(
                    submission_id=submission_id,
                    partner_name=partner_name,
                    reminder_type='manual_partner_reminder'
                )
            else:
                failed_partners.append(partner_name)
                
        except Exception as e:
            print(f"❌ Error sending reminder to {partner_name}: {e}")
            failed_partners.append(partner_name)
    
    # Send response to user
    if success_count > 0:
        if language == 'he':
            if success_count == 1:
                message = f"✅ תזכורת נשלחה ל{missing_partners[0]}!"
            else:
                message = f"✅ תזכורות נשלחו ל{success_count} פרטנרים!"
        else:
            if success_count == 1:
                message = f"✅ Reminder sent to {missing_partners[0]}!"
            else:
                message = f"✅ Reminders sent to {success_count} partners!"
        
        await update.message.reply_text(message)
    
    if failed_partners:
        if language == 'he':
            failed_names = ', '.join(failed_partners)
            message = f"❌ לא הצלחנו לשלוח תזכורת ל: {failed_names}"
        else:
            failed_names = ', '.join(failed_partners)
            message = f"❌ Failed to send reminders to: {failed_names}"
        
        await update.message.reply_text(message)

async def send_partner_reminder(partner_name: str, requester_name: str, language: str = 'en'):
    """Send a reminder to a partner (placeholder implementation)"""
    # TODO: Implement actual partner reminder sending
    # This could involve:
    # 1. Looking up partner's contact info from the database
    # 2. Sending an email or SMS
    # 3. Sending a Telegram message if they're registered
    # 4. Creating a notification in the system
    
    print(f"🔔 Sending reminder to {partner_name} from {requester_name}")
    
    # For now, just simulate success
    # In a real implementation, this would:
    # - Find partner's contact info
    # - Send actual reminder via preferred method
    # - Return True/False based on success
    
    return True  # Simulated success

async def log_reminder_sent(submission_id: str, partner_name: str, reminder_type: str):
    """Log that a reminder was sent"""
    from datetime import datetime
    
    # TODO: Implement actual logging to database or Google Sheets
    timestamp = datetime.now().isoformat()
    
    print(f"📝 Logged reminder: {submission_id} -> {partner_name} ({reminder_type}) at {timestamp}")
    
    # In a real implementation, this would:
    # - Add a row to a reminders log sheet
    # - Update the main sheet with reminder status
    # - Store in a database table
    
    return True

# --- /cancel command handler ---
async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user cancellation with reason and timing"""
    user_id = str(update.effective_user.id)
    
    # Get the submission ID for this user
    submission_id = user_submissions.get(user_id)
    
    # Get status data from Google Sheets
    status_data = None
    if submission_id:
        status_data = get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = get_status_data(telegram_user_id=user_id)
    
    if not status_data:
        # Use Telegram user's language if available, otherwise default to English
        user_language = 'he' if update.effective_user.language_code == 'he' else 'en'
        await update.message.reply_text(
            get_message(user_language, 'no_submission_linked')
        )
        return
    
    language = status_data.get('language', 'en')
    
    # Check if user provided a reason
    reason = " ".join(context.args) if context.args else ""
    
    if not reason:
        # Ask for cancellation reason
        if language == 'he':
            message = "אנא ספק סיבה לביטול (לדוגמה: /cancel מחלה פתאומית)"
        else:
            message = "Please provide a reason for cancellation (e.g., /cancel sudden illness)"
        await update.message.reply_text(message)
        return
    
    # TASK: cancellation - mark cancellation with reason and timing
    # Check if this is a last minute cancellation (you would need event date from somewhere)
    # For now, assume it's last minute if payment was completed (event is soon)
    is_last_minute = status_data.get('paid', False)
    
    # Update cancellation status
    success = update_cancellation_status(
        submission_id=status_data['submission_id'],
        cancelled=True,
        reason=reason,
        is_last_minute=is_last_minute
    )
    
    if success:
        if language == 'he':
            message = f"הרשמתך בוטלה.\n\nסיבה: {reason}"
            if is_last_minute:
                message += "\n\n⚠️ שים לב: זהו ביטול ברגע האחרון וזה יילקח בחשבון בבקשות עתידיות."
        else:
            message = f"Your registration has been cancelled.\n\nReason: {reason}"
            if is_last_minute:
                message += "\n\n⚠️ Note: This is a last-minute cancellation and will be taken into account for future applications."
        
        await update.message.reply_text(message)
    else:
        if language == 'he':
            message = "❌ שגיאה בביטול הרשמה. אנא פנה לתמיכה."
        else:
            message = "❌ Error cancelling registration. Please contact support."
        await update.message.reply_text(message)

# --- Automatic Reminder System ---
class ReminderScheduler:
    """Handles automatic reminders based on time and user state"""
    
    def __init__(self, bot_application):
        self.bot = bot_application
        self.reminder_intervals = {
            # 'partner_pending': 24 * 60 * 60,  # 24 hours in seconds
            'partner_pending': 1 * 60,  # 24 hours in seconds
            'payment_pending': 3 * 24 * 60 * 60,  # 3 days
            'group_opening': 7 * 24 * 60 * 60,  # 7 days before event
            'event_reminder': 24 * 60 * 60,  # 1 day before event
        }
        self.last_reminder_check = {}
        
    def quick_completion_check(self, row, column_indices):
        """Quick check if user needs any reminders without expensive parsing"""
        def get_cell_value(key, default=""):
            index = column_indices.get(key)
            if index is not None and index < len(row):
                return row[index]
            return default
        
        def get_boolean_value(key, default=False):
            """Get a boolean value from the sheet, handling various formats"""
            value = get_cell_value(key, "").strip().upper()
            if value in ['TRUE', 'YES', 'כן', '1', 'V', '✓']:
                return True
            elif value in ['FALSE', 'NO', 'לא', '0', '', 'X']:
                return False
            return default
        
        # Get essential info without expensive parsing
        submission_id = get_cell_value('submission_id')
        telegram_user_id = get_cell_value('telegram_user_id')
        
        if not submission_id or not telegram_user_id:
            return None  # Can't process without these
        
        # Check completion status
        partner_complete = get_boolean_value('partner_complete', False)
        approved = get_boolean_value('admin_approved', False)
        paid = get_boolean_value('payment_complete', False)
        group_open = get_boolean_value('group_access', False)
        
        return {
            'submission_id': submission_id,
            'telegram_user_id': telegram_user_id,
            'partner_complete': partner_complete,
            'approved': approved,
            'paid': paid,
            'group_open': group_open,
            'needs_reminders': not (partner_complete and approved and paid and group_open)
        }
    
    async def check_and_send_reminders(self):
        """Check all users and send appropriate reminders"""
        print("🔔 Checking for pending reminders...")
        
        # Get all sheet data
        sheet_data = get_sheet_data()
        if not sheet_data:
            print("⚠️  No sheet data available for reminder checking")
            return
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = get_column_indices(headers)
        
        # Counters for efficiency tracking
        total_users = 0
        skipped_users = 0
        processed_users = 0
        reminders_sent = 0
        
        # Process each user
        for row in rows:
            try:
                # Quick pre-check without expensive parsing
                quick_check = self.quick_completion_check(row, column_indices)
                if not quick_check:
                    continue
                
                total_users += 1
                
                # Skip if user doesn't need any reminders
                if not quick_check['needs_reminders']:
                    skipped_users += 1
                    print(f"⏭️  Skipping {quick_check['submission_id']} - fully complete (quick check)")
                    continue
                
                # Only do expensive parsing if user needs reminders
                user_data = parse_submission_row(row, column_indices)
                if not user_data or not user_data.get('submission_id'):
                    continue
                
                processed_users += 1
                
                # Check if user needs reminders
                result = await self.check_user_reminders(user_data)
                
            except Exception as e:
                print(f"❌ Error processing reminder for row: {e}")
                continue
        
        print(f"📊 Reminder check summary: {total_users} users total, {skipped_users} skipped (quick check), {processed_users} processed")
    
    async def check_user_reminders(self, user_data: Dict):
        """Check if a specific user needs any reminders"""
        submission_id = user_data.get('submission_id')
        telegram_user_id = user_data.get('telegram_user_id')
        user_name = user_data.get('alias', 'Unknown')
        
        if not telegram_user_id:
            return  # Can't send reminders without Telegram ID
        
        # Early exit if user is fully complete - no need to check any reminders
        if (user_data.get('partner', False) and 
            user_data.get('approved', False) and 
            user_data.get('paid', False) and 
            user_data.get('group_open', False)):
            print(f"⏭️  Skipping {user_name} - fully complete")
            return  # User is fully complete, no reminders needed
        
        # Check different reminder types (only if needed)
        if not user_data.get('partner', False):
            await self.check_partner_reminder(user_data)
        else:
            print(f"⏭️  Skipping partner check for {user_name} - partner complete")
        
        if user_data.get('approved', False) and not user_data.get('paid', False):
            await self.check_payment_reminder(user_data)
        
        if user_data.get('paid', False) and not user_data.get('group_open', False):
            await self.check_group_reminder(user_data)
        
        if user_data.get('group_open', False):
            await self.check_event_reminder(user_data)
    
    async def check_partner_reminder(self, user_data: Dict):
        """Check if user needs a partner reminder"""
        # Early exit if partner is already complete
        if user_data.get('partner', False):
            return  # Partner requirements already met
        
        submission_id = user_data.get('submission_id')
        partner_status = user_data.get('partner_status', {})
        missing_partners = partner_status.get('missing_partners', [])
        
        if not missing_partners:
            print(f"⏭️  No missing partners for {user_data.get('alias', 'Unknown')}")
            return  # No missing partners
        
        # Check if 24 hours have passed since last partner reminder
        last_reminder_key = f"{submission_id}_partner"
        now = datetime.now()
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (now - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['partner_pending']:
                print(f"⏭️  Too soon for partner reminder for {user_data.get('alias', 'Unknown')}")
                return  # Too soon for another reminder
        
        # Send partner reminder
        print(f"🔔 Sending partner reminder to {user_data.get('alias', 'Unknown')} for missing: {missing_partners}")
        await self.send_automatic_partner_reminder(user_data, missing_partners)
        self.last_reminder_check[last_reminder_key] = now
    
    async def check_payment_reminder(self, user_data: Dict):
        """Check if user needs a payment reminder"""
        # Early exit conditions moved to check_user_reminders for efficiency
        submission_id = user_data.get('submission_id')
        last_reminder_key = f"{submission_id}_payment"
        now = datetime.now()
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (now - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['payment_pending']:
                return  # Too soon for another reminder
        
        # Send payment reminder
        await self.send_automatic_payment_reminder(user_data)
        self.last_reminder_check[last_reminder_key] = now
    
    async def check_group_reminder(self, user_data: Dict):
        """Check if user needs a group opening reminder"""
        # Early exit conditions moved to check_user_reminders for efficiency
        
        # TODO: Check if it's 7 days before event
        # For now, simulate group opening reminder
        submission_id = user_data.get('submission_id')
        last_reminder_key = f"{submission_id}_group"
        now = datetime.now()
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (now - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['group_opening']:
                return  # Too soon for another reminder
        
        # Send group opening reminder
        await self.send_automatic_group_reminder(user_data)
        self.last_reminder_check[last_reminder_key] = now
    
    async def check_event_reminder(self, user_data: Dict):
        """Check if user needs an event reminder"""
        if not user_data.get('group_open'):
            return  # Group not open yet
        
        # TODO: Check if it's 1 day before event
        # This would require event date information
        pass
    
    async def send_automatic_partner_reminder(self, user_data: Dict, missing_partners: List[str]):
        """Send automatic partner reminder"""
        telegram_user_id = user_data.get('telegram_user_id')
        language = user_data.get('language', 'en')
        
        if not telegram_user_id:
            return
        
        try:
            if language == 'he':
                if len(missing_partners) == 1:
                    message = f"🔔 תזכורת: עדיין מחכים ל{missing_partners[0]} להשלים את הטופס. רוצה לשלוח להם תזכורת? השתמש ב /remind_partner"
                else:
                    missing_names = ', '.join(missing_partners)
                    message = f"🔔 תזכורת: עדיין מחכים ל{missing_names} להשלים את הטופס. השתמש ב /remind_partner"
            else:
                if len(missing_partners) == 1:
                    message = f"🔔 Reminder: Still waiting for {missing_partners[0]} to complete the form. Want to send them a reminder? Use /remind_partner"
                else:
                    missing_names = ', '.join(missing_partners)
                    message = f"🔔 Reminder: Still waiting for {missing_names} to complete the form. Use /remind_partner"
            
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await log_reminder_sent(
                submission_id=user_data.get('submission_id'),
                partner_name=', '.join(missing_partners),
                reminder_type='automatic_partner_reminder'
            )
            
        except Exception as e:
            print(f"❌ Error sending automatic partner reminder: {e}")
    
    async def send_automatic_payment_reminder(self, user_data: Dict):
        """Send automatic payment reminder"""
        telegram_user_id = user_data.get('telegram_user_id')
        language = user_data.get('language', 'en')
        
        if not telegram_user_id:
            return
        
        try:
            if language == 'he':
                message = "💸 תזכורת תשלום: הרשמתך אושרה! אנא השלם את התשלום כדי לאשר את מקומך באירוע."
            else:
                message = "💸 Payment reminder: Your registration has been approved! Please complete payment to confirm your spot at the event."
            
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await log_reminder_sent(
                submission_id=user_data.get('submission_id'),
                partner_name='',
                reminder_type='automatic_payment_reminder'
            )
            
        except Exception as e:
            print(f"❌ Error sending automatic payment reminder: {e}")
    
    async def send_automatic_group_reminder(self, user_data: Dict):
        """Send automatic group opening reminder"""
        telegram_user_id = user_data.get('telegram_user_id')
        language = user_data.get('language', 'en')
        
        if not telegram_user_id:
            return
        
        try:
            if language == 'he':
                message = "👥 הקבוצה פתוחה! קבוצת האירוע שלך פתוחה עכשיו. בואו להכיר או פשוט לצפות בשקט - מה שמתאים לכם! 🧘"
            else:
                message = "👥 Group is open! Your event group is now open. Come meet others, share vibes, or just lurk quietly if that's your vibe! 🧘"
            
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await log_reminder_sent(
                submission_id=user_data.get('submission_id'),
                partner_name='',
                reminder_type='automatic_group_reminder'
            )
            
        except Exception as e:
            print(f"❌ Error sending automatic group reminder: {e}")

# Global reminder scheduler
reminder_scheduler = None

async def start_reminder_scheduler(bot_application):
    """Start the automatic reminder scheduler"""
    global reminder_scheduler
    reminder_scheduler = ReminderScheduler(bot_application)
    
    # Run reminder checks every hour
    while True:
        try:
            await reminder_scheduler.check_and_send_reminders()
            await asyncio.sleep(50)  # Sleep for 1 hour
        except Exception as e:
            print(f"❌ Error in reminder scheduler: {e}")
            await asyncio.sleep(300)  # Sleep for 5 minutes on error, then retry

# --- Bot token from environment variable ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required. Please set it in your .env file.")

# --- Main runner ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("remind_partner", remind_partner))
    app.add_handler(CommandHandler("cancel", cancel_registration))

    print("Bot is running with polling...")
    
    # Define the scheduler function for the job queue
    async def scheduled_reminder_check(context):
        """Check and send reminders - called by job queue"""
        try:
            global reminder_scheduler
            if not reminder_scheduler:
                reminder_scheduler = ReminderScheduler(app)
            
            print("🔔 Checking for pending reminders...")
            await reminder_scheduler.check_and_send_reminders()
        except Exception as e:
            print(f"❌ Error in scheduled reminder check: {e}")
    
    # Add the reminder job to the job queue (every 50 seconds as per user's testing)
    job_queue = app.job_queue
    job_queue.run_repeating(scheduled_reminder_check, interval=50, first=10)
    
    print("🔔 Reminder scheduler added to job queue (checking every 50 seconds)")
    
    try:
        # Run the bot normally
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        if "Conflict" in str(e):
            print("❌ Error: Another instance of the bot is already running!")
            print("Solutions:")
            print("1. Stop any other running instances of this bot")
            print("2. Wait a few seconds and try again")
            print("3. If you have a webhook configured, disable it first")
            print("4. Check your task manager for other Python processes")
        else:
            print(f"❌ Error starting bot: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)
