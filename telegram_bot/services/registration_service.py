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