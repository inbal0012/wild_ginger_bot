# Wild Ginger Bot - Comprehensive Test Guide

## Overview

This guide covers all the tests created for the Wild Ginger Bot, including unit tests, integration tests, and scenario-based tests for different user types and event types.

## Test Structure

### Core Unit Tests

1. **`test_wild_ginger_bot.py`** - Main bot functionality tests
2. **`test_models.py`** - Data model tests
3. **`test_user_service.py`** - User management service tests
4. **`test_message_service.py`** - Message handling service tests
5. **`test_file_storage_service.py`** - File storage service tests
6. **`test_event_service.py`** - Event management service tests
7. **`test_registration_service.py`** - Registration service tests

### Scenario Tests

8. **`test_user_scenarios.py`** - User scenario tests (new vs returning users)
9. **`test_form_flow_scenarios.py`** - Form flow tests for different event types

## User Scenarios Covered

### New User Scenarios

#### 1. First-Time Registration
- **Test**: `test_new_user_first_time_registration`
- **Description**: Tests new user creating account and registering for first event
- **Expected Behavior**: User marked as new (not returning), form starts from beginning

#### 2. BDSM Workshop Registration
- **Test**: `test_new_user_bdsm_workshop_form_flow`
- **Description**: New user registering for BDSM workshop
- **Questions Tested**:
  - BDSM experience level (beginner/intermediate/experienced)
  - BDSM safety principles understanding
- **Expected Behavior**: Appropriate BDSM-specific questions

#### 3. Cuddle Party Registration
- **Test**: `test_new_user_cuddle_party_form_flow`
- **Description**: New user registering for cuddle party
- **Questions Tested**:
  - Physical touch comfort level
  - Boundary respect understanding
- **Expected Behavior**: Cuddle-specific questions, emphasis on comfort and boundaries

#### 4. Sexual Party Registration
- **Test**: `test_new_user_sexual_party_form_flow`
- **Description**: New user registering for sexual party
- **Questions Tested**:
  - Last STI test date
  - Enthusiastic consent understanding
  - Safe sex practices knowledge
- **Expected Behavior**: Sexual health and consent-focused questions

### Returning User Scenarios

#### 1. Returning User Registration
- **Test**: `test_returning_user_registration`
- **Description**: Returning user registering for event
- **Expected Behavior**: User marked as returning, experience considered

#### 2. Different Event Type Registration
- **Test**: `test_returning_user_different_event_type`
- **Description**: Returning user trying new event type
- **Expected Behavior**: Acknowledges returning status but treats as new to event type

#### 3. BDSM Workshop (Returning)
- **Test**: `test_returning_user_bdsm_workshop_form_flow`
- **Description**: Returning user with BDSM experience
- **Questions Tested**:
  - Advanced BDSM techniques interest
  - Teaching assistance willingness
- **Expected Behavior**: Advanced questions, teaching opportunities

## Event Type Tests

### BDSM Events
- **Event Types**: `bdsm_workshop`, `bdsm_party`
- **Key Questions**:
  - Experience level
  - Safety principles understanding
  - Advanced techniques interest (returning users)
  - Teaching willingness (returning users)
- **Safety Focus**: Consent, safety practices, experience validation

### Cuddle Events
- **Event Types**: `cuddle_party`, `cuddle_workshop`
- **Key Questions**:
  - Physical touch comfort
  - Boundary respect
  - Comfort level with different types of touch
- **Safety Focus**: Boundaries, comfort, non-sexual nature

### Sexual Events
- **Event Types**: `sexual_party`, `play_party`
- **Key Questions**:
  - STI test history
  - Consent understanding
  - Safe sex practices
  - Experience level
- **Safety Focus**: Sexual health, consent, safety practices

## Form Flow Tests

### New User Form Flow
- **Test**: `test_new_user_form_completion_flow`
- **Steps**:
  1. User starts form
  2. Answers basic questions (name, experience)
  3. Form completion
  4. Status update to "ready for review"
- **Expected Behavior**: Complete form flow with appropriate status updates

### Returning User Form Flow
- **Test**: `test_returning_user_form_completion_flow`
- **Steps**:
  1. User starts form
  2. Answers advanced questions
  3. Form completion
  4. Status update to "ready for review"
- **Expected Behavior**: Streamlined form for experienced users

