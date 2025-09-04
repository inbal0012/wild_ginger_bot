# PollDataService Documentation

## Overview

The `PollDataService` is a dedicated service for managing poll data in Google Sheets. It provides comprehensive CRUD operations for polls and their associated data, with advanced querying and management capabilities.

## Features

- **Complete CRUD Operations**: Create, read, update, and delete polls
- **Advanced Querying**: Search polls by various criteria
- **Statistics & Analytics**: Get comprehensive poll statistics
- **Automatic Cleanup**: Remove expired polls automatically
- **Google Sheets Integration**: Full integration with Google Sheets backend
- **Error Handling**: Comprehensive error handling and logging

## Service Structure

### Dependencies
- `BaseService`: Base service class for common functionality
- `SheetsService`: Google Sheets integration service

### Sheet Structure
The service manages a `PollData` sheet with the following columns:
- `poll_id`: Unique identifier for the poll
- `poll_data`: JSON string containing complete poll information
- `created_at`: Timestamp when the poll was created
- `updated_at`: Timestamp when the poll was last updated

## API Reference

### Constructor

```python
def __init__(self, sheets_service: SheetsService)
```

**Parameters:**
- `sheets_service`: Instance of SheetsService for Google Sheets operations

**Description:** Initializes the service and ensures the PollData sheet exists with proper structure.

### Core Methods

#### 1. `save_single_poll(poll_id: str, poll_info: Dict[str, Any]) -> bool`

Saves a single poll to Google Sheets efficiently. This is the recommended method for individual poll operations.

**Parameters:**
- `poll_id`: Unique identifier for the poll
- `poll_info`: Poll information dictionary

**Returns:** `True` if saved successfully, `False` otherwise

**Example:**
```python
poll_info = {
    "question": "What's your favorite color?",
    "options": ["Red", "Blue", "Green"],
    "type": "poll",
    "creator": "user123"
}
success = poll_service.save_single_poll("color_poll", poll_info)
```

#### 2. `save_multiple_polls(poll_data: Dict[str, Any]) -> bool`

Saves multiple poll data entries to Google Sheets efficiently. Use this when you need to save multiple polls at once.

**Parameters:**
- `poll_data`: Dictionary mapping poll_id to poll information

**Returns:** `True` if saved successfully, `False` otherwise

**Example:**
```python
polls = {
    "poll1": {"question": "What's your favorite color?", "options": ["Red", "Blue", "Green"]},
    "poll2": {"question": "How are you today?", "options": ["Great", "Good", "Okay", "Bad"]}
}
success = poll_service.save_multiple_polls(polls)
```

#### 3. `save_poll_data(poll_data: Dict[str, Any]) -> bool`

**Legacy method**: Saves multiple poll data entries to Google Sheets. This method is deprecated and maintained for backward compatibility. Use `save_single_poll()` for single polls or `save_multiple_polls()` for multiple polls for better performance.

#### 4. `load_poll_data() -> Dict[str, Any]`

Loads all poll data from Google Sheets.

**Returns:** Dictionary mapping poll_id to poll information

**Example:**
```python
all_polls = poll_service.load_poll_data()
for poll_id, poll_info in all_polls.items():
    print(f"Poll {poll_id}: {poll_info['question']}")
```

#### 5. `get_poll_by_id(poll_id: str) -> Optional[Dict[str, Any]]`

Retrieves a specific poll by its ID.

**Parameters:**
- `poll_id`: Unique identifier for the poll

**Returns:** Poll information dictionary or `None` if not found

**Example:**
```python
poll = poll_service.get_poll_by_id("poll123")
if poll:
    print(f"Question: {poll['question']}")
```

#### 6. `create_poll(poll_id: str, poll_info: Dict[str, Any]) -> bool`

Creates a new poll in the system.

**Parameters:**
- `poll_id`: Unique identifier for the poll
- `poll_info`: Poll information dictionary

**Returns:** `True` if created successfully, `False` otherwise

**Example:**
```python
poll_info = {
    "question": "What's your favorite programming language?",
    "options": ["Python", "JavaScript", "Java", "C++"],
    "type": "quiz",
    "creator": "user123",
    "expires_at": "2024-12-31T23:59:59"
}
success = poll_service.create_poll("lang_poll", poll_info)
```

