from typing import Optional, Dict, List, Any
from datetime import datetime

from ..config.settings import settings
from ..exceptions import SheetsConnectionException
from ..models.registration import RegistrationData, StepProgress, RegistrationStatus

class SheetsService:
    def __init__(self):
        self.spreadsheet = settings.sheets_service
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id
        self.range_name = settings.google_sheets_range
        
    def _column_index_to_letter(self, col_index: int) -> str:
        """Convert a column index (0-based) to Excel column letter format (A, B, ..., Z, AA, AB, ...)"""
        result = ""
        while col_index >= 0:
            result = chr(ord('A') + (col_index % 26)) + result
            col_index = col_index // 26 - 1
        return result
    
    def get_sheet_data(self) -> Optional[Dict[str, List]]:
        """Fetch all data from the Google Sheets"""
        if not self.spreadsheet:
            raise SheetsConnectionException("Google Sheets service not available")
        
        try:
            result = self.spreadsheet.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
                
            # First row should be headers
            headers = values[0] if values else []
            rows = values[1:] if len(values) > 1 else []
            
            return {'headers': headers, 'rows': rows}
        except Exception as e:
            raise SheetsConnectionException(f"Error reading Google Sheets: {e}")

    def get_column_indices(self, headers: List[str]) -> Dict[str, int]:
        """Get column indices for all important fields from headers"""
        # TODO use a dictionary instead of a list
        column_indices = {}
        for i, header in enumerate(headers):
            if 'Submission ID' in header and 'time' not in header.lower():
                column_indices['submission_id'] = i
            elif 'שם מלא' in header:  # Full name in Hebrew
                column_indices['full_name'] = i
            elif 'מגיע.ה לבד או באיזון' in header:  # Coming alone or in balance
                column_indices['coming_alone_or_balance'] = i
            elif 'שם הפרטנר' in header:  # Partner name in Hebrew
                column_indices['partner_name'] = i
            # Language preference column
            elif 'האם תרצו להמשיך בעברית או באנגלית' in header or 'Language Preference' in header:
                column_indices['language_preference'] = i
            # Returning participant column
            elif 'האם השתתפת בעבר באחד מאירועי Wild Ginger' in header or 'Previous Wild Ginger Participation' in header:
                column_indices['returning_participant'] = i
            # New dedicated status columns
            elif 'Form Complete' in header or 'טופס הושלם' in header:
                column_indices['form_complete'] = i
            elif 'Partner Complete' in header or 'פרטנר הושלם' in header:
                column_indices['partner_complete'] = i
            elif 'Get To Know Complete' in header or 'היכרות הושלמה' in header:
                column_indices['get_to_know_complete'] = i
            elif 'Admin Approved' in header or 'מאושר' in header:
                column_indices['admin_approved'] = i
            elif 'Payment Complete' in header or 'תשלום הושלם' in header:
                column_indices['payment_complete'] = i
            elif 'Group Access' in header or 'גישה לקבוצה' in header:
                column_indices['group_access'] = i
            # Keep the old status column as fallback
            elif 'Status' in header or 'status' in header.lower():
                column_indices['status'] = i
            # New: Telegram User ID column
            elif 'Telegram User Id' in header or 'מזהה משתמש טלגרם' in header:
                column_indices['telegram_user_id'] = i
            # Cancellation tracking columns
            elif 'Cancelled' in header or 'בוטל' in header or 'מבוטל' in header:
                column_indices['cancelled'] = i
            elif 'Cancellation Date' in header or 'תאריך ביטול' in header:
                column_indices['cancellation_date'] = i
            elif 'Cancellation Reason' in header or 'סיבת ביטול' in header:
                column_indices['cancellation_reason'] = i
            elif 'Last Minute Cancellation' in header or 'ביטול ברגע האחרון' in header:
                column_indices['last_minute_cancellation'] = i
            # Get-to-know response column
            elif 'Get To Know Response' in header or 'תשובת היכרות' in header:
                column_indices['get_to_know_response'] = i
            # NEW TASK 1: Check for "paid" column (column J) 
            elif 'paid' in header.lower() or 'שולם' in header.lower():
                column_indices['paid'] = i
        return column_indices

    def _parse_submission_row(self, row: List[str], column_indices: Dict[str, int]) -> Dict[str, Any]:
        """Parse a row from the sheet into our status format"""
        def get_cell_value(key, default=""):
            index = column_indices.get(key)
            if index is not None and index < len(row):
                return row[index]
            return default
        
        def get_boolean_value(key, default=False):
            """Get a boolean value from the sheet, handling various formats"""
            value = get_cell_value(key, "").strip().upper()
            if value in ['TRUE', 'YES', 'כן', '1', 'V', '✓']:
                return True
            elif value in ['FALSE', 'NO', 'לא', '0', '', 'X']:
                return False
            return default
        
        def get_language_preference(response):
            """Determine language preference from form response"""
            if not response:
                return 'en'  # Default to English
            
            response_lower = response.lower().strip()
            if 'עברית' in response_lower or 'hebrew' in response_lower:
                return 'he'
            elif 'אנגלית' in response_lower or 'english' in response_lower:
                return 'en'
            else:
                return 'en'  # Default to English
        
        def parse_multiple_partners(partner_text):
            """Parse multiple partner names from text"""
            if not partner_text:
                return []
            
            # Split by common separators
            separators = [',', '&', '+', 'ו', ' ו ', 'and', ' and ', " או "]
            partners = [partner_text.strip()]
            
            for separator in separators:
                new_partners = []
                for partner in partners:
                    if separator in partner:
                        new_partners.extend([p.strip() for p in partner.split(separator) if p.strip()])
                    else:
                        new_partners.append(partner)
                partners = new_partners
            
            return [p for p in partners if p and p.strip()]
        
        # Extract basic information
        submission_id = get_cell_value('submission_id')
        full_name = get_cell_value('full_name')
        telegram_user_id = get_cell_value('telegram_user_id')
        
        # Get language preference
        language_response = get_cell_value('language_preference')
        language = get_language_preference(language_response)
        
        # Get status columns
        form_complete = get_boolean_value('form_complete', False)
        partner_complete = get_boolean_value('partner_complete', False)
        get_to_know_complete = get_boolean_value('get_to_know_complete', False)
        admin_approved = get_boolean_value('admin_approved', False)
        payment_complete = get_boolean_value('payment_complete', False)
        group_access = get_boolean_value('group_access', False)
        
        # Get cancellation info
        cancelled = get_boolean_value('cancelled', False)
        cancellation_reason = get_cell_value('cancellation_reason')
        
        # Get returning participant status
        returning_participant = get_boolean_value('returning_participant', False)
        
        # Handle partner information
        partner_names = []
        partner_status = {}
        partner_alias = None
        
        if not partner_complete:
            coming_alone = get_cell_value('coming_alone_or_balance')
            partner_name_text = get_cell_value('partner_name')
            
            if partner_name_text and 'לבד' not in coming_alone:
                partner_names = parse_multiple_partners(partner_name_text)
                partner_alias = partner_name_text if len(partner_names) == 1 else None
                
                partner_status = {
                    'all_registered': False,
                    'registered_partners': [],
                    'missing_partners': partner_names
                }
            else:
                partner_complete = True
        else:
            partner_name_text = get_cell_value('partner_name')
            if partner_name_text:
                partner_names = parse_multiple_partners(partner_name_text)
                partner_alias = partner_name_text if len(partner_names) == 1 else None
        
        # Check if returning participant should auto-complete get-to-know
        if returning_participant and not get_to_know_complete:
            get_to_know_complete = True
        
        # Build the result dictionary
        result = {
            'submission_id': submission_id,
            'alias': full_name,
            'telegram_user_id': telegram_user_id,
            'language': language,
            'form': form_complete,
            'partner': partner_complete,
            'get_to_know': get_to_know_complete,
            'approved': admin_approved,
            'paid': payment_complete,
            'group_open': group_access,
            'cancelled': cancelled,
            'cancellation_reason': cancellation_reason,
            'is_returning_participant': returning_participant,
            'partner_names': partner_names,
            'partner_alias': partner_alias,
            'partner_status': partner_status
        }
        
        return result

    def find_submission_by_field(self, field_name: str, field_value: str) -> Optional[Dict[str, Any]]:
        """Generic function to find a submission by any field value"""
        sheet_data = self.get_sheet_data()
        if not sheet_data:
            return None
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        
        column_indices = self.get_column_indices(headers)
        
        # Look for the field value in the rows
        field_column_index = column_indices.get(field_name)
        if field_column_index is None:
            return None
        
        for row in rows:
            if len(row) > field_column_index:
                if row[field_column_index] == field_value:
                    return self._parse_submission_row(row, column_indices)
        
        return None

    async def find_submission_by_id(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Find a submission by its ID in the Google Sheets"""
        return self.find_submission_by_field('submission_id', submission_id)

    async def find_submission_by_telegram_id(self, telegram_user_id: str) -> Optional[Dict[str, Any]]:
        """Find a submission by Telegram User ID in the Google Sheets"""
        return self.find_submission_by_field('telegram_user_id', telegram_user_id)

    def _update_cell(self, submission_id: str, column_key: str, value: str) -> bool:
        """Generic method to update a single cell"""
        if not self.spreadsheet:
            print("⚠️  Google Sheets not available")
            return False
        
        try:
            sheet_data = self.get_sheet_data()
            if not sheet_data:
                return False
            
            headers = sheet_data['headers']
            rows = sheet_data['rows']
            
            column_indices = self.get_column_indices(headers)
            
            submission_id_col = column_indices.get('submission_id')
            target_col = column_indices.get(column_key)
            
            if submission_id_col is None or target_col is None:
                print(f"❌ Could not find required columns in Google Sheets")
                return False
            
            # Find the row with the matching submission ID
            for row_index, row in enumerate(rows):
                if len(row) > submission_id_col and row[submission_id_col] == submission_id:
                    sheet_row = row_index + 4  # Adjust for header row and 0-based indexing
                    
                    col_letter = self._column_index_to_letter(target_col)
                    range_name = f"managed!{col_letter}{sheet_row}"
                    
                    result = self.spreadsheet.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body={'values': [[value]]}
                    ).execute()
                    
                    print(f"✅ Updated {column_key} to {value} for submission {submission_id}")
                    return True
            
            print(f"❌ Could not find submission {submission_id} in Google Sheets")
            return False
            
        except Exception as e:
            print(f"❌ Error updating {column_key}: {e}")
            return False

    async def update_telegram_user_id(self, submission_id: str, telegram_user_id: str) -> bool:
        """Update the Telegram User ID for a specific submission in Google Sheets"""
        return self._update_cell(submission_id, 'telegram_user_id', telegram_user_id)

    async def update_step_status(self, submission_id: str, step: str, complete: bool) -> bool:
        """Update completion status of a registration step"""
        step_column_mapping = {
            'form': 'form_complete',
            'partner': 'partner_complete',
            'get_to_know': 'get_to_know_complete',
            'approved': 'admin_approved',
            'paid': 'payment_complete',
            'group_access': 'group_access'
        }
        
        column_key = step_column_mapping.get(step)
        if not column_key:
            print(f"❌ Unknown step: {step}")
            return False
        
        value = "TRUE" if complete else "FALSE"
        return self._update_cell(submission_id, column_key, value)

    async def get_all_registrations(self, event_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all registrations, optionally filtered by event"""
        sheet_data = self.get_sheet_data()
        if not sheet_data:
            return []
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = self.get_column_indices(headers)
        
        registrations = []
        for row in rows:
            if row:  # Skip empty rows
                registration = self._parse_submission_row(row, column_indices)
                if registration and registration.get('submission_id'):
                    registrations.append(registration)
        
        return registrations

    async def update_admin_approval(self, submission_id: str, approved: bool, notes: str = "") -> bool:
        """Update admin approval status"""
        return await self.update_step_status(submission_id, 'approved', approved)

    async def store_get_to_know_response(self, submission_id: str, response: str) -> bool:
        """Store get-to-know conversation response"""
        return self._update_cell(submission_id, 'get_to_know_response', response)

    async def update_cancellation_status(self, submission_id: str, cancelled: bool = True, reason: str = "", is_last_minute: bool = False) -> bool:
        """Update cancellation status with reason and timing information"""
        if not self.spreadsheet:
            print("⚠️  Google Sheets not available - cannot update cancellation status")
            return False
        
        try:
            # Update multiple fields for cancellation
            updates = [
                ('cancelled', "TRUE" if cancelled else "FALSE"),
                ('cancellation_reason', reason),
                ('last_minute_cancellation', "TRUE" if is_last_minute else "FALSE")
            ]
            
            if cancelled:
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updates.append(('cancellation_date', current_date))
            
            # Execute all updates
            success = True
            for column_key, value in updates:
                if not self._update_cell(submission_id, column_key, value):
                    success = False
            
            if success:
                print(f"✅ Updated cancellation status for submission {submission_id}")
                if reason:
                    print(f"   Reason: {reason}")
                if is_last_minute:
                    print(f"   ⚠️ Last minute cancellation noted")
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating cancellation status: {e}")
            return False 