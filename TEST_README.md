# Wild Ginger Telegram Bot - Test Suite

This document describes the comprehensive test suite for the Wild Ginger Telegram Bot, covering unit tests, integration tests, and edge cases.

## 🧪 Test Structure

### Test Files Overview

| File | Purpose | Coverage |
|------|---------|----------|
| `test_telegram_bot.py` | Core unit tests | Command handlers, message generation, Google Sheets integration |
| `test_integration.py` | Integration tests | End-to-end flows, component interactions |
| `test_fixtures.py` | Mock data & fixtures | Test data validation, mock objects |
| `run_tests.py` | Test runner | Automated test execution with reports |
| `test_reminders.py` | Reminder system tests | Existing reminder functionality |
| `test_multipartner.py` | Multi-partner tests | Partner parsing and validation |
| `test_sheets.py` | Google Sheets tests | Sheets connectivity and operations |

### Test Categories

#### 1. Unit Tests (`test_telegram_bot.py`)
- **Message Localization**: English/Hebrew message generation
- **Partner Management**: Partner parsing, status checking
- **Status Message Generation**: User status display logic
- **Google Sheets Integration**: Column mapping, row parsing
- **Command Handlers**: `/start`, `/status`, `/help`, `/cancel`, `/remind_partner`
- **Reminder System**: Automatic reminder logic
- **Edge Cases**: Empty data, malformed inputs, error conditions

#### 2. Integration Tests (`test_integration.py`)
- **End-to-End Flows**: Complete user registration flows
- **Multi-Partner Scenarios**: Complex partner management
- **Hebrew User Interface**: Localized user experience
- **Cancellation Flows**: User cancellation handling
- **Component Interactions**: Cross-component functionality
- **Error Handling**: Graceful error recovery
- **Performance Tests**: Large dataset handling

#### 3. Mock Data (`test_fixtures.py`)
- **Test Scenarios**: Happy path, edge cases, error conditions
- **Mock Objects**: Telegram objects, Google Sheets service
- **Data Validation**: Consistent test data
- **Fixtures**: Reusable test components

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py unit
python run_tests.py integration
python run_tests.py fixtures
```

### Manual Test Execution

```bash
# Unit tests only
python -m pytest test_telegram_bot.py -v

# Integration tests only
python -m pytest test_integration.py -v

# All tests with coverage
python -m pytest test_telegram_bot.py test_integration.py --cov=telegram_bot_polling --cov-report=html

# Run specific test class
python -m pytest test_telegram_bot.py::TestMessageLocalization -v

# Run specific test method
python -m pytest test_telegram_bot.py::TestMessageLocalization::test_get_message_english -v
```

### Test Dependencies

Install required packages:
```bash
pip install pytest pytest-asyncio pytest-cov
```

## 📊 Test Coverage

### Core Functionality Coverage

- ✅ **Command Handlers**: All major commands (`/start`, `/status`, `/help`, `/cancel`, `/remind_partner`)
- ✅ **Message Localization**: English and Hebrew message generation
- ✅ **Partner Management**: Single, multiple, and missing partner scenarios
- ✅ **Google Sheets Integration**: Data reading, writing, and error handling
- ✅ **Status Generation**: All user states and transitions
- ✅ **Reminder System**: Automatic and manual reminders
- ✅ **Error Handling**: Graceful degradation and error recovery

### Test Scenarios Covered

#### Happy Path Scenarios
- ✅ New user registration flow
- ✅ Returning user flow (auto-complete get-to-know)
- ✅ Hebrew user interface
- ✅ Single partner completion
- ✅ Multiple partner management
- ✅ Payment flow
- ✅ Group access flow

#### Edge Cases
- ✅ Invalid submission IDs
- ✅ Missing Telegram IDs
- ✅ Malformed user data
- ✅ Empty partner lists
- ✅ Mixed language preferences
- ✅ Unicode character handling
- ✅ Large datasets
- ✅ Concurrent operations

#### Error Conditions
- ✅ Google Sheets unavailable
- ✅ Telegram API errors
- ✅ Network timeouts
- ✅ Invalid user inputs
- ✅ Missing required fields
- ✅ Database inconsistencies

## 🧩 Test Data

### Mock Users

| User Type | Submission ID | Description |
|-----------|---------------|-------------|
| Complete User | `SUBM_12345` | All registration steps completed |
| Incomplete User | `SUBM_12346` | Waiting for partner completion |
| Alone User | `SUBM_12347` | Coming alone, returning participant |
| Hebrew User | `SUBM_12348` | Hebrew interface, mid-registration |
| Multi-Partner User | `SUBM_12349` | Multiple partners, some missing |
| Cancelled User | `SUBM_12350` | User who cancelled registration |

### Test Scenarios

```python
# Example test data usage
from test_fixtures import MockData, TestScenarios