### Language Support
- **Test**: `test_hebrew_language_form_flow`
- **Description**: Form flow in Hebrew language
- **Expected Behavior**: All questions and options in Hebrew

## Error Handling Tests

### User Not Found
- **Test**: `test_form_flow_user_not_found`
- **Expected Behavior**: Graceful handling, no crash

### Event Not Found
- **Test**: `test_form_flow_event_not_found`
- **Expected Behavior**: Graceful handling, no crash

### Invalid Language
- **Test**: `test_form_flow_invalid_language`
- **Expected Behavior**: Fallback to English

## Running Tests

### Install Dependencies
```bash
pip install -r tests/requirements-test.txt
```

### Run All Tests
```bash
cd tests
python run_all_tests.py
```

### Run Unit Tests Only
```bash
cd tests
python run_all_tests.py unit
```

### Run Specific Test File
```bash
cd tests
python run_all_tests.py specific test_user_scenarios.py
```

### Run with Coverage
```bash
cd tests
pytest --cov=telegram_bot --cov=wild_ginger_bot --cov-report=html
```

## Test Coverage Areas

### User Management
- ✅ New user creation
- ✅ Returning user detection
- ✅ Experience tracking
- ✅ Language preferences
- ✅ User updates

### Event Management
- ✅ Event creation
- ✅ Event type handling
- ✅ Event status management
- ✅ Event retrieval

### Registration Management
- ✅ Registration creation
- ✅ Registration status updates
- ✅ User-event relationships
- ✅ Registration validation

### Form Flow
- ✅ Question generation
- ✅ Answer processing
- ✅ Form completion
- ✅ Status updates
- ✅ Language support

### Message Handling
- ✅ Message retrieval
- ✅ Language fallbacks
- ✅ Message formatting
- ✅ Status message building

### File Storage
- ✅ Data persistence
- ✅ Data retrieval
- ✅ Error handling
- ✅ Unicode support

## Test Data

### Sample Users
- **New User**: `newuser123` - No experience, first time
- **Returning User**: `returning123` - Has BDSM experience
- **Mixed Experience**: `mixed123` - Different experience levels for different event types

### Sample Events
- **BDSM Workshop**: `bdsm1` - BDSM safety workshop
- **Cuddle Party**: `cuddle1` - Cozy cuddle party
- **Sexual Party**: `sexual1` - Intimate play party

### Sample Registrations
- **Active**: Status "approved", "pending", "form_complete"
- **Inactive**: Status "cancelled", "rejected"

## Best Practices

### Test Organization
- Each test file focuses on a specific service or scenario
- Tests are grouped by functionality
- Clear test names describe the scenario being tested

### Mock Usage
- External dependencies are mocked
- Google Sheets service is mocked for all tests
- Telegram bot is mocked for form flow tests

### Data Validation
- All data models are tested for proper creation
- Edge cases are covered (empty data, invalid data)
- Error conditions are tested

### Async Testing
- All async functions are properly tested
- `@pytest.mark.asyncio` decorator used for async tests
- Proper async mocking with `AsyncMock`

## Continuous Integration

### GitHub Actions
Tests can be integrated into CI/CD pipeline:

```yaml
- name: Run Tests
  run: |
    cd tests
    python run_all_tests.py
```

### Coverage Reports
- HTML coverage reports generated
- XML coverage reports for CI integration
- Coverage thresholds can be set

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Mock Issues**: Check that all external dependencies are mocked
3. **Async Issues**: Ensure `@pytest.mark.asyncio` is used for async tests
4. **Data Issues**: Verify test data matches expected schema

### Debug Mode
Run tests with verbose output:
```bash
pytest -v -s
```

### Specific Test Debug
Run single test with debug output:
```bash
pytest -v -s -k "test_new_user_bdsm_workshop_form_flow"
```

## Future Enhancements

### Planned Tests
- [ ] Integration tests with real Telegram API (sandbox)
- [ ] Performance tests for large datasets
- [ ] Load testing for concurrent users
- [ ] End-to-end user journey tests

### Test Improvements
- [ ] More edge case coverage
- [ ] Performance benchmarking
- [ ] Security testing
- [ ] Accessibility testing

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add comprehensive docstrings
3. Test both success and failure scenarios
4. Include edge cases
5. Update this documentation

## Support

For test-related issues:
1. Check the test logs
2. Verify test data is correct
3. Ensure all dependencies are installed
4. Check that mocks are properly configured 