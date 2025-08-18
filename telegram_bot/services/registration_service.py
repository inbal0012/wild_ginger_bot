from typing import Optional, Dict, Any

from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.models.registration import CreateRegistrationDTO, RegistrationStatus

class RegistrationService:
    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.headers = self.sheets_service.headers["Registrations"]

    # def find_registration_by_id(self, telegram_user_id: str) -> Optional[Dict[str, Any]]:
    #     sheet_data = self.sheets_service.get_data_from_sheet("Registrations")
        
    #     if not sheet_data:
    #         return None
        
    #     headers = sheet_data['headers']
    #     rows = sheet_data['rows']
        
    #     telegram_user_id_col = self.headers['telegram_user_id']
        
    #     for i, row in enumerate(rows):            
    #         if row and row[telegram_user_id_col] == str(telegram_user_id):
    #             return row
        
    #     return None

    async def create_new_registration(self, registration: CreateRegistrationDTO):
        try:
            # Get the next empty row in the Registrations sheet
            sheet_data = self.sheets_service.get_data_from_sheet("Registrations")
            if not sheet_data:
                return False

            # Create a new row with empty values matching number of columns
            new_row = [""] * len(sheet_data['headers'])

            # Fill in the provided registration data
            new_row[self.headers['registration_id']] = registration.id
            new_row[self.headers['user_id']] = registration.user_id
            new_row[self.headers['event_id']] = registration.event_id
            if isinstance(registration.status, RegistrationStatus):
                new_row[self.headers['status']] = registration.status.value
            else:
                new_row[self.headers['status']] = registration.status

            # Add the row to the sheet
            result = await self.sheets_service.append_row("Registrations", new_row)

            return result
        except Exception as e:
            print(f"Error creating new registration: {e}")
            return False
        
    def get_registration_id_by_user_id(self, user_id: str, event_id: str) -> Optional[str]:
        sheet_data = self.sheets_service.get_data_from_sheet("Registrations")
        if not sheet_data:
            return None
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        user_id_col = self.headers['user_id']
        event_id_col = self.headers['event_id']
        for row in rows:
            if row and row[user_id_col] == str(user_id) and row[event_id_col] == str(event_id):
                return row[self.headers['registration_id']]
        return None
    
    def set_ginger_first_try(self, registration_id: str, value: bool):
        """Set ginger first try for a user."""
        self.sheets_service.update_cell(registration_id, 'registration_id', "Registrations", 'ginger_first_try', value)
    
    async def update_registration_status(self, registration_id: str, status: RegistrationStatus) -> bool:
        """Update registration status."""
        try:
            if isinstance(status, RegistrationStatus):
                status_value = status.value
            else:
                status_value = status
            
            result = self.sheets_service.update_cell(
                registration_id, 
                'registration_id', 
                "Registrations", 
                'status', 
                status_value
            )
            return result
        except Exception as e:
            print(f"Error updating registration status: {e}")
            return False