#### 7. `update_poll(poll_id: str, poll_info: Dict[str, Any]) -> bool`

Updates an existing poll with new information.

**Parameters:**
- `poll_id`: Unique identifier for the poll
- `poll_info`: Updated poll information dictionary

**Returns:** `True` if updated successfully, `False` otherwise

**Example:**
```python
updated_info = {
    "question": "Updated question?",
    "options": ["Option A", "Option B"],
    "type": "poll"
}
success = poll_service.update_poll("poll123", updated_info)
```

#### 8. `remove_poll_data(poll_id: str) -> bool`

Removes a poll from the system.

**Parameters:**
- `poll_id`: Unique identifier for the poll to remove

**Returns:** `True` if removed successfully, `False` otherwise

**Example:**
```python
success = poll_service.remove_poll_data("poll123")
```

### Query Methods

#### 7. `get_polls_by_creator(creator_id: str) -> List[Dict[str, Any]]`

Retrieves all polls created by a specific user.

**Parameters:**
- `creator_id`: User ID of the poll creator

**Returns:** List of poll information dictionaries

**Example:**
```python
user_polls = poll_service.get_polls_by_creator("user123")
print(f"User created {len(user_polls)} polls")
```

#### 8. `get_active_polls() -> List[Dict[str, Any]]`

Retrieves all active (non-expired) polls.

**Returns:** List of active poll information dictionaries

**Example:**
```python
active_polls = poll_service.get_active_polls()
print(f"There are {len(active_polls)} active polls")
```

#### 9. `get_polls_by_type(poll_type: str) -> List[Dict[str, Any]]`

Retrieves all polls of a specific type.

**Parameters:**
- `poll_type`: Type of poll to filter by (e.g., "quiz", "poll", "survey")

**Returns:** List of poll information dictionaries

**Example:**
```python
quiz_polls = poll_service.get_polls_by_type("quiz")
print(f"Found {len(quiz_polls)} quiz polls")
```

#### 10. `search_polls(search_term: str) -> List[Dict[str, Any]]`

Searches polls by question text or other searchable fields.

**Parameters:**
- `search_term`: Text to search for

**Returns:** List of matching poll information dictionaries

**Example:**
```python
results = poll_service.search_polls("favorite")
print(f"Found {len(results)} polls containing 'favorite'")
```

### Utility Methods

#### 11. `get_poll_statistics() -> Dict[str, Any]`

Retrieves comprehensive statistics about all polls.

**Returns:** Dictionary containing poll statistics

**Example:**
```python
stats = poll_service.get_poll_statistics()
print(f"Total polls: {stats['total_polls']}")
print(f"Active polls: {stats['active_polls']}")
print(f"Total votes: {stats['total_votes']}")
```

**Statistics include:**
- `total_polls`: Total number of polls
- `active_polls`: Number of active polls
- `poll_types`: Count by poll type
- `creators`: Count by creator
- `total_votes`: Total number of votes across all polls

#### 12. `cleanup_expired_polls() -> int`

Automatically removes expired polls from the system.

**Returns:** Number of polls removed

**Example:**
```python
removed_count = poll_service.cleanup_expired_polls()
print(f"Cleaned up {removed_count} expired polls")
```

## Poll Data Structure

### Standard Poll Fields

```python
poll_info = {
    "question": "What's your favorite color?",
    "options": ["Red", "Blue", "Green", "Yellow"],
    "type": "poll",  # "poll", "quiz", "survey"
    "creator": "user123",
    "created_at": "2024-01-01T10:00:00",
    "expires_at": "2024-12-31T23:59:59",  # Optional
    "is_anonymous": False,
    "allow_multiple": False,
    "max_votes": 1
}
```

### Quiz-Specific Fields

```python
quiz_info = {
    "question": "What is 2 + 2?",
    "options": ["3", "4", "5", "6"],
    "type": "quiz",
    "correct_answer": 1,  # Index of correct option
    "explanation": "Basic arithmetic",
    "points": 10
}
```

### Survey-Specific Fields

