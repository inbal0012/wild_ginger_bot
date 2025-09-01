# Wild Ginger Bot - Logging Setup

## Overview
The Wild Ginger Bot now includes comprehensive logging that saves all log messages to both the console and a local file. The logging configuration is centralized in the `BaseService` class, which `WildGingerBot` and more inherits from.

## Log Files
- **Location**: `logs/wild_ginger_bot.log`
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Encoding**: UTF-8

## Log Rotation
The bot uses rotating file handlers to manage log file size:
- **Maximum file size**: 10MB per log file
- **Backup files**: Up to 5 backup files (wild_ginger_bot.log.1, wild_ginger_bot.log.2, etc.)
- **Automatic rotation**: When the main log file reaches 10MB, it's automatically rotated

## Log Levels
- **INFO**: General information about bot operations
- **ERROR**: Error messages and exceptions
- **DEBUG**: Detailed debugging information (if enabled)

## What Gets Logged
- Bot startup and initialization
- User interactions (start, status, help, register commands)
- Form flow operations
- User creation and management
- Poll interactions
- Error messages and exceptions
- Bot command setup

## Example Log Entries
```
2024-01-15 10:30:15,123 - __main__ - INFO - Starting Wild Ginger Bot...
2024-01-15 10:30:15,456 - __main__ - INFO - Bot is running with polling...
2024-01-15 10:30:15,789 - __main__ - INFO - Bot command autocomplete set up successfully
2024-01-15 10:31:20,123 - __main__ - INFO - User 123456789 started the bot
2024-01-15 10:31:20,456 - __main__ - INFO - User 123456789 is already in the sheet
```

## Directory Structure
```
Wild Ginger Bot/
├── wild_ginger_bot.py
├── logs/
│   ├── wild_ginger_bot.log          # Current log file
│   ├── wild_ginger_bot.log.1        # Previous log file (if rotated)
│   ├── wild_ginger_bot.log.2        # Older log file (if rotated)
│   └── ...
└── README_LOGGING.md
```

## Architecture
- **BaseService**: Centralized logging configuration and common service functionality
- **WildGingerBot**: Inherits from BaseService and uses its logging methods
- **Other Services**: Can also inherit from BaseService for consistent logging

## Usage
The logging is automatically configured when you run the bot. No additional setup is required. The `logs` directory will be created automatically if it doesn't exist.

## Logging Methods
The BaseService provides convenient logging methods:
- `self.log_info(message)`: Log informational messages
- `self.log_error(message)`: Log error messages  
- `self.log_warning(message)`: Log warning messages

## Troubleshooting
- If you don't see log files, check that the bot has write permissions in the directory
- If log files are not rotating, check available disk space
- To change log levels, modify the `level=logging.INFO` parameter in the logging configuration 