# Wild Ginger Bot - Telegram Registration Assistant

This is a Telegram bot for managing alternative event registrations with a multi-step flow.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Follow the instructions to get your bot token
4. Copy the token (format: `1234567890:ABCdefGHIjklMNOpqrSTUvwxyz`)

### 3. Google Sheets API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Create a Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Download the JSON credentials file
5. Share your Google Sheet with the service account email
6. Note your spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### 4. Environment Configuration
Create a `.env` file in the project root:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/your/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_RANGE=managed!A3:Z1000
```

**⚠️ Important**: Never commit your `.env` file or credentials file to version control.

### 5. Test Google Sheets Integration (Optional)
```bash
python test_sheets.py
```
This will verify your Google Sheets configuration and show you what data is being read.

### 6. Test Reminder System (Optional)
```bash
python test_reminders.py
```
This will test the reminder system functionality without actually sending messages.

### 7. Run the Bot
```bash
python telegram_bot_polling.py
```

## Current Features

- **`/start`** - Welcome message and form submission linking
- **`/status`** - Show current registration progress with emojis
- **`/remind_partner`** - Send reminders to partners who haven't completed their forms
- **Automatic reminder system** - Sends scheduled reminders based on registration status
- **Submission ID linking** - Connect Telegram accounts to external form submissions
- **Google Sheets integration** - Real-time data from your managed spreadsheet
- **Hebrew support** - Handles Hebrew column names and content
- **Automatic fallback** - Uses mock data if Google Sheets is unavailable

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot introduction |
| `/start SUBMISSION_ID` | Link Telegram account to form submission |
| `/status` | Show registration progress across all steps |
| `/get_to_know` | Complete the get-to-know section interactively |
| `/remind_partner` | Send reminders to partners who haven't completed forms |
| `/cancel <reason>` | Cancel registration with a reason |
| `/help` | Show help message and available commands |

## Get-to-Know Flow

The bot now includes an interactive get-to-know flow that helps create a safe and comfortable environment for events:

### How it works:
1. **Start the flow**: Use `/get_to_know` command
2. **Answer questions**: The bot asks simple questions about you, your experience, and something interesting about you
3. **Smart follow-up**: If you give a short or generic answer, the bot will ask a follow-up question to encourage more sharing
4. **Automatic completion**: Once you provide good responses, the bot marks this step as complete

### Features:
- **Hebrew-first**: Designed with Hebrew questions and responses
- **Boring answer detection**: Automatically detects generic answers like "לא יודע", "רגיל", etc.
- **Follow-up questions**: Encourages users to share something more interesting about themselves
- **Google Sheets integration**: Stores responses in your spreadsheet for admin review
- **Automatic status updates**: Marks the get-to-know step as complete when finished

### Example flow:
```
User: /get_to_know
Bot: אשמח לשמוע עליך קצת.
     קצת מי אתה, קצת על הניסיון שלך עם אירועים מהסוג הזה, קצת משהו מגניב עליך 😃

User: לא יודע
Bot: אשמח לשמוע משהו מגניב ומעניין עליך. לא חובה (ואף רצוי) לא מתוך העולם האלטרנטיבי.

