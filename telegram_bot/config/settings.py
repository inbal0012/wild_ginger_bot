import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

class Settings:
    def __init__(self):
        # --- Telegram Bot Configuration ---
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # --- Admin Configuration ---
        self.admin_user_ids = self._load_admin_user_ids()
        self.admin_notifications = {
            'new_registrations': True,
            'partner_delays': True,
            'payment_overdue': True,
            'weekly_digest': True,
            'status_changes': True
        }
        
        # --- Google Sheets Configuration ---
        self.google_sheets_credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
        self.google_sheets_spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        self.google_sheets_range = os.getenv("GOOGLE_SHEETS_RANGE", "managed!A3:GG1000")
        
        # --- Initialize Google Sheets Service ---
        self.sheets_service = self._initialize_sheets_service()
        
        # --- Multilingual Messages ---
        self.messages = self._load_messages()
        
    def _load_admin_user_ids(self) -> List[int]:
        """Load admin user IDs from environment variables"""
        admin_ids = []
        admin_ids_env = os.getenv("ADMIN_USER_IDS", "")
        if admin_ids_env:
            try:
                admin_ids = [int(id.strip()) for id in admin_ids_env.split(",") if id.strip()]
                print(f"✅ Admin users configured: {len(admin_ids)} admins")
            except ValueError:
                print("❌ Invalid ADMIN_USER_IDS format. Please use comma-separated integers.")
        return admin_ids
        
    def _initialize_sheets_service(self) -> Optional[object]:
        """Initialize Google Sheets service with robust path handling"""
        if self.google_sheets_credentials_file and self.google_sheets_spreadsheet_id:
            try:
                # Resolve credentials file path relative to project root
                credentials_path = self._resolve_credentials_path()
                
                if not credentials_path or not os.path.exists(credentials_path):
                    print(f"❌ Google Sheets credentials file not found")
                    print(f"   Looked for: {credentials_path}")
                    print(f"   Please ensure credentials.json exists in project root")
                    print(f"   Or set GOOGLE_SHEETS_CREDENTIALS_FILE to correct path")
                    return None
                
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                sheets_service = build('sheets', 'v4', credentials=credentials)
                print(f"✅ Google Sheets integration enabled using: {credentials_path}")
                return sheets_service
            except Exception as e:
                print(f"❌ Google Sheets integration failed: {e}")
                return None
        else:
            print("⚠️  Google Sheets not configured - using mock data")
            print("   Set GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID to enable")
            return None
    
    def _resolve_credentials_path(self) -> Optional[str]:
        """Resolve the credentials file path relative to the project root"""
        if not self.google_sheets_credentials_file:
            return None
        
        # If it's already an absolute path, use it as-is
        if os.path.isabs(self.google_sheets_credentials_file):
            return self.google_sheets_credentials_file
        
        # Get the project root (2 levels up from this file: telegram_bot/config/settings.py -> project_root)
        current_dir = os.path.dirname(os.path.abspath(__file__))  # telegram_bot/config/
        telegram_bot_dir = os.path.dirname(current_dir)            # telegram_bot/
        project_root = os.path.dirname(telegram_bot_dir)           # project_root/
        
        # Resolve relative to project root
        credentials_path = os.path.join(project_root, self.google_sheets_credentials_file)
        return os.path.abspath(credentials_path)
    
    def _load_messages(self) -> Dict:
        """Load multilingual messages"""
        return {
            'en': {
                'welcome': "Hello {name}! 👋\nI'm your registration assistant. you can: \n/register to our upcoming events\ncheck your status with /status\nget help with /help",
                'welcome_no_name': "Hello there! 👋\nI'm your registration assistant. you can: \n/register to our upcoming events\ncheck your status with /status\nget help with /help",
                'submission_not_found': "❌ Could not find submission {submission_id}.\nPlease check your submission ID and try again.",
                'no_submission_linked': "❌ No submission linked to your account.\n\nTo link your form submission, please use the link provided after filling out the registration form.\nIt should look like: `/start SUBM_12345`",
                'status': "Your registration status:\n{status}\n{status_details}",
                'status_no_name': "You're not registered for any events. You can register with /register",
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
                        "/start - Start your journey with Wild Ginger\n"
                        "/register - Register for our upcoming events\n"
                        "/status - Check your registration progress\n"
                        # "/get_to_know - Complete the get-to-know section\n"
                        # "/remind_partner - Send reminder to your partner\n"
                        "/help - Show this help message\n"
                        # "/cancel <reason> - Cancel your registration with reason\n\n"
                        # "To link your registration, use the link provided after filling out the form.\n"
                        # "Example: /start SUBM_12345",
                        "\nyou can contact @beloved_kalanit for technical help and more details",
                'all_partners_complete': "✅ All your partners have already completed the form!",
                'partner_reminder_sent': "✅ Partner reminder sent successfully!",
                'partner_reminder_failed': "❌ Failed to send partner reminder."
            },
            'he': {
                # TODO welcome - hello, welcome to Wild Ginger bot. you can: /register to our upcoming events, check your status with /status, get help with /help
                'welcome': "שלום {name}! 👋\nאני עוזר הרשמה שלך. אתה יכול\nלהירשם לאירועים עתידיים באמצעות /register\nלבדוק את הסטטוס שלך באמצעות /status\nלקבל עזרה באמצעות /help",
                'welcome_no_name': "שלום! 👋\nאני עוזר הרשמה שלך. אתה יכול\nלהירשם לאירועים עתידיים באמצעות /register\nלבדוק את הסטטוס שלך באמצעות /status\nלקבל עזרה באמצעות /help",
                'submission_not_found': "❌ לא הצלחתי למצוא הגשה {submission_id}.\nאנא בדוק את מזהה ההגשה ונסה שוב.",
                'no_submission_linked': "❌ אין הגשה מקושרת לחשבון שלך.\n\nכדי לקשר את הטופס שלך, אנא השתמש בקישור שניתן לאחר מילוי טופס הרשמה.\nזה צריך להראות כך: `/start SUBM_12345`",
                'status': "סטטוס הרשמה שלך:\n{status}\n{status_details}",
                'status_no_name': "אינך רשום לאף אירוע. ניתן להירשם באמצעות /register",
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
                        "/start - צפייה בתפריט הבוט\n"
                        "/register - הרשמה לאירועי הליין\n"
                        "/status - בדיקת סטטוס ההרשמה\n"
                        # "/get_to_know - השלמת חלק ההיכרות\n"
                        # "/remind_partner - שליחת תזכורת לשותף\n"
                        "/help - הצגת הודעת עזרה זו\n"
                        # "/cancel <סיבה> - ביטול הרשמה עם סיבה\n\n"
                        # "כדי לקשר את הרשמתך, השתמש בקישור שניתן לאחר מילוי הטופס.\n"
                        # "דוגמה: /start SUBM_12345",
                        "\nניתן לפנות ל @beloved_kalanit לעזרה טכנית ובירורים נוספים",
                'all_partners_complete': "✅ כל הפרטנרים שלך כבר השלימו את הטופס!",
                'partner_reminder_sent': "✅ תזכורת הפרטנר נשלחה בהצלחה!",
                'partner_reminder_failed': "❌ נכשל בשליחת תזכורת הפרטנר."
            }
        }

# Global settings instance
settings = Settings() 