# Get complete user data
user_data = MockData.get_parsed_complete_user()

# Get test scenario
scenario = TestScenarios.HAPPY_PATH_NEW_USER
```

## 🔧 Customizing Tests

### Adding New Test Cases

1. **Add to `test_telegram_bot.py`** for unit tests:
```python
class TestNewFeature:
    def test_new_functionality(self):
        # Your test here
        pass
```

2. **Add to `test_integration.py`** for integration tests:
```python
@pytest.mark.asyncio
async def test_new_flow(self):
    # Your async test here
    pass
```

3. **Add mock data to `test_fixtures.py`**:
```python
NEW_USER_ROW = [
    'SUBM_NEW', 'New User', 'new_field_value', ...
]
```

### Test Configuration

Modify `run_tests.py` to add new test configurations:
```python
test_configs.append({
    'name': 'New Test Suite',
    'command': 'python -m pytest test_new_feature.py -v',
    'description': 'Tests for new feature'
})
```

## 📈 Test Reports

### Coverage Report
After running tests with coverage, view the HTML report:
```bash
python -m http.server 8000
# Visit: http://localhost:8000/htmlcov/
```

### Test Results
The test runner provides:
- ✅ Pass/fail status for each test suite
- 📊 Overall success rate
- 📋 Detailed error messages
- 🔍 Coverage metrics

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Ensure `telegram_bot_polling.py` is in the same directory
2. **Async Test Issues**: Use `@pytest.mark.asyncio` for async tests
3. **Mock Failures**: Verify mock objects match expected interfaces
4. **Data Inconsistencies**: Run `python test_fixtures.py` to validate test data

### Debug Mode
Run tests with verbose output:
```bash
python -m pytest test_telegram_bot.py -v -s
```

### Test Isolation
Run single test method for debugging:
```bash
python -m pytest test_telegram_bot.py::TestMessageLocalization::test_get_message_english -v -s
```

## 📝 Best Practices

### Writing Tests
- ✅ Use descriptive test method names
- ✅ Test both happy path and edge cases
- ✅ Mock external dependencies (Google Sheets, Telegram API)
- ✅ Use fixtures for reusable test data
- ✅ Test error conditions and edge cases

### Test Organization
- ✅ Group related tests in classes
- ✅ Use consistent naming conventions
- ✅ Keep tests focused and atomic
- ✅ Document complex test scenarios

### Maintenance
- ✅ Update tests when code changes
- ✅ Validate test data consistency
- ✅ Monitor test coverage
- ✅ Remove obsolete tests

## 🚨 Continuous Integration

### GitHub Actions (Example)
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python run_tests.py
```

### Test Automation
Set up pre-commit hooks:
```bash
# Install pre-commit
pip install pre-commit

# Add to .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: python run_tests.py
        language: system
        pass_filenames: false
```

## 📚 Additional Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Python-Telegram-Bot Testing**: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Writing-Tests
- **Google Sheets API Testing**: https://developers.google.com/sheets/api/guides/concepts
- **Mock Testing in Python**: https://docs.python.org/3/library/unittest.mock.html

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add integration tests for new workflows
4. Update this documentation
5. Run full test suite before submitting PR

---

For questions or issues with the test suite, please check existing tests for examples or create an issue in the project repository. 