User: אני אופה עוגות מדהימות ואוהב לרקוד סלסה
Bot: 🎉 תודה על השיתוף! זה עוזר לנו ליצור סביבה בטוחה ונוחה לכולם.
```

## Admin Commands

The bot includes a comprehensive admin notification system for managing registrations:

| Command | Description |
|---------|-------------|
| `/admin_dashboard` | Show admin dashboard with registration statistics |
| `/admin_approve SUBM_ID` | Approve a registration |
| `/admin_reject SUBM_ID [reason]` | Reject a registration with optional reason |
| `/admin_status SUBM_ID` | Check detailed status of a registration |
| `/admin_digest` | Generate and send weekly digest manually |

### Admin Notifications

The system automatically sends notifications to admins for:
- **New registrations ready for review** - When users complete all required steps
- **Partner registration delays** - When partners haven't completed forms after 24 hours
- **Payment overdue** - When approved registrations haven't completed payment
- **Weekly digest** - Automatic summary of registration statuses every 7 days

### Admin Configuration

To enable admin notifications, add admin user IDs to your `.env` file:

```env
# Comma-separated list of Telegram User IDs
ADMIN_USER_IDS=123456789,987654321
```

**Note:** To get your Telegram User ID, message [@userinfobot](https://t.me/userinfobot) on Telegram.

## Reminder System

The bot now includes a comprehensive reminder system that automatically sends reminders based on registration status and timing:

### Automatic Reminders:
- **Partner reminders**: Sent every 24 hours if partners haven't completed their forms
- **Payment reminders**: Sent every 3 days after approval until payment is confirmed
- **Group opening reminders**: Sent when event groups open (7 days before event)
- **Event reminders**: Sent 1 day before the event

### Manual Reminders:
- Use `/remind_partner` to manually send reminders to missing partners
- The bot will tell you which partners are missing and track reminder history
- Supports both Hebrew and English messaging

### Reminder Features:
- **Rate limiting**: Won't spam users with too many reminders
- **Logging**: All reminders are logged for admin tracking
- **Language support**: Sends reminders in user's preferred language
- **Multi-partner support**: Handles users with multiple partners correctly

## Form Submission Linking

The bot supports linking external form submissions to Telegram accounts:

1. **User fills out external form** (Google Form, etc.)
2. **Form saves to Google Sheets** with unique Submission ID
3. **User gets link**: `https://t.me/yourbotname?start=SUBM_12345`
4. **Bot links accounts** when user clicks the link
5. **Status tracking** now works with their actual submission

### Example Link Format:
```
https://t.me/yourbotname?start=SUBM_12345
```

This automatically runs `/start SUBM_12345` and links the user.

## Google Sheets Structure

The bot expects your Google Sheet to have these columns (row 3 should contain headers):

| Column Name | Description | Example Values |
|-------------|-------------|----------------|
| **Status** | Current registration status | `pending`, `approved`, `paid`, `rejected` |
| **Submission ID** | Unique identifier for each submission | `SUBM_12345`, `SUBM_67890` |
| **שם מלא** | Full name (Hebrew) | `דני כהן`, `מרים לוי` |
| **מגיע.ה לבד או באיזון** | Coming alone or in balance (Hebrew) | `לבד`, `באיזון` |
| **שם הפרטנר** | Partner name (Hebrew) | `יונתן`, `שרה` |
| **Get To Know Complete** | Whether get-to-know section is finished | `TRUE`, `FALSE` |
| **Get To Know Response** / **תשובת היכרות** | User's get-to-know response | `Free text response about the user` |

### Status Interpretation:
- **Form**: ✅ if Submission ID exists
- **Partner**: ✅ if not coming alone (`לבד`) and partner name provided
- **Get-to-know**: ✅ if `Get To Know Complete` is `TRUE` or user is returning participant
- **Approved**: ✅ if status contains `approved` or `מאושר`
- **Paid**: ✅ if status contains `paid` or `שולם`
- **Group**: ✅ if status contains `group` or `קבוצה`

## Registration Flow Status

The bot tracks these registration steps:
- 📋 **Form**: Event-specific questionnaire
- 🤝 **Partner**: Partner matching/linking
- 💬 **Get-to-know**: Introduction and boundaries
- 🛠️ **Status**: Admin approval
- 💸 **Payment**: Payment confirmation
- 👥 **Group**: Event group access

## Next Steps

- [x] **Environment configuration** - Bot token management ✅
- [x] **Submission ID linking** - Connect forms to Telegram accounts ✅
- [x] **Google Sheets integration** - Real-time data from managed spreadsheet ✅
- [x] **Hebrew support** - Handle Hebrew column names and content ✅
- [x] **Status validation** - Verify submission exists before showing status ✅
- [x] **Add `/remind_partner` and `/help` commands** ✅
- [x] **Automatic reminder system** - Time-based reminders for partners, payment, and groups ✅
- [x] **Partner coordination features** - Remind partners, link partners ✅
- [x] **Get-to-know interactive flow** - Complete conversational get-to-know section ✅
- [ ] **Enhanced partner reminder sending** - Email/SMS integration for actual partner contact
- [ ] **User data persistence** - Store Telegram ID ↔ Submission ID mapping in database
- [ ] **Real-time status updates** - Webhook notifications from form updates
- [ ] **Admin commands** - Allow admins to update status directly via bot
- [ ] **Event date integration** - Calculate reminders based on actual event dates
- [ ] **Reminder analytics** - Track reminder effectiveness and delivery rates 