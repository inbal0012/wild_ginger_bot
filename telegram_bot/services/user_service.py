from typing import Optional, Dict, Any

from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.models.user import CreateUserFromTelegramDTO


class UserService:
    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.headers = self.sheets_service.parse_sheet_headers("Users")

    def get_user_by_telegram_id(self, telegram_user_id: str) -> Optional[Dict[str, Any]]:
        sheet_data = self.sheets_service.get_data_from_sheet("Users")
        
        if not sheet_data:
            return None
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        telegram_user_id_col = self.sheets_service.user_headers['telegram_user_id']
        
        for i, row in enumerate(rows):            
            if row and row[telegram_user_id_col] == str(telegram_user_id):
                return row
        
        return None

    async def create_new_user(self, user: CreateUserFromTelegramDTO):
        # Get the next empty row in the Users sheet
        sheet_data = self.sheets_service.get_data_from_sheet("Users")
        if not sheet_data:
            return False
            
        # Create a new row with empty values matching number of columns
        new_row = [""] * len(sheet_data['headers'])
        
        # Fill in the provided user data
        new_row[self.headers['telegram_user_id']] = user.telegram_user_id
        new_row[self.headers['telegram']] = user.telegram_username
        new_row[self.headers['full_name']] = user.full_name
        new_row[self.headers['language']] = user.language
        
        # Add the row to the sheet
        result = await self.sheets_service.append_row("Users", new_row)
        
        return result
        