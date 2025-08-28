from typing import Optional, Dict, Any, List

from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.models.registration import CreateRegistrationDTO, RegistrationStatus, Status, RegistrationData

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
        
    async def finish_form_flow(self, registration_id: str, status: Status):
        await self.update_registration_by_registration_id(registration_id, "form_complete", True)
        await self.update_registration_by_registration_id(registration_id, "status", status.value)
    
    async def update_registration_by_registration_id(self, registration_id: str, field: str, value: str) -> bool:
        """Update registration status."""
        try:
            result = self.sheets_service.update_cell(
                registration_id, 
                'registration_id', 
                "Registrations", 
                field, 
                value
            )
            return result
        except Exception as e:
            print(f"Error updating registration status: {e}")
            return False
        
    async def update_registration_by_user_event(self, user_id: str, event_id: str, field: str, value: str) -> bool:
        """Update registration status."""
        registration_id = self.get_registration_id_by_user_id(user_id, event_id)
        if not registration_id:
            return False
        
        return await self.update_registration_by_registration_id(registration_id, field, value)
        
    async def get_all_registrations_for_event(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all registrations for an event."""
        sheet_data = self.sheets_service.get_data_from_sheet("Registrations")
        if not sheet_data:
            return []
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        event_id_col = self.headers['event_id']
        
        registrations = []
        for row in rows:
            if row and row[event_id_col] == str(event_id):
                registration_data = {}
                for i, header in enumerate(headers):
                    if i < len(row) and row[i] is not None:
                        registration_data[header] = row[i]
                registrations.append(registration_data)
        return registrations
    
    async def get_all_registrations_for_user(self, user_id: str) -> List[RegistrationData]:
        """Get all registrations for a user."""
        sheet_data = self.sheets_service.get_data_from_sheet("Registrations")
        if not sheet_data:
            return []
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        user_id_col = self.headers['user_id']
        
        registrations = []
        for row in rows:
            if row and row[user_id_col] == str(user_id):
                registrations.append(self.dict_to_registration_data(row))
        return registrations
    
    def dict_to_registration_data(self, row: Dict[str, Any]) -> RegistrationData:
        return RegistrationData(
            id=row[self.headers['registration_id']],
            event_id=row[self.headers['event_id']],
            user_id=row[self.headers['user_id']],
            status=row[self.headers['status']],
            partner_telegram_link=row[self.headers['partner_telegram_link']],
            payment_status=row[self.headers['payment_status']],
            payment_method=row[self.headers['payment_method']],
            registration_date=row[self.headers['registration_date']],
            payment_date=row[self.headers['payment_date']],
            partner_or_single=row[self.headers['partner_or_single']],
            intro_opt_in=row[self.headers['intro_opt_in']],
            intro_text=row[self.headers['intro_text']],
            intro_posted_at=row[self.headers['intro_posted_at']],
            created_at=row[self.headers['created_at']],
            updated_at=row[self.headers['updated_at']],
            would_you_like_to_register=row[self.headers['would_you_like_to_register']],
            last_sti_test=row[self.headers['last_sti_test']],
            bdsm_declaration=row[self.headers['bdsm_declaration']],
            is_play_with_partner_only=row[self.headers['is_play_with_partner_only']],
            desired_play_partners=row[self.headers['desired_play_partners']],
            contact_type=row[self.headers['contact_type']],
            contact_type_other=row[self.headers['contact_type_other']],
            share_bdsm_interests=row[self.headers['share_bdsm_interests']],
            alcohol_in_event=row[self.headers['alcohol_in_event']],
            agree_participant_commitment=row[self.headers['agree_participant_commitment']],
            enthusiastic_verbal_consent_commitment=row[self.headers['enthusiastic_verbal_consent_commitment']],
            agree_line_rules=row[self.headers['agree_line_rules']],
            wants_to_helper=row[self.headers['wants_to_helper']],
            helper_shifts=row[self.headers['helper_shifts']],
            wants_to_DM=row[self.headers['wants_to_DM']],
            DM_shifts=row[self.headers['DM_shifts']],
            get_to_know_status=row[self.headers['get_to_know_status']],
            group_status=row[self.headers['group_status']],
            arrived=row[self.headers['arrived']],
            ginger_first_try=row[self.headers['ginger_first_try']],
            form_complete=row[self.headers['form_complete']],
        )