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
GOOGLE_SHEETS_RANGE = os.getenv("GOOGLE_SHEETS_RANGE", "managed!A3:Z1000")  # Start from row 3 (headers)

# Initialize Google Sheets service
sheets_service = None
if GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID:
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
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

def find_submission_by_id(submission_id: str):
    """Find a submission by its ID in the Google Sheets"""
    sheet_data = get_sheet_data()
    if not sheet_data:
        return None
    
    headers = sheet_data['headers']
    rows = sheet_data['rows']
    
    # Find the column indices for our important fields
    column_indices = {}
    for i, header in enumerate(headers):
        if 'Submission ID' in header and 'time' not in header.lower():
            column_indices['submission_id'] = i
        elif 'Status' in header or 'status' in header.lower():
            column_indices['status'] = i
        elif 'שם מלא' in header or 'name' in header.lower():  # Full name in Hebrew or English
            column_indices['full_name'] = i
        elif 'מגיע.ה לבד או באיזון' in header:  # Coming alone or in balance
            column_indices['coming_alone_or_balance'] = i
        elif 'שם הפרטנר' in header:  # Partner name in Hebrew
            column_indices['partner_name'] = i
    
    # Look for the submission ID in the rows
    for row in rows:
        if len(row) > column_indices.get('submission_id', 0):
            if row[column_indices['submission_id']] == submission_id:
                return parse_submission_row(row, column_indices)
    
    return None

def parse_submission_row(row, column_indices):
    """Parse a row from the sheet into our status format"""
    def get_cell_value(key, default=""):
        index = column_indices.get(key)
        if index is not None and index < len(row):
            return row[index]
        return default
    
    # Get basic info
    submission_id = get_cell_value('submission_id')
    status = get_cell_value('status', '').lower()
    full_name = get_cell_value('full_name')
    coming_alone_or_balance = get_cell_value('coming_alone_or_balance')
    partner_name = get_cell_value('partner_name')
    
    # Determine if they have a partner
    has_partner = coming_alone_or_balance != 'לבד' and partner_name  # 'לבד' means 'alone' in Hebrew
    
    # Parse status into our flow steps
    form_complete = submission_id != ""  # If there's a submission ID, form is complete
    partner_complete = has_partner and partner_name != ""
    get_to_know_complete = True  # Assume this is complete if form is submitted
    approved = 'approved' in status or 'מאושר' in status
    paid = 'paid' in status or 'שולם' in status
    group_open = 'group' in status or 'קבוצה' in status
    
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
        "raw_status": status
    }

# --- Get status data (Google Sheets or mock) ---
def get_status_data(submission_id: str = None):
    """Get status data from Google Sheets or fallback to mock data"""
    if sheets_service and submission_id:
        # Try to get real data from Google Sheets
        sheet_data = find_submission_by_id(submission_id)
        if sheet_data:
            return sheet_data
    
    # Fallback to mock data with specific names
    mock_data = {
        "7b64f54f-afe8-4f28-a0a9-fb57d495e51e": {
            "submission_id": "7b64f54f-afe8-4f28-a0a9-fb57d495e51e",
            "alias": "אלעד ויסברוד",
            "form": True,
            "partner": True,
            "get_to_know": True,
            "approved": False,
            "paid": False,
            "group_open": False,
            "partner_alias": "ShadowBeast"
        },
        "481b2f14-8463-4e9b-8b9b-c4e955f3ab4c": {
            "submission_id": "481b2f14-8463-4e9b-8b9b-c4e955f3ab4c",
            "alias": "בילא מאלץ",
            "form": True,
            "partner": True,
            "get_to_know": True,
            "approved": False,
            "paid": False,
            "group_open": False,
            "partner_alias": "ShadowBeast"
        }
    }
    
    # Return specific mock data if available, otherwise default
    if submission_id and submission_id in mock_data:
        return mock_data[submission_id]
    
    return {
        "submission_id": submission_id or "SUBM_12345",
        "alias": "VelvetFox",
        "form": True,
        "partner": True,
        "get_to_know": True,
        "approved": False,
        "paid": False,
        "group_open": False,
        "partner_alias": "ShadowBeast"
    }

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
        status_data = get_status_data(submission_id)
        
        await update.message.reply_text(
            f"Hi {status_data['alias']}! 👋\n"
            f"I'm your registration assistant. You can check your status anytime with /status."
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
    
    # Get the submission ID for this user
    submission_id = user_submissions.get(user_id)
    
    if not submission_id:
        await update.message.reply_text(
            f"❌ No submission linked to your account.\n\n"
            f"To link your form submission, please use the link provided after filling out the registration form.\n"
            f"It should look like: `/start SUBM_12345`"
        )
        return
    
    # Get status data from Google Sheets or mock data
    status_data = get_status_data(submission_id)
    
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
        f"🆔 Submission ID: `{status_data['submission_id']}`"
    )
    
    # Add additional info if available from Google Sheets
    if 'coming_alone_or_balance' in status_data:
        message += f"\n👤 Registration: {status_data['coming_alone_or_balance']}"
    
    await update.message.reply_text(message)

# --- Main runner ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

    print("Bot is running with polling...")
    app.run_polling()
