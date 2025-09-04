import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.event_service import EventService
from telegram_bot.models.event import CreateEventDTO, EventDTO


class TestEventService:
    """Test suite for EventService class"""
    
    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock SheetsService"""
        sheets_service = Mock()
        sheets_service.headers = {
            "Events": {
                "id": 0,
                "name": 1,
                "start_date": 2,
                "start_time": 3,
                "event_type": 4,
                "price_single": 5,
                "price_couple": 6,
                "theme": 7,
                "max_participants": 8,
                "status": 9,
                "created_at": 10,
                "updated_at": 11,
                "main_group_id": 12,
                "singles_group_id": 13,
                "is_public": 14,
                "description": 15,
                "location": 16,
                "end_date": 17,
                "end_time": 18,
                "price_include": 19,
                "schedule": 20,
                "participant_commitment": 21,
                "line_rules": 22,
                "place_rules": 23,
                "balance": 24
            }
        }
        return sheets_service
    
    @pytest.fixture
    def event_service(self, mock_sheets_service):
        """Create an EventService instance with mocked dependencies"""
        return EventService(mock_sheets_service)
    
    @pytest.fixture
    def sample_event_data(self):
        """Sample event data for testing"""
        return {
            'headers': ['id', 'name', 'start_date', 'start_time', 'event_type', 'price_single', 'price_couple', 'theme', 'max_participants', 'status', 'created_at', 'updated_at', 'main_group_id', 'singles_group_id', 'is_public', 'description', 'location', 'end_date', 'end_time', 'price_include', 'schedule', 'participant_commitment', 'line_rules', 'place_rules', 'balance'],
            'rows': [
                ['event1', 'Test Event 1', '2024-01-15', '18:00', 'play', '100', '180', 'BDSM Basics', '20', 'active', '2024-01-01 10:00:00', '2024-01-01 10:00:00', 'group1', 'singles1', 'true', 'Test description', 'Test location', '2024-01-15', '22:00', 'Food included', '18:00-22:00', 'Commitment required', 'Line rules', 'Place rules', '0'],
                ['event2', 'Test Event 2', '2024-02-15', '19:00', 'cuddle', '150', '250', 'Fetish Party', '50', 'inactive', '2024-01-01 10:00:00', '2024-01-01 10:00:00', 'group2', 'singles2', 'false', 'Test description 2', 'Test location 2', '2024-02-15', '23:00', 'Drinks included', '19:00-23:00', 'Commitment required', 'Line rules 2', 'Place rules 2', '0'],
                ['event3', 'Test Event 3', '2024-03-15', '20:00', 'sexual', '120', '200', 'Advanced BDSM', '15', 'active', '2024-01-01 10:00:00', '2024-01-01 10:00:00', 'group3', 'singles3', 'true', 'Test description 3', 'Test location 3', '2024-03-15', '24:00', 'Full meal', '20:00-24:00', 'Commitment required', 'Line rules 3', 'Place rules 3', '0']
            ]
        }
    
    def test_init(self, mock_sheets_service):
        """Test EventService initialization"""
        event_service = EventService(mock_sheets_service)
        
        assert event_service.sheets_service == mock_sheets_service
        assert event_service.headers == mock_sheets_service.headers["Events"]
    
    def test_get_upcoming_events_success(self, event_service, sample_event_data):
        """Test getting upcoming events successfully"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        events = event_service.get_upcoming_events()
        
        assert len(events) == 2  # Only active events
        assert events[0].id == "event1"
        assert events[0].name == "Test Event 1"
        assert events[0].status == "active"
        assert events[1].id == "event3"
        assert events[1].name == "Test Event 3"
        assert events[1].status == "active"
        
        event_service.sheets_service.get_data_from_sheet.assert_called_once_with("Events")
    
    def test_get_upcoming_events_no_data(self, event_service):
        """Test getting upcoming events when no data is available"""
        event_service.sheets_service.get_data_from_sheet.return_value = None
        
        events = event_service.get_upcoming_events()
        
        assert events == []
        event_service.sheets_service.get_data_from_sheet.assert_called_once_with("Events")
    
    def test_get_upcoming_events_empty_data(self, event_service):
        """Test getting upcoming events when data is empty"""
        event_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['id', 'name', 'status'],
            'rows': []
        }
        
        events = event_service.get_upcoming_events()
        
        assert events == []
    
    def test_get_upcoming_events_no_active_events(self, event_service):
        """Test getting upcoming events when no active events exist"""
        event_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['id', 'name', 'description', 'start_date', 'start_time', 'end_date', 'end_time', 'location', 'schedule', 'event_type', 'price_single', 'price_couple', 'price_include', 'theme', 'max_participants', 'status', 'participant_commitment', 'line_rules', 'place_rules', 'created_at', 'balance'],
            'rows': [
                ['event1', 'Test Event 1', 'Description 1', '2024-01-01', '18:00', '2024-01-01', '22:00', 'Location 1', '18:00-22:00', 'sexual', '100', '180', 'Food included', 'Theme 1', '20', 'inactive', 'Required', 'Rules 1', 'Place rules 1', '2024-01-01', '0'],
                ['event2', 'Test Event 2', 'Description 2', '2024-01-02', '19:00', '2024-01-02', '23:00', 'Location 2', '19:00-23:00', 'cuddle', '120', '200', 'Food included', 'Theme 2', '25', 'cancelled', 'Required', 'Rules 2', 'Place rules 2', '2024-01-02', '0']
            ]
        }
        
        events = event_service.get_upcoming_events()
        
        assert events == []
    
    def test_row_to_eventDTO(self, event_service):
        """Test converting row to EventDTO"""
        row = [
            'event1', 'Test Event', '2024-01-15', '18:00', 'cuddle', '100', '180',
            'BDSM Basics', '20', 'active', '2024-01-01 10:00:00', '2024-01-01 10:00:00',
            'group1', 'singles1', 'true', 'Test description', 'Test location',
            '2024-01-15', '22:00', 'Food included', '18:00-22:00', 'Commitment required',
            'Line rules', 'Place rules', '0'
        ]
        
        event_dto = event_service.row_to_eventDTO(row)
        
        assert isinstance(event_dto, EventDTO)
        assert event_dto.id == "event1"
        assert event_dto.name == "Test Event"
        assert event_dto.start_date == "2024-01-15"
        assert event_dto.start_time == "18:00"
        assert event_dto.event_type == "workshop"
        assert event_dto.price_single == "100"
        assert event_dto.price_couple == "180"
        assert event_dto.theme == "BDSM Basics"
        assert event_dto.max_participants == "20"
        assert event_dto.status == "active"
        assert event_dto.created_at == "2024-01-01 10:00:00"
        assert event_dto.updated_at == "2024-01-01 10:00:00"
        assert event_dto.main_group_id == "group1"
        assert event_dto.singles_group_id == "singles1"
        assert event_dto.is_public == "true"
        assert event_dto.description == "Test description"
        assert event_dto.location == "Test location"
        assert event_dto.end_date == "2024-01-15"
        assert event_dto.end_time == "22:00"
        assert event_dto.price_include == "Food included"
        assert event_dto.schedule == "18:00-22:00"
        assert event_dto.participant_commitment == "Commitment required"
        assert event_dto.line_rules == "Line rules"
        assert event_dto.place_rules == "Place rules"
    
    def test_get_event_by_id_found(self, event_service, sample_event_data):
        """Test getting event by ID when event exists"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        event = event_service.get_event_by_id("event1")
        
        assert event is not None
        assert event.id == "event1"
        assert event.name == "Test Event 1"
        assert event.status == "active"
        event_service.sheets_service.get_data_from_sheet.assert_called_once_with("Events")
    
    def test_get_event_by_id_not_found(self, event_service, sample_event_data):
        """Test getting event by ID when event doesn't exist"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        event = event_service.get_event_by_id("nonexistent")
        
        assert event is None
        event_service.sheets_service.get_data_from_sheet.assert_called_once_with("Events")
    
    def test_get_event_by_id_no_data(self, event_service):
        """Test getting event by ID when no data is available"""
        event_service.sheets_service.get_data_from_sheet.return_value = None
        
        event = event_service.get_event_by_id("event1")
        
        assert event is None
        event_service.sheets_service.get_data_from_sheet.assert_called_once_with("Events")
    
    def test_get_event_by_id_string_conversion(self, event_service, sample_event_data):
        """Test that event_id is converted to string for comparison"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        # Test with integer input
        event = event_service.get_event_by_id(123)
        
        assert event is None  # No event with ID "123" in sample data
    
    @pytest.mark.asyncio
    async def test_create_new_event_success(self, event_service):
        """Test successful event creation"""
        sheet_data = {
            'headers': ['id', 'name', 'start_date', 'start_time', 'event_type', 'price_single', 'price_couple', 'theme', 'max_participants', 'status', 'created_at', 'updated_at', 'main_group_id', 'singles_group_id', 'is_public', 'description', 'location', 'end_date', 'end_time', 'price_include', 'schedule', 'participant_commitment', 'line_rules', 'place_rules', 'balance'],
            'rows': []
        }
        event_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        event_service.sheets_service.append_row = AsyncMock(return_value=True)
        
        event_dto = CreateEventDTO(
            name="New Event",
            start_date="2024-04-15",
            start_time="19:00",
            event_type="workshop",
            price_single="120",
            price_couple="200",
            status="active",
            created_at="2024-04-15"
        )
        
        result = await event_service.create_new_event(event_dto)
        
        assert result is True
        event_service.sheets_service.append_row.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_new_event_failure_no_sheet_data(self, event_service):
        """Test event creation failure when sheet data is not available"""
        event_service.sheets_service.get_data_from_sheet.return_value = None
        
        event_dto = CreateEventDTO(
            name="New Event",
            start_date="2024-04-15",
            start_time="19:00",
            event_type="workshop",
            price_single="120",
            price_couple="200",
            status="active",
            created_at="2024-04-15"
        )
        
        result = await event_service.create_new_event(event_dto)
        
        assert result is False
        event_service.sheets_service.get_data_from_sheet.assert_called_once_with("Events")
        event_service.sheets_service.append_row.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_new_event_failure_append_fails(self, event_service):
        """Test event creation failure when append_row fails"""
        sheet_data = {
            'headers': ['id', 'name', 'start_date', 'start_time', 'event_type', 'price_single', 'price_couple', 'theme', 'max_participants', 'status', 'created_at', 'updated_at', 'main_group_id', 'singles_group_id', 'is_public', 'description', 'location', 'end_date', 'end_time', 'price_include', 'schedule', 'participant_commitment', 'line_rules', 'place_rules', 'balance'],
            'rows': []
        }
        event_service.sheets_service.get_data_from_sheet.return_value = sheet_data
        event_service.sheets_service.append_row = AsyncMock(return_value=False)
        
        event_dto = CreateEventDTO(
            name="New Event",
            start_date="2024-04-15",
            start_time="19:00",
            event_type="workshop",
            price_single="120",
            price_couple="200",
            status="active",
            created_at="2024-04-15"
        )
        
        result = await event_service.create_new_event(event_dto)
        
        assert result is False
    
    def test_get_event_type_found(self, event_service, sample_event_data):
        """Test getting event type when event exists"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        event_type = event_service.get_event_type("event1")
        
        assert event_type == "workshop"
    
    def test_get_event_type_not_found(self, event_service, sample_event_data):
        """Test getting event type when event doesn't exist"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        event_type = event_service.get_event_type("nonexistent")
        
        assert event_type is None
    
    def test_get_event_name_by_id_found(self, event_service, sample_event_data):
        """Test getting event name when event exists"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        event_name = event_service.get_event_name_by_id("event1")
        
        assert event_name == "Test Event 1"
    
    def test_get_event_name_by_id_not_found(self, event_service, sample_event_data):
        """Test getting event name when event doesn't exist"""
        event_service.sheets_service.get_data_from_sheet.return_value = sample_event_data
        
        event_name = event_service.get_event_name_by_id("nonexistent")
        
        assert event_name is None
    
    def test_get_event_name_by_id_no_data(self, event_service):
        """Test getting event name when no data is available"""
        event_service.sheets_service.get_data_from_sheet.return_value = None
        
        event_name = event_service.get_event_name_by_id("event1")
        
        assert event_name is None
    
    def test_row_to_eventDTO_with_empty_values(self, event_service):
        """Test converting row with empty values to EventDTO"""
        row = [''] * 25  # Empty row with 25 columns
        row[0] = 'event1'  # Set only the ID
        
        event_dto = event_service.row_to_eventDTO(row)
        
        assert event_dto.id == "event1"
        assert event_dto.name == ""
        assert event_dto.start_date == ""
        assert event_dto.start_time == ""
        assert event_dto.event_type == ""
        assert event_dto.price_single == ""
        assert event_dto.price_couple == ""
        assert event_dto.theme == ""
        assert event_dto.max_participants == ""
        assert event_dto.status == ""
        assert event_dto.created_at == ""
        assert event_dto.updated_at == ""
        assert event_dto.main_group_id == ""
        assert event_dto.singles_group_id == ""
        assert event_dto.is_public == ""
        assert event_dto.description == ""
        assert event_dto.location == ""
        assert event_dto.end_date == ""
        assert event_dto.end_time == ""
        assert event_dto.price_include == ""
        assert event_dto.schedule == ""
        assert event_dto.participant_commitment == ""
        assert event_dto.line_rules == ""
        assert event_dto.place_rules == ""
    
    def test_get_upcoming_events_mixed_statuses(self, event_service):
        """Test getting upcoming events with mixed statuses"""
        event_service.sheets_service.get_data_from_sheet.return_value = {
            'headers': ['id', 'name', 'start_date', 'start_time', 'event_type', 'price_single', 'price_couple', 'theme', 'max_participants', 'status', 'created_at', 'updated_at', 'main_group_id', 'singles_group_id', 'is_public', 'description', 'location', 'end_date', 'end_time', 'price_include', 'schedule', 'participant_commitment', 'line_rules', 'place_rules', 'balance'],
            'rows': [
                ['event1', 'Active Event 1', '2024-01-01', '18:00', 'workshop', '100', '180', 'Theme 1', '20', 'active', '2024-01-01', '2024-01-01', 'group1', 'singles1', 'true', 'Description 1', 'Location 1', '2024-01-01', '22:00', 'Food included', '18:00-22:00', 'Required', 'Rules 1', 'Place rules 1', '0'],
                ['event2', 'Inactive Event', '2024-01-02', '19:00', 'workshop', '120', '200', 'Theme 2', '25', 'inactive', '2024-01-02', '2024-01-02', 'group2', 'singles2', 'false', 'Description 2', 'Location 2', '2024-01-02', '23:00', 'Food included', '19:00-23:00', 'Required', 'Rules 2', 'Place rules 2', '0'],
                ['event3', 'Active Event 2', '2024-01-03', '20:00', 'workshop', '150', '250', 'Theme 3', '30', 'active', '2024-01-03', '2024-01-03', 'group3', 'singles3', 'true', 'Description 3', 'Location 3', '2024-01-03', '00:00', 'Food included', '20:00-00:00', 'Required', 'Rules 3', 'Place rules 3', '0'],
                ['event4', 'Cancelled Event', '2024-01-04', '21:00', 'workshop', '180', '300', 'Theme 4', '35', 'cancelled', '2024-01-04', '2024-01-04', 'group4', 'singles4', 'false', 'Description 4', 'Location 4', '2024-01-04', '01:00', 'Food included', '21:00-01:00', 'Required', 'Rules 4', 'Place rules 4', '0'],
                ['event5', 'Active Event 3', '2024-01-05', '22:00', 'workshop', '200', '350', 'Theme 5', '40', 'active', '2024-01-05', '2024-01-05', 'group5', 'singles5', 'true', 'Description 5', 'Location 5', '2024-01-05', '02:00', 'Food included', '22:00-02:00', 'Required', 'Rules 5', 'Place rules 5', '0']
            ]
        }
        
        events = event_service.get_upcoming_events()
        
        assert len(events) == 3
        assert all(event.status == "active" for event in events)
        event_names = [event.name for event in events]
        assert "Active Event 1" in event_names
        assert "Active Event 2" in event_names
        assert "Active Event 3" in event_names 