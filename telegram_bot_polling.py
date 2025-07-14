from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# --- Bot token from environment variable ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required. Please set it in your .env file.")

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
    
    # Get basic info
    submission_id = get_cell_value('submission_id')
    full_name = get_cell_value('full_name')
    coming_alone_or_balance = get_cell_value('coming_alone_or_balance')
    partner_name = get_cell_value('partner_name')
    
    # Determine if they have a partner
    has_partner = coming_alone_or_balance != 'לבד' and partner_name  # 'לבד' means 'alone' in Hebrew
    
    # Parse status into our flow steps - no assumptions, use dedicated columns
    form_complete = get_boolean_value('form_complete', False)
    partner_complete = get_boolean_value('partner_complete', False)
    get_to_know_complete = get_boolean_value('get_to_know_complete', False)
    approved = get_boolean_value('admin_approved', False)
    paid = get_boolean_value('payment_complete', False)
    group_open = get_boolean_value('group_access', False)
    
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
        "coming_alone_or_balance": coming_alone_or_balance,
        "raw_status": get_cell_value('status', ''),  # Keep as fallback/reference
        "telegram_user_id": get_cell_value('telegram_user_id', '')
    }

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
            
            await update.message.reply_text(
                f"Hi {status_data['alias']}! 👋\n"
                f"I'm your registration assistant. You can check your status anytime with /status."
            )
        else:
            await update.message.reply_text(
                f"❌ Could not find submission {submission_id}.\n"
                f"Please check your submission ID and try again."
            )
    else:
        # No submission ID provided
        await update.message.reply_text(
            f"Hi {user.first_name or 'there'}! 👋\n"
            f"I'm your registration assistant.\n\n"
            f"To link your form submission, please use the link provided after filling out the registration form.\n"
            f"You can check your status anytime with /status."
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
        await update.message.reply_text(
            f"❌ No submission linked to your account.\n\n"
            f"To link your form submission, please use the link provided after filling out the registration form.\n"
            f"It should look like: `/start SUBM_12345`"
        )
        return
    
    # Build the status message
    partner_text = "❌"
    if status_data['partner']:
        if status_data['partner_alias']:
            partner_text = f"✅ ({status_data['partner_alias']})"
        else:
            partner_text = "✅"
    
    message = (
        f"📋 Form: {'✅' if status_data['form'] else '❌'}\n"
        f"🤝 Partner: {partner_text}\n"
        f"💬 Get-to-know: {'✅' if status_data['get_to_know'] else '❌'}\n"
        f"🛠️ Status: {'✅ Approved' if status_data['approved'] else '⏳ Waiting for review'}\n"
        f"💸 Payment: {'✅' if status_data['paid'] else '❌ Not yet paid'}\n"
        f"👥 Group: {'✅ Open' if status_data['group_open'] else '❌ Not open yet'}\n\n"
        # f"🆔 Submission ID: `{status_data['submission_id']}`"
    )
    
    # Add additional info if available from Google Sheets
    # if 'coming_alone_or_balance' in status_data:
    #     message += f"\n👤 Registration: {status_data['coming_alone_or_balance']}"
    
    await update.message.reply_text(message)

# --- Main runner ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

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
