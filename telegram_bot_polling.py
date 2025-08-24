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

from telegram_bot.config import settings
from telegram_bot.services.form_flow_service import FormFlowService
from telegram_bot.services.validation_service import ValidationService
from telegram_bot.services.sheets_service import SheetsService

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# --- Admin Configuration ---
# Admin user IDs - these are Telegram User IDs of administrators
ADMIN_USER_IDS = []
admin_ids_env = os.getenv("ADMIN_USER_IDS", "")
if admin_ids_env:
    try:
        ADMIN_USER_IDS = [int(id.strip()) for id in admin_ids_env.split(",") if id.strip()]
        print(f"✅ Admin users configured: {len(ADMIN_USER_IDS)} admins")
    except ValueError:
        print("❌ Invalid ADMIN_USER_IDS format. Please use comma-separated integers.")

# Admin notification preferences
ADMIN_NOTIFICATIONS = {
    'new_registrations': True,
    'new_get_to_know_responses': True,
    'ready_for_review': True,
    'partner_delays': True,
    'payment_overdue': True,
    'weekly_digest': True,
    'status_changes': True
}

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
                "/get_to_know - Complete the get-to-know section\n"
                "/remind_partner - Send reminder to your partner\n"
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
                "/get_to_know - השלמת חלק ההיכרות\n"
                "/remind_partner - שליחת תזכורת לשותף\n"
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
    
    # Handle invalid language codes gracefully
    if language not in MESSAGES:
        language = 'en'
    
    labels = MESSAGES[language]['status_labels']
    
    # Build detailed partner text
    partner_text = build_partner_status_text(status_data, language)
    
    # Build status text (with safe defaults for malformed data)
    status_text = labels['approved'] if status_data.get('approved', False) else labels['waiting_review']
    
    # Build payment text
    payment_text = labels['paid'] if status_data.get('paid', False) else labels['not_paid']
    
    # Build group text
    group_text = labels['group_open'] if status_data.get('group_open', False) else labels['group_not_open']
    
    # Construct the message (with safe defaults for malformed data)
    message = (
        f"{labels['form']}: {'✅' if status_data.get('form', False) else '❌'}\n"
        f"{partner_text}\n"
        f"{labels['get_to_know']}: {'✅' if status_data.get('get_to_know', False) else '❌'}\n"
        f"{labels['status']}: {status_text}\n"
        f"{labels['payment']}: {payment_text}\n"
        f"{labels['group']}: {group_text}\n\n"
    )
    
    return message

# Initialize Google Sheets service
sheets_service = SheetsService()

# --- Google Sheets functions ---
def parse_submission_row(row, column_indices):
    """Parse a row from the sheet into our status format"""
    
    def parse_multiple_partners(partner_text):
        """Parse multiple partner names from text"""
        if not partner_text:
            return []
        
        # Split by common separators
        separators = [',', '&', '+', 'ו', ' ו ', 'and', ' and ']
        partners = [partner_text.strip()]
        
        for separator in separators:
            new_partners = []
            for partner in partners:
                if separator in partner:
                    new_partners.extend([p.strip() for p in partner.split(separator) if p.strip()])
                else:
                    new_partners.append(partner)
            partners = new_partners
        
        return [p for p in partners if p and p.strip()]
    
    def check_partner_registration_status(partner_names):
        """Check which partners are registered (simplified version)"""
        if not partner_names:
            return {
                'all_registered': True,
                'registered_partners': [],
                'missing_partners': []
            }
        
        # For now, we'll return a simplified status
        # In a full implementation, this would check against the full sheet data
        return {
            'all_registered': False,
            'registered_partners': [],
            'missing_partners': partner_names
        }
    
    # Extract basic information
    submission_id = sheets_service.get_cell_value(row, 'submission_id')
    full_name = sheets_service.get_cell_value(row, 'full_name')
    telegram_user_id = sheets_service.get_cell_value(row, 'telegram_user_id')
    
    # Get language preference
    language = sheets_service.get_language_preference(row)
    
    # Get status columns
    form_complete = sheets_service.get_boolean_value(row, 'form_complete', False)
    partner_complete = sheets_service.get_boolean_value(row, 'partner_complete', False)
    get_to_know_complete = sheets_service.get_boolean_value(row, 'get_to_know_complete', False)
    admin_approved = sheets_service.get_boolean_value(row, 'admin_approved', False)
    payment_complete = sheets_service.get_boolean_value(row, 'payment_complete', False)
    group_access = sheets_service.get_boolean_value(row, 'group_access', False)
    
    # Get cancellation info
    cancelled = sheets_service.get_boolean_value(row, 'cancelled', False)
    cancellation_reason = sheets_service.get_cell_value(row, 'cancellation_reason')
    
    # Get returning participant status
    returning_participant = sheets_service.get_boolean_value(row, 'returning_participant', False)
    
    # Handle partner information (only if partner not already complete)
    partner_names = []
    partner_status = {}
    partner_alias = None
    
    if not partner_complete:
        # Only do expensive partner parsing if needed
        coming_alone = sheets_service.get_cell_value(row, 'coming_alone_or_balance')
        partner_name_text = sheets_service.get_cell_value(row, 'partner_name')
        
        if partner_name_text and 'לבד' not in coming_alone:
            # Parse partner names
            partner_names = parse_multiple_partners(partner_name_text)
            partner_alias = partner_name_text if len(partner_names) == 1 else None
            
            # Check partner registration status
            partner_status = check_partner_registration_status(partner_names)
            
            # Auto-update partner complete if all registered
            if partner_status.get('all_registered', False):
                partner_complete = True
                # In a full implementation, you'd call update_partner_complete here
        else:
            # Coming alone
            partner_complete = True
    else:
        # Partner already complete, just get the names for display
        partner_name_text = sheets_service.get_cell_value(row, 'partner_name')
        if partner_name_text:
            partner_names = parse_multiple_partners(partner_name_text)
            partner_alias = partner_name_text if len(partner_names) == 1 else None
    
    # Check if returning participant should auto-complete get-to-know
    if returning_participant and not get_to_know_complete:
        get_to_know_complete = True
        # In a full implementation, you'd call update_get_to_know_complete here
    
    # Build the result dictionary
    result = {
        'submission_id': submission_id,
        'alias': full_name,
        'telegram_user_id': telegram_user_id,
        'language': language,
        'form': form_complete,
        'partner': partner_complete,
        'get_to_know': get_to_know_complete,
        'approved': admin_approved,
        'paid': payment_complete,
        'group_open': group_access,
        'cancelled': cancelled,
        'cancellation_reason': cancellation_reason,
        'is_returning_participant': returning_participant,
        'partner_names': partner_names,
        'partner_alias': partner_alias,
        'partner_status': partner_status
    }
    
    return result