```python
survey_info = {
    "question": "How satisfied are you with our service?",
    "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"],
    "type": "survey",
    "scale": "1-5",
    "category": "customer_satisfaction"
}
```

## Usage Examples

### Basic Poll Management

```python
# Initialize service
poll_service = PollDataService(sheets_service)

# Create a new poll
poll_info = {
    "question": "What's your favorite season?",
    "options": ["Spring", "Summer", "Fall", "Winter"],
    "type": "poll",
    "creator": "admin_user"
}
success = poll_service.create_poll("season_poll", poll_info)

# Get the poll
poll = poll_service.get_poll_by_id("season_poll")
if poll:
    print(f"Question: {poll['question']}")

# Update the poll
poll['options'].append("All seasons")
success = poll_service.update_poll("season_poll", poll)

# Remove the poll
success = poll_service.remove_poll_data("season_poll")
```

### Advanced Querying

```python
# Get all polls by a specific user
user_polls = poll_service.get_polls_by_creator("user123")

# Get all active polls
active_polls = poll_service.get_active_polls()

# Search for polls containing specific text
search_results = poll_service.search_polls("favorite")

# Get statistics
stats = poll_service.get_poll_statistics()
print(f"User has created {len(user_polls)} polls")
print(f"There are {stats['active_polls']} active polls")
```

### Batch Operations

```python
# Save multiple polls at once (recommended method)
polls_batch = {
    "poll1": {"question": "Q1?", "options": ["A", "B"]},
    "poll2": {"question": "Q2?", "options": ["X", "Y", "Z"]},
    "poll3": {"question": "Q3?", "options": ["Yes", "No"]}
}
success = poll_service.save_multiple_polls(polls_batch)

# Save single poll (most efficient for individual operations)
success = poll_service.save_single_poll("single_poll", {"question": "Single Q?", "options": ["Yes", "No"]})

# Load all polls
all_polls = poll_service.load_poll_data()
```

## Error Handling

The service includes comprehensive error handling:

- **Sheet Creation**: Automatically creates the PollData sheet if it doesn't exist
- **Data Validation**: Validates poll data before saving
- **JSON Parsing**: Handles JSON serialization/deserialization errors
- **Network Issues**: Gracefully handles Google Sheets API errors
- **Logging**: Detailed logging for debugging and monitoring

## Performance Considerations

- **Single Poll Operations**: Use `save_single_poll()` for individual poll operations for best performance
- **Batch Operations**: Use `save_multiple_polls()` for multiple polls instead of individual calls
- **Legacy Method**: `save_poll_data()` is deprecated - use the appropriate method based on your needs
- **Caching**: Consider implementing caching for frequently accessed polls
- **Pagination**: For large datasets, consider implementing pagination
- **Cleanup**: Regular cleanup of expired polls to maintain performance

## Integration with FormFlowService

The PollDataService is integrated with FormFlowService:

```python
# In FormFlowService
self.poll_data_service = PollDataService(sheets_service)

# Usage - Single poll (most efficient)
success = self.poll_data_service.save_single_poll("poll_id", {"question": "Q?", "options": ["A", "B"]})

# Usage - Multiple polls
poll_data = {"poll_id": {"question": "Q?", "options": ["A", "B"]}}
success = self.poll_data_service.save_multiple_polls(poll_data)
```

## Testing

The service can be tested using mock objects:

```python
from unittest.mock import Mock

# Create mock sheets service
mock_sheets = Mock()
mock_sheets.get_data_from_sheet.return_value = {'headers': [], 'rows': []}
mock_sheets.update_sheet.return_value = True

# Initialize service
poll_service = PollDataService(mock_sheets)

# Test methods
success = poll_service.create_poll("test", {"question": "Test?"})
```

## Future Enhancements

Potential improvements for the service:

1. **Real-time Updates**: WebSocket integration for live poll updates
2. **Analytics Dashboard**: Advanced analytics and reporting
3. **Poll Templates**: Predefined poll templates for common use cases
4. **Export Functionality**: Export poll data to various formats
5. **Access Control**: Role-based access control for poll management
6. **Poll Scheduling**: Schedule polls to be active at specific times
7. **Response Validation**: Advanced validation for poll responses
8. **Integration APIs**: REST API endpoints for external integrations 