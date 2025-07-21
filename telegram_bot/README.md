# Wild Ginger Bot - Refactored Architecture

This is the refactored version of the Wild Ginger Bot, broken down into maintainable, modular components.

## 📁 Project Structure

```
telegram_bot/
├── main.py                          # Main bot entry point
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configuration and environment variables
├── services/
│   ├── __init__.py
│   ├── sheets_service.py           # Google Sheets integration
│   └── message_service.py          # Multilingual message handling
├── handlers/
│   ├── __init__.py
│   ├── user_commands.py            # User command handlers (TODO)
│   └── admin_commands.py           # Admin command handlers (TODO)
├── models/
│   ├── __init__.py
│   └── registration.py             # Data models and enums
├── exceptions/
│   ├── __init__.py
│   └── service_exceptions.py       # Custom exceptions
└── utils/
    ├── __init__.py
    └── common.py                   # Shared utilities (TODO)
```

## 🧩 Architecture Overview

### Core Components

1. **Configuration Service** (`config/settings.py`)
   - Centralizes all environment variable handling
   - Manages Google Sheets connection
   - Loads multilingual messages

2. **Sheets Service** (`services/sheets_service.py`)
   - Handles all Google Sheets operations
   - CRUD operations for registrations
   - Data parsing and validation

3. **Message Service** (`services/message_service.py`)
   - Multilingual message handling
   - Status message formatting
   - Template management

4. **Models** (`models/registration.py`)
   - Data structures for registration data
   - Enums for status types
   - Type safety across services

5. **Exception Handling** (`exceptions/`)
   - Custom exceptions for different error types
   - Proper error propagation
   - User-friendly error messages

## 🔧 Benefits of the Refactored Architecture

### ✅ Maintainability
- **Single Responsibility**: Each service has one clear purpose
- **Small Files**: No more 3000-line files
- **Clear Dependencies**: Easy to understand what depends on what

### ✅ Testability
- **Isolated Components**: Each service can be tested independently
- **Mock-Friendly**: Services use dependency injection
- **Interface-Based**: Clear contracts between components

### ✅ Scalability
- **Microservice Ready**: Aligns with your planned architecture
- **Easy Replacement**: Swap implementations without changing contracts
- **Performance**: Services can be optimized independently

### ✅ Developer Experience
- **IDE Support**: Better autocomplete and type checking
- **Team Work**: Different developers can work on different services
- **Documentation**: Each service is self-documenting

## 🚀 How to Use

### Running the Bot

```bash
# Install dependencies (same as before)
pip install -r requirements.txt

# Run the refactored bot
cd telegram_bot
python main.py
```

### Using Services

```python
from services import SheetsService, MessageService
from models.registration import RegistrationStatus

# Initialize services
sheets = SheetsService()
messages = MessageService()

# Find a user's registration
registration = await sheets.find_submission_by_telegram_id("123456")

# Build a status message
if registration:
    status_msg = messages.build_status_message(
        registration, 
        language=registration.get('language', 'en')
    )
```

## 📋 Migration Status

### ✅ Completed
- [x] Core data models
- [x] Configuration service
- [x] Google Sheets service
- [x] Message service
- [x] Basic bot commands (/start, /status, /help)
- [x] Exception handling

### 🔄 In Progress
- [ ] Registration service (business logic)
- [ ] Admin service (admin commands)
- [ ] Reminder service (automated reminders)
- [ ] Conversation service (get-to-know flow)

### ⏳ TODO
- [ ] User command handlers
- [ ] Admin command handlers
- [ ] Background task scheduler
- [ ] Database migration (future)
- [ ] API endpoints (future)

## 🔧 Development Guidelines

### Adding a New Service

1. Create the service file in `services/`
2. Define the interface/contract
3. Implement the service class
4. Add to `services/__init__.py`
5. Update dependencies in main.py

### Adding a New Handler

1. Create the handler file in `handlers/`
2. Import required services
3. Implement async handler functions
4. Register handlers in main.py

### Error Handling

- Use custom exceptions from `exceptions/`
- Always log errors with context
- Return user-friendly messages
- Handle sheets connection failures gracefully

## 🔍 Key Improvements

### Before (Original File)
- 3000+ lines in one file
- Mixed responsibilities
- Global variables
- Hard to test
- Difficult to modify

### After (Refactored)
- ~200 lines per service
- Clear separation of concerns
- Dependency injection
- Easily testable
- Modular and extensible

## 🧪 Testing Strategy

Each service can be tested independently:

```python
# Test sheets service
def test_find_submission_by_id():
    sheets = SheetsService()
    result = await sheets.find_submission_by_id("SUBM_12345")
    assert result is not None

# Test message service with mocked data
def test_build_status_message():
    messages = MessageService()
    mock_data = {"form": True, "partner": False, "language": "en"}
    message = messages.build_status_message(mock_data)
    assert "✅" in message
```

## 📈 Future Enhancements

With this architecture, you can easily:

- Replace Google Sheets with a database
- Add new languages
- Implement caching
- Add API endpoints
- Scale services independently
- Add comprehensive logging
- Implement rate limiting

## 🤝 Contributing

When adding new features:

1. Follow the service-based architecture
2. Use type hints and proper error handling
3. Keep services focused and small
4. Document public interfaces
5. Add appropriate tests

---

This refactored architecture sets the foundation for a scalable, maintainable, and professional bot system! 🎉 