def update_form_complete(submission_id: str, form_complete: bool = True):
    """Update the Form Complete field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Form Complete")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
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
                col_letter = sheets_service.column_index_to_letter(form_complete_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if form_complete else "FALSE"
                result = sheets_service.update_range(range_name, value)
                
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
        sheet_data = sheets_service.get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
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
                col_letter = sheets_service.column_index_to_letter(get_to_know_complete_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if get_to_know_complete else "FALSE"
                result = sheets_service.update_range(range_name, value)
                
                print(f"✅ Updated Get To Know Complete to {value} for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Get To Know Complete: {e}")
        return False

def update_payment_complete(submission_id: str, payment_complete: bool = True):
    """Update the Payment Complete field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Payment Complete")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        payment_complete_col = column_indices.get('payment_complete')
        
        if submission_id_col is None or payment_complete_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the Payment Complete field
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Convert column index to letter using proper function
                col_letter = sheets_service.column_index_to_letter(payment_complete_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if payment_complete else "FALSE"
                result = sheets_service.update_range(range_name, value)
                
                print(f"✅ Updated Payment Complete to {value} for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Payment Complete: {e}")
        return False

def update_group_access(submission_id: str, group_access: bool = True):
    """Update the Group Access field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Group Access")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        group_access_col = column_indices.get('group_access')
        
        if submission_id_col is None or group_access_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the Group Access field
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Convert column index to letter
                col_letter = sheets_service.column_index_to_letter(group_access_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if group_access else "FALSE"
                result = sheets_service.update_range(range_name, value)
                
                print(f"✅ Updated Group Access to {value} for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Group Access: {e}")
        return False

def update_status(submission_id: str, status: str = "Ready for Review", approved: bool = False, paid: bool = False, group_open: bool = False):
    """Update the status of a submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update status")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data()
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        status_col = column_indices.get('status')
        approved_col = column_indices.get('admin_approved')
        paid_col = column_indices.get('payment_complete')
        group_open_col = column_indices.get('group_access')
        
        if submission_id_col is None or status_col is None or approved_col is None or paid_col is None or group_open_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the status
                sheet_row = row_index + 4  # Adjust for header row and 0-based indexing
                
                # Convert column index to letter
                col_letter = sheets_service.column_index_to_letter(status_col) 
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell
                result = sheets_service.update_range(range_name, status)
                
                # Update approval status
                if approved_col is not None:
                    col_letter = sheets_service.column_index_to_letter(approved_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    result = sheets_service.update_range(range_name, approved)
                
                # Update payment status
                if paid_col is not None:
                    col_letter = sheets_service.column_index_to_letter(paid_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    result = sheets_service.update_range(range_name, paid)
                
                # Update group open status
                if group_open_col is not None:
                    col_letter = sheets_service.column_index_to_letter(group_open_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    result = sheets_service.update_range(range_name, group_open)
                
                print(f"✅ Updated status for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        return False

def update_cancellation_status(submission_id: str, cancelled: bool = True, reason: str = "", is_last_minute: bool = False):
    """Update cancellation status with reason and timing information"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update cancellation status")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data() 
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
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
                    col_letter = sheets_service.column_index_to_letter(cancelled_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    value = "TRUE" if cancelled else "FALSE"
                    updates.append((range_name, value))
                
                # Update cancellation date (current date)
                if cancellation_date_col is not None and cancelled:
                    from datetime import datetime
                    col_letter = sheets_service.column_index_to_letter(cancellation_date_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updates.append((range_name, current_date))
                
                # Update cancellation reason
                if cancellation_reason_col is not None and reason:
                    col_letter = sheets_service.column_index_to_letter(cancellation_reason_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    updates.append((range_name, reason))
                
                # Update last minute flag
                if last_minute_col is not None:
                    col_letter = sheets_service.column_index_to_letter(last_minute_col) 
                    range_name = f"managed!{col_letter}{sheet_row}"
                    value = "TRUE" if is_last_minute else "FALSE"
                    updates.append((range_name, value))
                
                # Execute all updates
                for range_name, value in updates:
                    result = sheets_service.update_range(range_name, value)
                
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
async def get_status_data(submission_id: str = None, telegram_user_id: str = None):
    """Get status data from Google Sheets or fallback to mock data"""
    if sheets_service and submission_id:
        # Try to get real data from Google Sheets
        sheet_data = await sheets_service.find_submission_by_id(submission_id)
        if sheet_data:
            return sheet_data
    
    if sheets_service and telegram_user_id:
        # Try to get real data from Google Sheets by Telegram User ID
        sheet_data = await sheets_service.find_submission_by_telegram_id(telegram_user_id)
        if sheet_data:
            return sheet_data
    
    return None

# Store user -> submission_id mapping (in production, use a database)
user_submissions = {}

# --- Admin Functions ---
def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    return user_id in ADMIN_USER_IDS

async def notify_admins(message: str, notification_type: str = "general"):
    """Send notification to all admins"""
    if not ADMIN_USER_IDS:
        print("⚠️  No admin users configured - skipping admin notification")
        return
    
    if not ADMIN_NOTIFICATIONS.get(notification_type, True):
        print(f"⚠️  Admin notifications disabled for type: {notification_type}")
        return
    
    from telegram import Bot
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    
    for admin_id in ADMIN_USER_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"🔔 **Admin Notification**\n\n{message}",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"❌ Failed to send admin notification to {admin_id}: {e}")

async def notify_registration_ready_for_review(submission_id: str, user_name: str, partner_info: str = ""):
    """Notify admins when a registration is ready for review"""
    partner_text = f" (Partner: {partner_info})" if partner_info else ""
    message = (
        f"📋 **New Registration Ready for Review**\n\n"
        f"**User:** {user_name}\n"
        f"**Submission ID:** {submission_id}{partner_text}\n"
        f"**Status:** Ready for approval\n\n"
        f"Please review and approve/reject this registration."
    )
    
    await notify_admins(message, "ready_for_review")

async def notify_partner_delay(submission_id: str, user_name: str, missing_partners: list):
    """Notify admins about partner registration delays"""
    missing_text = ", ".join(missing_partners)
    message = (
        f"⏰ **Partner Registration Delay**\n\n"
        f"**User:** {user_name}\n"
        f"**Submission ID:** {submission_id}\n"
        f"**Missing Partners:** {missing_text}\n\n"
        f"Partners have been pending for >24 hours. Consider manual follow-up."
    )
    
    await notify_admins(message, "partner_delays")

async def notify_payment_overdue(submission_id: str, user_name: str, days_overdue: int):
    """Notify admins about overdue payments"""
    message = (
        f"💸 **Payment Overdue**\n\n"
        f"**User:** {user_name}\n"
        f"**Submission ID:** {submission_id}\n"
        f"**Days Overdue:** {days_overdue}\n\n"
        f"Approved registration has not completed payment. Consider follow-up."
    )
    
    await notify_admins(message, "payment_overdue")

async def check_and_notify_ready_for_review(status_data: dict):
    """Check if a registration is ready for review and notify admins"""
    if not status_data:
        return
    
    # Check if user is ready for review: form, partner, get-to-know complete but not approved
    if (status_data.get('form', False) and 
        status_data.get('partner', False) and 
        status_data.get('get_to_know', False) and 
        not status_data.get('approved', False)):
        
        # Get partner info for notification
        partner_info = ""
        if status_data.get('partner_names'):
            partner_info = ", ".join(status_data['partner_names'])
        elif status_data.get('partner_alias'):
            partner_info = status_data['partner_alias']
        
        # Notify admins
        await notify_registration_ready_for_review(
            submission_id=status_data.get('submission_id', 'Unknown'),
            user_name=status_data.get('alias', 'Unknown'),
            partner_info=partner_info
        )

def update_admin_approved(submission_id: str, approved: bool = True):
    """Update the Admin Approved field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Admin Approved")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data() 
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers) 
        
        submission_id_col = column_indices.get('submission_id')
        admin_approved_col = column_indices.get('admin_approved')
        
        if submission_id_col is None or admin_approved_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Calculate the actual row number (adding 2 for header row and 0-based indexing)
                actual_row = row_index + 2
                
                # Convert column index to letter
                admin_approved_col_letter = sheets_service.column_index_to_letter(admin_approved_col)
                
                # Update the cell
                range_name = f"{admin_approved_col_letter}{actual_row}"
                
                body = {
                    'values': [['TRUE' if approved else 'FALSE']]
                }
                
                result = sheets_service.update_range(range_name, body)
                
                print(f"✅ Admin approval updated for {submission_id}: {approved}")
                return True
        
        print(f"❌ Submission ID {submission_id} not found in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating admin approval: {e}")
        return False

def update_partner_complete(submission_id: str, partner_complete: bool = True):
    """Update the Partner Complete field for a specific submission in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot update Partner Complete")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data() 
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices using the helper function
        column_indices = sheets_service.get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        partner_complete_col = column_indices.get('partner_complete')
        
        if submission_id_col is None or partner_complete_col is None:
            print("❌ Could not find required columns in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the Partner Complete field
                # Row index in the sheet = row_index + 4 (header row + 1-based indexing + start from row 3)
                sheet_row = row_index + 4
                
                # Convert column index to letter using proper function
                col_letter = sheets_service.column_index_to_letter(partner_complete_col) 
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell with TRUE/FALSE
                value = "TRUE" if partner_complete else "FALSE"
                result = sheets_service.update_range(range_name, value)
                
                print(f"✅ Updated Partner Complete to {value} for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error updating Partner Complete: {e}")
        return False


# --- Start of Form Flow Implementation ---
validation_service = ValidationService()
form_flow_service = FormFlowService(validation_service, sheets_service)

# --- End of Form Flow Implementation ---

# --- /start command handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    # Start the form flow
    result = await form_flow_service.start_form(user_id)   
    
    # Check if a submission ID was provided
    if context.args:
        submission_id = context.args[0]
        
        # Store the user -> submission_id mapping
        user_submissions[user_id] = submission_id
        
        # Get status data (from Google Sheets or mock data)
        status_data = await get_status_data(submission_id=submission_id)
        
        if status_data:
            # Link the Telegram User ID to the submission in Google Sheets
            await sheets_service.update_telegram_user_id(submission_id, user_id)
            
            # TASK: new registers - automatically mark them as 'Form Complete' TRUE
            # If I have a record, that means they filled out the form
            update_form_complete(submission_id, True)
            
            # TASK: returning participant - auto mark 'Get To Know Complete' as TRUE
            # If they participated in a previous event, they already know the process
            if status_data.get('is_returning_participant'):
                update_get_to_know_complete(submission_id, True)
            
            # NEW TASK 1: if the "paid" col (J) isn't empty mark "Payment Complete"
            # Check if there's payment data in the paid column and auto-update payment_complete
            if sheets_service:
                try:
                    sheet_data = sheets_service.get_sheet_data()  
                    if sheet_data:
                        headers = sheet_data['headers']
                        rows = sheet_data['rows']
                        column_indices = sheets_service.get_column_indices(headers) 
                        
                        submission_id_col = column_indices.get('submission_id')
                        paid_col = column_indices.get('paid')
                        
                        if submission_id_col is not None and paid_col is not None:
                            # Find the current user's row
                            for row in rows:
                                if (len(row) > submission_id_col and 
                                    row[submission_id_col] == submission_id and
                                    len(row) > paid_col):
                                    
                                    paid_col_value = row[paid_col].strip() if row[paid_col] else ''
                                    
                                    if paid_col_value and not status_data.get('paid', False):
                                        print(f"✅ Found payment data in paid column for {status_data['alias']}: '{paid_col_value}' - auto-updating payment_complete to TRUE")
                                        update_payment_complete(submission_id, True)
                                        break
                except Exception as e:
                    print(f"❌ Error checking paid column: {e}")
            
            # Send welcome message
            await update.message.reply_text(
                get_message(status_data['language'], 'welcome', name=status_data['alias'])
            )
            
            # TASK: chat continues - keep the conversation going after /start
            # Guide user to their next step instead of letting conversation fade
            await continue_conversation(update, context, status_data)
            
            # Check if user is now ready for review and notify admins
            await check_and_notify_ready_for_review(status_data)
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
        status_data = await get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = await get_status_data(telegram_user_id=user_id)
    
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
        status_data = await get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = await get_status_data(telegram_user_id=user_id)
    
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
            parallel_tasks.append("💬 השתמש ב-/get_to_know כדי להשלים את חלק ההיכרות.")
        else:
            parallel_tasks.append("💬 Use /get_to_know to complete the get-to-know section.")
    
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
        status_data = await get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = await get_status_data(telegram_user_id=user_id)
    
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
        status_data = await get_status_data(submission_id=submission_id)
    
    if not status_data:
        # Try to find by Telegram User ID in the sheet
        status_data = await get_status_data(telegram_user_id=user_id)
    
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

# --- Admin Commands ---
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin dashboard with registration statistics"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    if not sheets_service:
        await update.message.reply_text("❌ Google Sheets not available. Cannot access registration data.")
        return
    
    try:
        sheet_data = sheets_service.get_sheet_data()    
        if not sheet_data:
            await update.message.reply_text("❌ No registration data found.")
            return
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = sheets_service.get_column_indices(headers) 
        
        # Calculate statistics
        stats = {
            'total': 0,
            'ready_for_review': 0,
            'approved': 0,
            'paid': 0,
            'partner_pending': 0,
            'cancelled': 0
        }
        
        pending_approvals = []
        
        for row in rows:
            if len(row) <= column_indices.get('submission_id', 0):
                continue
                
            submission_id = row[column_indices.get('submission_id', 0)]
            if not submission_id:
                continue
                
            stats['total'] += 1
            status_data = parse_submission_row(row, column_indices)
            
            # Count by status
            if status_data.get('cancelled', False):
                stats['cancelled'] += 1
            elif not status_data.get('partner', False):
                stats['partner_pending'] += 1
            elif status_data.get('form', False) and status_data.get('partner', False) and status_data.get('get_to_know', False) and not status_data.get('approved', False):
                stats['ready_for_review'] += 1
                pending_approvals.append({
                    'name': status_data.get('alias', 'Unknown'),
                    'submission_id': submission_id,
                    'partner': status_data.get('partner_alias', 'Solo')
                })
            elif status_data.get('approved', False) and status_data.get('paid', False):
                stats['paid'] += 1
            elif status_data.get('approved', False):
                stats['approved'] += 1
        
        # Create dashboard message
        message = (
            f"🔧 **Admin Dashboard**\n\n"
            f"**Registration Statistics:**\n"
            f"• Total: {stats['total']}\n"
            f"• Ready for Review: {stats['ready_for_review']}\n"
            f"• Approved: {stats['approved']}\n"
            f"• Paid: {stats['paid']}\n"
            f"• Partner Pending: {stats['partner_pending']}\n"
            f"• Cancelled: {stats['cancelled']}\n\n"
        )
        
        if pending_approvals:
            message += f"**Pending Approvals ({len(pending_approvals)}):**\n"
            for approval in pending_approvals[:10]:  # Show first 10
                partner_info = f" + {approval['partner']}" if approval['partner'] != 'Solo' else ""
                message += f"• {approval['name']}{partner_info} (`{approval['submission_id']}`)\n"
            
            if len(pending_approvals) > 10:
                message += f"• ... and {len(pending_approvals) - 10} more\n"
        
        message += f"\n**Available Commands:**\n"
        message += f"• `/admin_approve SUBM_ID` - Approve registration\n"
        message += f"• `/admin_reject SUBM_ID` - Reject registration\n"
        message += f"• `/admin_status SUBM_ID` - Check registration status\n"
        message += f"• `/admin_digest` - Generate weekly digest\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating dashboard: {e}")

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a registration (admin only)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/admin_approve SUBM_12345`")
        return
    
    submission_id = context.args[0]
    
    # Update the admin approved status
    success = update_admin_approved(submission_id, True)
    
    if success:
        # Get user data to send notification
        status_data = await get_status_data(submission_id=submission_id) 
        if status_data and status_data.get('telegram_user_id'):
            try:
                user_language = status_data.get('language', 'en')
                if user_language == 'he':
                    user_message = f"🎉 הרשמתך אושרה!\n\nמזהה הגשה: {submission_id}\n\nהצעד הבא: השלמת התשלום."
                else:
                    user_message = f"🎉 Your registration has been approved!\n\nSubmission ID: {submission_id}\n\nNext step: Complete payment."
                
                await context.bot.send_message(
                    chat_id=status_data['telegram_user_id'],
                    text=user_message
                )
            except Exception as e:
                print(f"❌ Failed to notify user about approval: {e}")
        
        await update.message.reply_text(f"✅ Registration {submission_id} approved successfully!")
        
        # Notify other admins
        admin_name = update.effective_user.first_name or "Admin"
        await notify_admins(
            f"✅ Registration approved by {admin_name}\n\n"
            f"**Submission ID:** {submission_id}\n"
            f"**User:** {status_data.get('alias', 'Unknown') if status_data else 'Unknown'}",
            "status_changes"
        )
    else:
        await update.message.reply_text(f"❌ Failed to approve registration {submission_id}. Please check the submission ID.")

async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject a registration (admin only)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/admin_reject SUBM_12345 [reason]`")
        return
    
    submission_id = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    
    # Update the admin approved status to false
    success = update_admin_approved(submission_id, False)
    
    if success:
        # Get user data to send notification
        status_data = await get_status_data(submission_id=submission_id) 
        if status_data and status_data.get('telegram_user_id'):
            try:
                user_language = status_data.get('language', 'en')
                if user_language == 'he':
                    user_message = f"❌ הרשמתך נדחתה\n\nמזהה הגשה: {submission_id}\n\nסיבה: {reason}\n\nאתה מוזמן לנסות שוב באירוע הבא."
                else:
                    user_message = f"❌ Your registration has been rejected\n\nSubmission ID: {submission_id}\n\nReason: {reason}\n\nYou're welcome to try again for the next event."
                
                await context.bot.send_message(
                    chat_id=status_data['telegram_user_id'],
                    text=user_message
                )
            except Exception as e:
                print(f"❌ Failed to notify user about rejection: {e}")
        
        await update.message.reply_text(f"✅ Registration {submission_id} rejected successfully!")
        
        # Notify other admins
        admin_name = update.effective_user.first_name or "Admin"
        await notify_admins(
            f"❌ Registration rejected by {admin_name}\n\n"
            f"**Submission ID:** {submission_id}\n"
            f"**User:** {status_data.get('alias', 'Unknown') if status_data else 'Unknown'}\n"
            f"**Reason:** {reason}",
            "status_changes"
        )
    else:
        await update.message.reply_text(f"❌ Failed to reject registration {submission_id}. Please check the submission ID.")

async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check detailed status of a registration (admin only)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/admin_status SUBM_12345`")
        return
    
    submission_id = context.args[0]
    status_data = await get_status_data(submission_id=submission_id) 
    
    if not status_data:
        await update.message.reply_text(f"❌ Registration {submission_id} not found.")
        return
    
    # Create detailed status message
    partner_info = ""
    if status_data.get('partner_names'):
        partner_status = status_data.get('partner_status', {})
        registered_partners = partner_status.get('registered_partners', [])
        missing_partners = partner_status.get('missing_partners', [])
        
        if registered_partners:
            partner_info += f"**Registered Partners:** {', '.join(registered_partners)}\n"
        if missing_partners:
            partner_info += f"**Missing Partners:** {', '.join(missing_partners)}\n"
    elif status_data.get('partner_alias'):
        partner_info = f"**Partner:** {status_data['partner_alias']}\n"
    else:
        partner_info = "**Partner:** Coming alone\n"
    
    message = (
        f"📋 **Registration Status: {submission_id}**\n\n"
        f"**Name:** {status_data.get('alias', 'Unknown')}\n"
        f"**Language:** {status_data.get('language', 'Unknown')}\n"
        f"**Telegram ID:** {status_data.get('telegram_user_id', 'Not linked')}\n\n"
        f"{partner_info}\n"
        f"**Progress:**\n"
        f"• Form: {'✅' if status_data.get('form', False) else '❌'}\n"
        f"• Partner: {'✅' if status_data.get('partner', False) else '❌'}\n"
        f"• Get-to-know: {'✅' if status_data.get('get_to_know', False) else '❌'}\n"
        f"• Approved: {'✅' if status_data.get('approved', False) else '❌'}\n"
        f"• Paid: {'✅' if status_data.get('paid', False) else '❌'}\n"
        f"• Group: {'✅' if status_data.get('group_open', False) else '❌'}\n\n"
        f"**Returning Participant:** {'Yes' if status_data.get('is_returning_participant', False) else 'No'}\n"
        f"**Cancelled:** {'Yes' if status_data.get('cancelled', False) else 'No'}"
    )
    
    await update.message.reply_text(message)

async def admin_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send weekly admin digest manually"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    await update.message.reply_text("📊 Generating weekly digest...")
    await send_weekly_admin_digest()
    await update.message.reply_text("✅ Weekly digest sent to all admins!")

async def send_weekly_admin_digest():
    """Send weekly digest of registration statuses to admins"""
    if not sheets_service:
        print("⚠️  Cannot send weekly digest - Google Sheets not available")
        return
    
    try:
        sheet_data = sheets_service.get_sheet_data()
        if not sheet_data:
            return
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = sheets_service.get_column_indices(headers)
        
        # Count registrations by status
        stats = {
            'total': 0,
            'pending_approval': 0,
            'approved': 0,
            'paid': 0,
            'partner_pending': 0,
            'cancelled': 0
        }
        
        recent_registrations = []
        
        for row in rows:
            if len(row) <= column_indices.get('submission_id', 0):
                continue
                
            submission_id = row[column_indices.get('submission_id', 0)]
            if not submission_id:
                continue
                
            stats['total'] += 1
            
            # Parse status
            status_data = parse_submission_row(row, column_indices)
            
            # Count by status
            if status_data.get('cancelled', False):
                stats['cancelled'] += 1
            elif not status_data.get('partner', False):
                stats['partner_pending'] += 1
            elif status_data.get('approved', False) and status_data.get('paid', False):
                stats['paid'] += 1
            elif status_data.get('approved', False):
                stats['approved'] += 1
            elif status_data.get('form', False) and status_data.get('partner', False) and status_data.get('get_to_know', False):
                stats['pending_approval'] += 1
            
            # Add to recent registrations (last 7 days would require timestamp comparison)
            recent_registrations.append({
                'name': status_data.get('alias', 'Unknown'),
                'submission_id': submission_id,
                'status': 'Ready for Review' if (status_data.get('form', False) and status_data.get('partner', False) and status_data.get('get_to_know', False) and not status_data.get('approved', False)) else 'In Progress'
            })
        
        # Create digest message
        message = (
            f"📊 **Weekly Registration Digest**\n\n"
            f"**Total Registrations:** {stats['total']}\n"
            f"**Pending Approval:** {stats['pending_approval']}\n"
            f"**Approved:** {stats['approved']}\n"
            f"**Paid:** {stats['paid']}\n"
            f"**Partner Pending:** {stats['partner_pending']}\n"
            f"**Cancelled:** {stats['cancelled']}\n\n"
        )
        
        if stats['pending_approval'] > 0:
            message += f"⚠️  **{stats['pending_approval']} registrations need your review!**\n\n"
        
        if recent_registrations[:5]:  # Show first 5
            message += "**Recent Activity:**\n"
            for reg in recent_registrations[:5]:
                message += f"• {reg['name']} ({reg['submission_id']}) - {reg['status']}\n"
        
        await notify_admins(message, "weekly_digest")
        
    except Exception as e:
        print(f"❌ Error generating weekly digest: {e}")

# --- Automatic Reminder System ---
class ReminderScheduler:
    """Handles automatic reminders based on time and user state"""
    
    def __init__(self, bot_application):
        self.bot = bot_application
        self.reminder_intervals = {
            'partner_pending': 24 * 60 * 60,  # 24 hours in seconds
            'payment_pending': 3 * 24 * 60 * 60,  # 3 days
            'group_opening': 7 * 24 * 60 * 60,  # 7 days before event
            'event_reminder': 24 * 60 * 60,  # 1 day before event
            'weekly_digest': 7 * 24 * 60 * 60,  # 7 days
        }
        self.last_reminder_check = {}
        self.last_weekly_digest = None
        
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
        sheet_data = sheets_service.get_sheet_data() 
        if not sheet_data:
            print("⚠️  No sheet data available for reminder checking")
            return
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = sheets_service.get_column_indices(headers)
        
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
        
        # Check if it's time for weekly digest
        await self.check_weekly_digest()
    
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
        
        # Also notify admins about the partner delay
        await notify_partner_delay(
            submission_id=user_data.get('submission_id', 'Unknown'),
            user_name=user_data.get('alias', 'Unknown'),
            missing_partners=missing_partners
        )
    
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
        
        # Calculate days since approval (simplified - in reality you'd track approval timestamp)
        days_overdue = 3  # Simplified - this would be calculated from actual approval date
        
        # Notify admins about payment overdue
        await notify_payment_overdue(
            submission_id=user_data.get('submission_id', 'Unknown'),
            user_name=user_data.get('alias', 'Unknown'),
            days_overdue=days_overdue
        )
    
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
    
    async def check_weekly_digest(self):
        """Check if it's time to send weekly digest to admins"""
        now = datetime.now()
        
        # Check if it's time for weekly digest (every 7 days)
        if self.last_weekly_digest:
            time_since_last = (now - self.last_weekly_digest).total_seconds()
            if time_since_last < self.reminder_intervals['weekly_digest']:
                return  # Too soon for another digest
        
        # Send weekly digest
        print("📊 Sending weekly admin digest...")
        await send_weekly_admin_digest()
        self.last_weekly_digest = now
    
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

# --- Get-to-Know Flow Implementation ---

# Simple Hebrew get-to-know questions
GET_TO_KNOW_QUESTIONS = {
    'he': {
        'first_question': "אשמח לשמוע עליך קצת.\nקצת מי אתה, קצת על הניסיון שלך עם אירועים מהסוג הזה, קצת משהו מגניב עליך 😃",
        'followup_question': "אשמח לשמוע משהו מגניב ומעניין עליך. לא חובה (ואף רצוי) לא מתוך העולם האלטרנטיבי.",
        'completion_message': "🎉 תודה על השיתוף! תשובתך נשמרה, מנהלת הליין תעבור עליה בהקדם ונחזיר לך תשובה בהקדם.",
        'already_completed': "✅ כבר השלמת את חלק ההיכרות!",
        'no_registration': "אנא קשר את ההרשמה שלך קודם עם /start"
    },
    'en': {
        'first_question': "I'd love to hear about you a bit.\nA bit about who you are, your experience with these types of events, something cool about you 😃",
        'followup_question': "I'd love to hear something cool and interesting about you. Not required (and preferably not) from the alternative world.",
        'completion_message': "🎉 Thanks for sharing! This helps us create a safe and comfortable environment for everyone.",
        'already_completed': "✅ You've already completed the get-to-know section!",
        'no_registration': "Please link your registration first with /start"
    }
}

# Boring answer detection patterns - improved based on real examples
BORING_PATTERNS = [
    # Hebrew filler words and phrases
    'אמממ', 'האמת שאין לי מושג', 'לא יודע', 'לא יודעת', 'אין לי מושג', 
    'לא הכי טובה בלכתוב', 'לא כל כך יודע', 'מה לכתוב', 'אהמ', 'בסדר',
    'אין לי', 'רגיל', 'רגילה', 'כלום', 'לא יודע מה לכתוב',
    'נסיון מועט', 'לא יותר מידי', 'בייבי בהכל',
    # English patterns - more specific to avoid false positives
    'idk', "i don't know", 'regular', 'normal', 'nothing', 'boring', 'dunno',
    'not sure', 'whatever', 'meh', 'dunno what to write', 'dont know'
]

# Strong boring indicators (if present, very likely boring)
STRONG_BORING_INDICATORS = [
    'אמממ', 'האמת שאין לי מושג', 'אין לי מושג', 'לא יודע מה לכתוב'
]

# Indicators of good answers (if present, less likely to be boring)
GOOD_ANSWER_INDICATORS = [
    # Specific details and experiences - but avoid negative contexts
    'אוהב', 'אוהבת', 'מעניין', 'מעניינת', 'תחביב', 'עובד', 'עובדת', 
    'לומד', 'לומדת', 'מנגן', 'שר',
    # Personality traits
    'אנרגיות', 'ידידותי', 'חייכן', 'שובב', 'אהבה', 'תחום',
    # Specific activities or interests
    'מוזיקה', 'ספורט', 'אמנות', 'טבע', 'נסיעות', 'קריאה',
    'גיטרה', 'רקוד', 'טיול', 'צניחה', 'קוקטיל', 'אקסטרים',
    'פסטיבל', 'אגרונומית', 'לאונרד כהן', 'קילימנג\'רו', 'טאקוונדו',
    'פסיכותרפיה', 'שיבארי', 'שפות', 'בלשנות', 'עצלן', 'שלט',
    # Professional/educational details
    'מעצב', 'מאמן', 'מאמנת', 'מתורגמן', 'מתורגמנת', 'הייטק',
    'חינוך', 'שיקום', 'עיסוי', 'אינטגרטיבי'
]

# Negative contexts that negate good indicators
NEGATIVE_CONTEXTS = [
    'אין לי מושג למשהו מגניב',
    'לא יודע משהו מגניב',
    'אין לי ניסיון',
    'לא יודע מה',
    'נסיון מועט'
]

# Store conversation states
user_conversation_states = {}

def is_boring_answer(answer: str) -> bool:
    """
    Improved boring answer detection based on real examples
    
    Criteria for boring answers:
    1. Very short answers
    2. Strong boring indicators (immediate red flags)
    3. Many filler words without substance
    4. Lacks specific details or personality
    """
    if not answer or len(answer.strip()) < 3:
        return True
    
    answer_lower = answer.lower().strip()
    original_answer = answer.strip()
    
    # Hebrew detection (contains Hebrew characters)
    has_hebrew = any('\u0590' <= char <= '\u05FF' for char in answer)
    
    # 1. Too short for meaningful content
    min_length = 30 if has_hebrew else 20
    if len(answer_lower) < min_length:
        return True
    
    # 2. Check for strong boring indicators (immediate red flags)
    strong_boring_count = 0
    for strong_indicator in STRONG_BORING_INDICATORS:
        if strong_indicator in answer_lower:
            strong_boring_count += 1
    
    # If has strong boring indicators, check if there's enough substance to override
    if strong_boring_count > 0:
        # Count good indicators
        good_indicators = 0
        for indicator in GOOD_ANSWER_INDICATORS:
            if indicator in answer_lower:
                good_indicators += 1
        
        # Check for negative contexts that negate good indicators
        negative_context_count = 0
        for negative_context in NEGATIVE_CONTEXTS:
            if negative_context in answer_lower:
                negative_context_count += 1
        
        # Reduce good indicators if there are negative contexts
        if negative_context_count > 0:
            good_indicators = max(0, good_indicators - negative_context_count)
        
        # If strong boring indicators but good substance, not boring
        # More lenient for shorter answers with really good content
        if good_indicators >= 2 and len(answer_lower) > 50:
            return False
        elif good_indicators >= 1 and len(answer_lower) > 40 and any(excellent in answer_lower for excellent in ['צניחה', 'אקסטרים', 'קילימנג\'רו', 'לאונרד כהן']):
            return False
        # Otherwise, if strong boring indicators, it's boring
        else:
            return True
    
    # 3. Count regular filler words/phrases
    filler_count = 0
    for pattern in BORING_PATTERNS:
        if pattern in answer_lower:
            filler_count += 1
    
    # 4. Count good indicators, but check for negative contexts
    good_indicators = 0
    for indicator in GOOD_ANSWER_INDICATORS:
        if indicator in answer_lower:
            good_indicators += 1
    
    # Check for negative contexts that negate good indicators
    negative_context_count = 0
    for negative_context in NEGATIVE_CONTEXTS:
        if negative_context in answer_lower:
            negative_context_count += 1
    
    # Reduce good indicators if there are negative contexts
    if negative_context_count > 0:
        good_indicators = max(0, good_indicators - negative_context_count)
    
    # 5. Calculate word count
    words = answer_lower.split()
    word_count = len(words)
    
    # Decision logic based on examples analysis:
    
    # If good indicators present and reasonable length, probably not boring
    if good_indicators >= 2 and word_count >= 15:
        return False
    
    # If multiple filler words and no good indicators = boring
    if filler_count >= 2 and good_indicators == 0:
        return True
    
    # If short answer with filler words and no substance = boring
    if filler_count >= 1 and word_count < 25 and good_indicators == 0:
        return True
    
    # Special case: answers that are just demographics without personality
    # (like "בת 22 מכפר סבא, סטודנטית" without more detail)
    if (word_count < 15 and 
        any(demo in answer_lower for demo in ['בת ', 'בן ', 'מ', 'גר ב', 'גרה ב']) and
        good_indicators == 0):
        return True
    
    # If very short and no good indicators = boring
    if word_count < 20 and good_indicators == 0:
        return True
    
    # Special case: even with some good indicators, if it's very generic/short and has filler words
    if word_count < 25 and filler_count >= 1 and good_indicators <= 1:
        return True
    
    return False

async def get_to_know_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the get-to-know conversation flow"""
    user_id = str(update.effective_user.id)
    
    # Get user's submission data
    submission_id = user_submissions.get(user_id)
    if not submission_id:
        # Try to find by Telegram User ID
        status_data = await get_status_data(telegram_user_id=user_id)
        if status_data:
            submission_id = status_data.get('submission_id')
            user_submissions[user_id] = submission_id
    
    if not submission_id:
        await update.message.reply_text("אנא קשר את ההרשמה שלך קודם עם /start")
        return
    
    status_data = await get_status_data(submission_id=submission_id)
    if not status_data:
        await update.message.reply_text("לא הצלחתי למצוא את ההרשמה שלך.")
        return
    
    # Check if already completed
    if status_data.get('get_to_know', False):
        language = status_data.get('language', 'he')
        await update.message.reply_text(GET_TO_KNOW_QUESTIONS[language]['already_completed'])
        return
    
    # Start the conversation flow
    language = status_data.get('language', 'he')
    user_conversation_states[user_id] = {
        'flow': 'get_to_know',
        'step': 'first_question',
        'language': language,
        'submission_id': submission_id,
        'responses': {}
    }
    
    # Ask first question
    await update.message.reply_text(GET_TO_KNOW_QUESTIONS[language]['first_question'])

async def handle_get_to_know_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user responses during get-to-know flow"""
    user_id = str(update.effective_user.id)
    state = user_conversation_states.get(user_id)
    
    if not state or state.get('flow') != 'get_to_know':
        return  # Not in get-to-know flow
    
    response = update.message.text.strip()
    current_step = state['step']
    language = state['language']
    
    if current_step == 'first_question':
        # Store the first response
        state['responses']['first_answer'] = response
        
        # Check if response is boring
        if is_boring_answer(response):
            # Ask follow-up question
            state['step'] = 'followup_question'
            await update.message.reply_text(GET_TO_KNOW_QUESTIONS[language]['followup_question'])
        else:
            # Good answer, complete the flow
            await complete_get_to_know_flow(update, user_id)
    
    elif current_step == 'followup_question':
        # Store the follow-up response
        state['responses']['followup_answer'] = response
        
        # Complete the flow regardless of answer quality
        await complete_get_to_know_flow(update, user_id)

async def complete_get_to_know_flow(update: Update, user_id: str):
    """Complete the get-to-know flow and store responses"""
    state = user_conversation_states.get(user_id)
    if not state:
        return
    
    submission_id = state['submission_id']
    responses = state['responses']
    language = state['language']
    
    # Combine responses for storage
    combined_response = ""
    if 'first_answer' in responses:
        combined_response += responses['first_answer']
    if 'followup_answer' in responses:
        if combined_response:
            combined_response += "\n\n[Follow-up]: "
        combined_response += responses['followup_answer']
    
    # Store response in Google Sheets
    success = store_get_to_know_response(submission_id, combined_response)
    
    if success:
        # Mark as complete
        update_get_to_know_complete(submission_id, True)
        
        # Send completion message
        await update.message.reply_text(GET_TO_KNOW_QUESTIONS[language]['completion_message'])
        
        # Continue with next steps
        status_data = await get_status_data(submission_id=submission_id)
        if status_data:
            await continue_conversation(update, None, status_data)
    else:
        # Error message
        if language == 'he':
            await update.message.reply_text("❌ שגיאה בשמירת התשובות. אנא נסה שוב.")
        else:
            await update.message.reply_text("❌ Error saving responses. Please try again.")
    
    # Clean up state
    if user_id in user_conversation_states:
        del user_conversation_states[user_id]

def store_get_to_know_response(submission_id: str, response: str):
    """Store get-to-know response in Google Sheets"""
    if not sheets_service:
        print("⚠️  Google Sheets not available - cannot store get-to-know response")
        return False
    
    try:
        # Get current data to find the row
        sheet_data = sheets_service.get_sheet_data() 
        if not sheet_data:
            return False
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        # Find column indices
        column_indices = sheets_service.get_column_indices(headers)
        
        submission_id_col = column_indices.get('submission_id')
        if submission_id_col is None:
            print("❌ Could not find submission_id column")
            return False
        
        # Look for get-to-know response column (we'll add this to the sheets)
        get_to_know_response_col = None
        for i, header in enumerate(headers):
            if 'Get To Know Response' in header or 'תשובת היכרות' in header:
                get_to_know_response_col = i
                break
        
        if get_to_know_response_col is None:
            print("⚠️  Get-to-know response column not found in Google Sheets")
            return False
        
        # Find the row with the matching submission ID
        for row_index, row in enumerate(rows):
            if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                # Found the row! Update the response
                sheet_row = row_index + 4  # Adjust for header row and 0-based indexing
                
                # Convert column index to letter
                col_letter = sheets_service.column_index_to_letter(get_to_know_response_col)
                range_name = f"managed!{col_letter}{sheet_row}"
                
                # Update the cell
                result = sheets_service.update_range(range_name, response)
                
                print(f"✅ Stored get-to-know response for submission {submission_id}")
                return True
        
        print(f"❌ Could not find submission {submission_id} in Google Sheets")
        return False
        
    except Exception as e:
        print(f"❌ Error storing get-to-know response: {e}")
        return False

# --- End of Get-to-Know Flow Implementation ---

# --- Main runner ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("remind_partner", remind_partner))
    app.add_handler(CommandHandler("cancel", cancel_registration))
    app.add_handler(CommandHandler("get_to_know", get_to_know_command))
    
    # Admin commands
    app.add_handler(CommandHandler("admin_dashboard", admin_dashboard))
    app.add_handler(CommandHandler("admin_approve", admin_approve))
    app.add_handler(CommandHandler("admin_reject", admin_reject))
    app.add_handler(CommandHandler("admin_status", admin_status))
    app.add_handler(CommandHandler("admin_digest", admin_digest))
    
    # Message handlers (must be after command handlers)
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_get_to_know_response))

    # NEW TASK 2: telegram bot command autocomplete
    # Set up command autocomplete for better user experience
    async def setup_bot_commands():
        """Set up bot command autocomplete"""
        commands = [
            BotCommand("start", "Link your registration or get welcome message"),
            BotCommand("status", "Check your registration progress"),
            BotCommand("help", "Show help and available commands"),
            BotCommand("cancel", "Cancel your registration with reason"),
            BotCommand("remind_partner", "Send reminder to partner(s)"),
            BotCommand("get_to_know", "Complete the get-to-know section"),
        ]
        
        try:
            await app.bot.set_my_commands(commands)
            print("✅ Bot command autocomplete set up successfully")
        except Exception as e:
            print(f"❌ Error setting up bot commands: {e}")
    
    # NEW TASK 3: Define Sheet1 monitoring functions before they are used
    
    def get_managed_sheet_data():
        """Fetch data from managed sheet"""
        return sheets_service.get_sheet_data()  # This already reads from managed sheet

    def duplicate_to_managed_sheet(row_data, sheet1_headers):
        """Duplicate a row from Sheet1 to the managed sheet"""
        if not sheets_service:
            print("⚠️  Google Sheets not available - cannot duplicate data")
            return False
        
        try:
            # Get current managed sheet data to find the next empty row
            managed_data = get_managed_sheet_data()
            if not managed_data:
                print("❌ Could not access managed sheet")
                return False
            
            # Find the next empty row in managed sheet
            next_row = len(managed_data['rows']) + 4  # +4 for header and starting from row 3
            
            # Prepare the row data for insertion
            # Map Sheet1 columns to managed sheet columns
            # mapped_row = map_sheet1_to_managed(row_data, sheet1_headers)
            
            # Insert the row
            range_name = f"managed!M{next_row}:ZZ{next_row}"
            
            result = sheets_service.update_range(range_name, row_data)
            
            print(f"✅ Duplicated new registration to managed sheet at row {next_row}")
            return True
            
        except Exception as e:
            print(f"❌ Error duplicating to managed sheet: {e}")
            return False

    def map_sheet1_to_managed(row_data, sheet1_headers):
        """Map Sheet1 row data to managed sheet format"""
        # This function maps the columns from Sheet1 to the expected managed sheet format
        # You'll need to adjust this based on your actual Sheet1 structure
        
        managed_row = [''] * 30  # Initialize with empty values
        
        # Map common fields (adjust indices based on your actual sheets)
        for i, header in enumerate(sheet1_headers):
            if i < len(row_data):
                value = row_data[i]
                
                # Map specific columns to managed sheet positions
                if 'Submission ID' in header:
                    managed_row[0] = value  # Submission ID in column A
                elif 'שם מלא' in header:
                    managed_row[1] = value  # Full name in column B
                elif 'שם הפרטנר' in header:
                    managed_row[2] = value  # Partner name in column C
                elif 'האם תרצו להמשיך בעברית או באנגלית' in header:
                    managed_row[3] = value  # Language preference
                elif 'האם השתתפת בעבר באחד מאירועי Wild Ginger' in header:
                    managed_row[4] = value  # Returning participant
                # Add more mappings as needed
                
        return managed_row

    def check_for_new_registrations():
        """Check Sheet1 for new entries and duplicate them to managed"""
        print("🔍 Checking for new registrations in Sheet1...")
        
        # Get Sheet1 data
        sheet1_data = sheets_service.get_sheet1_data()
        if not sheet1_data:
            print("⚠️  Could not access Sheet1")
            return
        
        # Get managed sheet data
        managed_data = get_managed_sheet_data()
        if not managed_data:
            print("⚠️  Could not access managed sheet")
            return
        
        # Find submission IDs that exist in managed sheet
        managed_submission_ids = set()
        managed_headers = managed_data['headers']
        managed_column_indices = sheets_service.get_column_indices(managed_headers)
        submission_id_col = managed_column_indices.get('submission_id')
        
        if submission_id_col is not None:
            for row in managed_data['rows']:
                if len(row) > submission_id_col and row[submission_id_col]:
                    managed_submission_ids.add(row[submission_id_col])
        
        # Check Sheet1 for new entries
        sheet1_headers = sheet1_data['headers']
        sheet1_submission_col = None
        
        # Find submission ID column in Sheet1
        for i, header in enumerate(sheet1_headers):
            if 'Submission ID' in header:
                sheet1_submission_col = i
                break
        
        if sheet1_submission_col is None:
            print("❌ Could not find Submission ID column in Sheet1")
            return
        
        # Check each row in Sheet1
        new_registrations = []
        for row in sheet1_data['rows']:
            if len(row) > sheet1_submission_col and row[sheet1_submission_col]:
                submission_id = row[sheet1_submission_col]
                
                # If this submission ID is not in managed sheet, it's new
                if submission_id not in managed_submission_ids:
                    new_registrations.append((submission_id, row))
        
        # Process new registrations
        if new_registrations:
            print(f"📝 Found {len(new_registrations)} new registrations")
            
            for submission_id, row_data in new_registrations:
                # Duplicate to managed sheet
                if duplicate_to_managed_sheet(row_data, sheet1_headers):
                    # Notify admin about new registration
                    asyncio.create_task(notify_admin_new_registration(submission_id, row_data, sheet1_headers))
        else:
            print("✅ No new registrations found")

    async def notify_admin_new_registration(submission_id, row_data, sheet1_headers):
        """Notify admin about new registration"""
        # Extract name from row data
        name = extract_name(row_data, sheet1_headers)
                
        # Create notification message
        message = (
            f"🆕 **New Registration Alert**\n\n"
            f"**Name:** {name}\n"
            f"**Submission ID:** {submission_id}\n"
            f"**Status:** Automatically copied to managed sheet\n\n"
            f"Please review and process this registration."
        )
        
        # Send notification to each admin
        await notify_admins(message, 'new_registration')
    
    # Extract name from row data
    def extract_name(row_data, sheet1_headers):
        name = "Unknown"
        for i, header in enumerate(sheet1_headers):
            if 'שם מלא' in header and i < len(row_data):
                name = row_data[i]
                break
        return name
    
    # NEW TASK 3: Set up periodic monitoring for Sheet1 -> managed duplication
    async def periodic_sheet_monitoring():
        """Periodically check Sheet1 for new entries"""
        while True:
            try:
                check_for_new_registrations()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"❌ Error in periodic monitoring: {e}")
                await asyncio.sleep(300)  # Continue checking even if there's an error
    
    # Post-init hook to start background tasks
    async def post_init(application):
        """Initialize background tasks after bot starts"""
        # Set up command autocomplete
        await setup_bot_commands()
        
        # Start periodic monitoring if sheets service is available
        if sheets_service:
            import asyncio
            asyncio.create_task(periodic_sheet_monitoring())
            print("✅ Sheet1 monitoring started - checking every 5 minutes")
        else:
            print("⚠️  Sheet1 monitoring disabled - Google Sheets not available")
    
    # Set the post_init hook
    app.post_init = post_init
    
    print("Bot is running with polling...")
    
    try:
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
