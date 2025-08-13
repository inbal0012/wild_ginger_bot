# Data Storage for Wild Ginger Bot

This document explains the file-based storage system implemented for development and testing purposes.

## Overview

The bot now uses a `FileStorageService` to persist data between bot restarts. This is a temporary solution until the Google Sheets integration is fully implemented.

## What Gets Stored

### 1. Active Forms (`active_forms.json`)
- Form state for users currently filling out registration forms
- Includes current step, answers, completion status, and timestamps
- Automatically saved after each form interaction

### 2. Poll Data (`poll_data.json`)
- Poll and quiz data created by the TelegramPollBot
- Vote tracking and results
- Automatically saved after poll creation and vote updates

## File Structure

```
data/
├── active_forms.json      # Form state data
├── poll_data.json         # Poll and quiz data
└── *_backup_*.json        # Backup files (created by management utility)
```

## Data Management

### Using the Management Utility

Run the data management utility to view and manage stored data:

```bash
python manage_data.py
```

**Available Actions:**
1. **List all data files** - See what data files exist
2. **View data file contents** - Examine the contents of any data file
3. **Backup data file** - Create a timestamped backup
4. **Delete data file** - Remove a data file (with confirmation)
5. **Show file info** - Get detailed information about file size and timestamps
6. **Clean up old backups** - Remove backup files

### Manual File Access

Data files are stored in the `data/` directory as JSON files. You can:

- **View files directly**: Open `data/active_forms.json` or `data/poll_data.json` in any text editor
- **Backup manually**: Copy the files with a timestamp suffix
- **Reset data**: Delete the files to start fresh

## Data Format

### Active Forms Format
```json
{
  "data": {
    "user_id_123": {
      "user_id": "user_id_123",
      "event_id": "event_456",
      "language": "he",
      "current_step": "personal_info",
      "answers": {
        "language_selection": "he",
        "event_details": "yes"
      },
      "completed": false,
      "created_at": 1703123456.789,
      "updated_at": 1703123500.123
    }
  },
  "metadata": {
    "saved_at": "2023-12-21T10:30:00.123456",
    "data_type": "dict",
    "version": "1.0"
  }
}
```

### Poll Data Format
```json
{
  "data": {
    "poll_id_789": {
      "question": "What's your favorite color?",
      "options": ["Red", "Blue", "Green"],
      "chat_id": -1001234567890,
      "message_id": 123,
      "creator": 987654321,
      "type": "regular",
      "votes": {
        "0": [123456789, 987654321],
        "1": [555666777],
        "2": []
      }
    }
  },
  "metadata": {
    "saved_at": "2023-12-21T10:30:00.123456",
    "data_type": "dict",
    "version": "1.0"
  }
}
```

## Automatic Saving

The bot automatically saves data in these situations:

### Form Flow Service
- When a new form is started
- After each form answer is processed
- When form state changes

### Poll Bot
- When a new poll is created
- When a new quiz is created
- When votes are cast
- When external polls are detected

## Development Tips

### Testing Form Flow
1. Start a form with `/start`
2. Answer some questions
3. Stop the bot (`Ctrl+C`)
4. Restart the bot
5. Continue from where you left off

### Testing Polls
1. Create a poll with `/poll`
2. Vote on the poll
3. Stop the bot
4. Restart the bot
5. Check results with `/results`

### Debugging
- Use `python manage_data.py` to inspect data files
- Check the `data/` directory for file timestamps
- Look for error messages in the bot logs

### Resetting Data
```bash
# Delete all data files
rm -rf data/

# Or use the management utility
python manage_data.py
# Choose option 4 to delete specific files
```

## Migration to Production

When ready to move to production:

1. **Google Sheets Integration**: Replace file storage with Google Sheets API calls
2. **Database Storage**: Consider using a proper database (PostgreSQL, MongoDB, etc.)
3. **Data Migration**: Export current data from files and import to new storage
4. **Backup Strategy**: Implement automated backups for production data

## Troubleshooting

### Common Issues

**"No data files found"**
- Check if the `data/` directory exists
- Verify the bot has write permissions

**"Error loading data"**
- Check file permissions
- Verify JSON format is valid
- Look for corrupted files

**"Data not persisting"**
- Check if save operations are being called
- Verify file paths are correct
- Check for disk space issues

### Logs
The bot logs all storage operations. Look for:
- `✅ Data saved to...`
- `✅ Data loaded from...`
- `❌ Error saving/loading data...`

## Security Notes

⚠️ **Important**: This file storage is for development only!

- Data is stored in plain text JSON files
- No encryption or access controls
- Files are stored locally on the bot server
- Do not use this in production without proper security measures

For production, implement:
- Encrypted storage
- Access controls
- Secure backup procedures
- Data retention policies 