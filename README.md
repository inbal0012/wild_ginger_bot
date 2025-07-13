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

### 6. Run the Bot
```bash
python telegram_bot_polling.py
```

## Current Features

- **`/start`** - Welcome message and form submission linking
- **`/status`** - Show current registration progress with emojis
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

### Status Interpretation:
- **Form**: ✅ if Submission ID exists
- **Partner**: ✅ if not coming alone (`לבד`) and partner name provided
- **Get-to-know**: ✅ assumed complete if form submitted
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
- [ ] **Add `/remind_partner` and `/help` commands**
- [ ] **User data persistence** - Store Telegram ID ↔ Submission ID mapping in database
- [ ] **Partner coordination features** - Remind partners, link partners
- [ ] **Real-time status updates** - Webhook notifications from form updates
- [ ] **Admin commands** - Allow admins to update status directly via bot 