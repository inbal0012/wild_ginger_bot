from typing import Optional, Dict, Any, List
from datetime import datetime

from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.models.event import CreateEventDTO, EventDTO


class EventService:
    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.headers = self.sheets_service.headers["Events"]

    def get_upcoming_events(self) -> List[EventDTO]:
        sheet_data = self.sheets_service.get_data_from_sheet("Events")
        if not sheet_data:
            return []
        
        # get events with status "active"
        active_events = [self.row_to_eventDTO(row) for row in sheet_data['rows'] if row[self.headers['status']] == "active"]
        return active_events

    def row_to_eventDTO(self, row: Dict[str, Any]) -> EventDTO:
        # TODO make {name, event_type, description, location, schedule, price_include, participant_commitment, line_rules, place_rules } translatable using Text class
        return EventDTO(
            id=row[self.headers['id']],
            name=row[self.headers['name']],
            start_date=row[self.headers['start_date']],
            start_time=row[self.headers['start_time']],
            event_type=row[self.headers['event_type']],
            price_single=row[self.headers['price_single']],
            price_couple=row[self.headers['price_couple']],
            theme=row[self.headers['theme']],
            max_participants=row[self.headers['max_participants']],
            status=row[self.headers['status']],
            created_at=row[self.headers['created_at']],
            updated_at=row[self.headers['updated_at']],
            main_group_id=row[self.headers['main_group_id']],
            singles_group_id=row[self.headers['singles_group_id']],
            is_public=row[self.headers['is_public']],
            description=row[self.headers['description']],
            location=row[self.headers['location']],
            end_date=row[self.headers['end_date']],
            end_time=row[self.headers['end_time']],
            price_include=row[self.headers['price_include']],
            schedule=row[self.headers['schedule']],
            participant_commitment=row[self.headers['participant_commitment']],
            line_rules=row[self.headers['line_rules']],
            place_rules=row[self.headers['place_rules']],
            balance=row[self.headers['balance']]
        )

    def get_event_by_id(self, event_id: str) -> Optional[EventDTO]:
        sheet_data = self.sheets_service.get_data_from_sheet("Events")
        
        if not sheet_data:
            return None
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        event_id_col = self.sheets_service.headers["Events"]['id']
        
        for i, row in enumerate(rows):            
            if row and row[event_id_col] == str(event_id):
                return self.row_to_eventDTO(row)
        
        return None

    async def create_new_event(self, event: CreateEventDTO):
        # Get the next empty row in the Events sheet
        sheet_data = self.sheets_service.get_data_from_sheet("Events")
        if not sheet_data:
            return False
            
        # Create a new row with empty values matching number of columns
        new_row = [""] * len(sheet_data['headers'])
    
        # Fill in the provided user data
        new_row[self.headers['name']] = event.name
        new_row[self.headers['start_date']] = event.start_date
        new_row[self.headers['start_time']] = event.start_time
        new_row[self.headers['event_type']] = event.event_type
        new_row[self.headers['price_single']] = event.price_single
        new_row[self.headers['price_couple']] = event.price_couple
        new_row[self.headers['status']] = event.status
        new_row[self.headers['created_at']] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add the row to the sheet
        result = await self.sheets_service.append_row("Events", new_row)
        
        return result
        
    def get_event_type(self, event_id: str) -> str:
        event = self.get_event_by_id(event_id)
        if event:
            return event.event_type
        return None
    
    def get_event_name_by_id(self, event_id: str) -> str:
        event = self.get_event_by_id(event_id)
        if event:
            return event.name
        return None
    