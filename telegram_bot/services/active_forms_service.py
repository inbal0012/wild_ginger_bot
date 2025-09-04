"""
ActiveFormsService - Service for managing active forms.
Handles form storage, retrieval, and management operations.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base_service import BaseService
from .sheets_service import SheetsService
from ..models.form_state import FormState


class ActiveFormsService(BaseService):
    """
    Service for managing active forms.
    Handles form storage, retrieval, and management operations.
    """
    
    def __init__(self, sheets_service: SheetsService):
        """Initialize the active forms service."""
        super().__init__()
        self.sheets_service = sheets_service
        self.active_forms: Dict[str, FormState] = {}
        self._load_active_forms()
    
    def _load_active_forms(self) -> None:
        """Load active forms from Google Sheets."""
        try:
            sheet_data = self.sheets_service.get_data_from_sheet("ActiveForms")
            if not sheet_data or 'rows' not in sheet_data:
                self.log_info("No active forms sheet data found, starting with empty forms")
                return
            
            headers = sheet_data['headers']
            rows = sheet_data['rows']
            
            # Find column indices
            user_id_col = headers.index('user_id') if 'user_id' in headers else 0
            form_data_col = headers.index('form_data') if 'form_data' in headers else 1
            
            for row in rows:
                if len(row) > max(user_id_col, form_data_col) and row[user_id_col] and row[form_data_col]:
                    try:
                        # Parse the JSON form data
                        form_dict = json.loads(row[form_data_col])
                        self.active_forms[row[user_id_col]] = FormState.from_dict(form_dict)
                    except Exception as e:
                        self.log_error(f"Error loading form state for user {row[user_id_col]}: {e}")
                        continue
            
            self.log_info(f"Loaded {len(self.active_forms)} active forms from Google Sheets")
            
        except Exception as e:
            self.log_error(f"Error loading active forms from Google Sheets: {e}")
    
    async def save_active_forms(self, user_id: str, form_state: FormState) -> bool:
        """Save a specific form to Google Sheets."""
        try:
            # Update in-memory cache
            self.active_forms[user_id] = form_state
            
            # Get existing sheet data
            sheet_data = self.sheets_service.get_data_from_sheet("ActiveForms")
                        
            headers = sheet_data['headers']
            existing_rows = sheet_data['rows']
            
            # Find column indices
            user_id_col = headers.index('user_id') 
            form_data_col = headers.index('form_data') 
            created_at_col = headers.index('created_at')
            updated_at_col = headers.index('updated_at')
            
            # Create a map of existing user IDs to row indices
            user_to_row = {}
            for i, row in enumerate(existing_rows):
                if len(row) > user_id_col and row[user_id_col]:
                    user_to_row[row[user_id_col]] = i
            
            # Convert form state to dictionary and JSON
            form_dict = form_state.to_dict()
            form_json = json.dumps(form_dict, default=str)
            current_time = datetime.now().isoformat()
            
            if user_id in user_to_row:
                # Update existing row
                row_index = user_to_row[user_id]
                # Ensure the row has enough columns
                while len(existing_rows[row_index]) < len(headers):
                    existing_rows[row_index].append('')
                existing_rows[row_index][form_data_col] = form_json
                existing_rows[row_index][updated_at_col] = current_time
                success = self.sheets_service.update_range(f"ActiveForms!A{row_index + 2}:D{row_index + 2}", existing_rows[row_index])
            else:
                # Add new row
                new_row = [''] * len(headers)
                new_row[user_id_col] = user_id
                new_row[form_data_col] = form_json
                new_row[created_at_col] = current_time
                new_row[updated_at_col] = current_time
                success = await self.sheets_service.append_row("ActiveForms", new_row)
            
            if success:
                self.log_info(f"Saved form for user {user_id} to Google Sheets")
            else:
                self.log_error(f"Failed to save form for user {user_id} to Google Sheets")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error saving form for user {user_id} to Google Sheets: {e}")
            return False
    
    async def save_active_form(self, user_id: str, form_state: FormState) -> bool:
        """Save a specific form to Google Sheets."""
        try:
            # Update in-memory cache
            self.active_forms[user_id] = form_state
            
            # Get existing sheet data
            sheet_data = self.sheets_service.get_data_from_sheet("ActiveForms")
                        
            headers = sheet_data['headers']
            existing_rows = sheet_data['rows']
            
            # Find column indices
            user_id_col = headers.index('user_id') 
            form_data_col = headers.index('form_data') 
            created_at_col = headers.index('created_at')
            updated_at_col = headers.index('updated_at')
            
            # Find the row index for the user_id
            row_index = None
            for i, row in enumerate(existing_rows):
                if len(row) > user_id_col and row[user_id_col] == user_id:
                    row_index = i
                    break
            
            # Convert form state to dictionary and JSON
            form_dict = form_state.to_dict()
            form_json = json.dumps(form_dict, default=str)
            current_time = datetime.now().isoformat()
            
            if row_index is None:
                self.log_error(f"No row found for user {user_id}")
                return await self.sheets_service.append_row("ActiveForms", [user_id, form_json, current_time, current_time])
            
            # Update the row with the new form data
            existing_rows[row_index][form_data_col] = form_json
            existing_rows[row_index][updated_at_col] = current_time
            
            success = self.sheets_service.update_range(f"ActiveForms!A{row_index + 2}:D{row_index + 2}", existing_rows[row_index])            
            
            if success:
                self.log_info(f"Saved form for user {user_id} to Google Sheets")
            else:
                self.log_error(f"Failed to save form for user {user_id} to Google Sheets")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error saving form for user {user_id} to Google Sheets: {e}")
            return False
    
    async def save_all_active_forms(self) -> bool:
        """Save all active forms to Google Sheets."""
        try:
            success = True
            for user_id, form_state in self.active_forms.items():
                if not await self.save_active_forms(user_id, form_state):
                    success = False
            
            if success:
                self.log_info(f"Saved all {len(self.active_forms)} active forms to Google Sheets")
            else:
                self.log_error("Some forms failed to save")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error saving all active forms: {e}")
            return False
    
    def get_active_forms(self) -> Dict[str, FormState]:
        """Get all active forms."""
        return self.active_forms.copy()
    
    def get_form_by_user_id(self, user_id: str) -> Optional[FormState]:
        """Get a specific form by user ID."""
        return self.active_forms.get(str(user_id))
    
    async def add_form(self, user_id: str, form_state: FormState) -> None:
        """Add a new form to the service."""
        self.active_forms[user_id] = form_state
        await self.save_active_form(user_id, form_state)
        self.log_info(f"Added form for user {user_id}")
    
    async def update_form(self, user_id: str, form_state: FormState) -> None:
        """Update an existing form."""
        if user_id in self.active_forms:
            self.active_forms[user_id] = form_state
            await self.save_active_form(user_id, form_state)
            self.log_info(f"Updated form for user {user_id}")
        else:
            self.log_error(f"No form found for user {user_id} to update")
    
    def remove_form(self, user_id: str) -> bool:
        """Remove a form from the service and Google Sheets."""
        try:
            if user_id not in self.active_forms:
                self.log_info(f"No form found for user {user_id} to remove")
                return True
            
            # Remove from memory
            form_state = self.active_forms.pop(user_id)
            
            # Remove from Google Sheets
            sheet_data = self.sheets_service.get_data_from_sheet("ActiveForms")
            if not sheet_data or 'rows' not in sheet_data:
                self.log_info("No ActiveForms sheet found, nothing to remove")
                return True
            
            headers = sheet_data['headers']
            rows = sheet_data['rows']
            
            # Find user_id column index
            user_id_col = headers.index('user_id') if 'user_id' in headers else 0
            
            # Find and remove the row with this user_id
            for i, row in enumerate(rows):
                if len(row) > user_id_col and row[user_id_col] == user_id:
                    success = self.sheets_service.delete_row("ActiveForms", i)
                    break
            
            if success:
                self.log_info(f"Removed form for user {user_id} from Google Sheets")
            else:
                self.log_error(f"Failed to remove form for user {user_id} from Google Sheets")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error removing form for user {user_id}: {e}")
            return False
    
    def ensure_sheet_exists(self) -> None:
        """Ensure the ActiveForms sheet exists with proper structure."""
        try:
            sheet_data = self.sheets_service.get_data_from_sheet("ActiveForms")
            if not sheet_data or 'headers' not in sheet_data:
                # Create the sheet with proper headers
                headers = ['user_id', 'form_data', 'created_at', 'updated_at']
                initial_data = {
                    'headers': headers,
                    'rows': []
                }
                success = self.sheets_service.update_sheet("ActiveForms", initial_data)
                if success:
                    self.log_info("Created ActiveForms sheet with proper structure")
                else:
                    self.log_error("Failed to create ActiveForms sheet")
        except Exception as e:
            self.log_error(f"Error ensuring ActiveForms sheet exists: {e}")
    
    def get_forms_count(self) -> int:
        """Get the total number of active forms."""
        return len(self.active_forms)
    
    def get_completed_forms_count(self) -> int:
        """Get the number of completed forms."""
        return sum(1 for form in self.active_forms.values() if form.completed)
    
    def get_active_forms_count(self) -> int:
        """Get the number of active (incomplete) forms."""
        return sum(1 for form in self.active_forms.values() if not form.completed)
    
    def get_forms_by_language(self, language: str) -> List[FormState]:
        """Get all forms for a specific language."""
        return [form for form in self.active_forms.values() if form.language == language]
    
    def get_forms_by_event(self, event_id: str) -> List[FormState]:
        """Get all forms for a specific event."""
        return [form for form in self.active_forms.values() if form.event_id == event_id]
    
    async def update_answer(self, user_id: str, question_field: str, answer: Any) -> None:
        """Update an answer for a specific user."""
        try:
            if user_id in self.active_forms:
                self.active_forms[user_id].update_answer(question_field, answer)
                await self.save_active_form(user_id, self.active_forms[user_id])
                self.log_info(f"Updated answer for user {user_id} for question {question_field}")
            else:
                self.log_error(f"No form found for user {user_id} to update answer")
        except Exception as e:
            self.log_error(f"Error updating answer for user {user_id} for question {question_field}: {e}")
    
    def cleanup_completed_forms(self) -> int:
        """Remove all completed forms and return count of removed forms."""
        completed_user_ids = [
            user_id for user_id, form_state in self.active_forms.items() 
            if form_state.completed
        ]
        
        removed_count = 0
        for user_id in completed_user_ids:
            if self.remove_form(user_id):
                removed_count += 1
        
        self.log_info(f"Cleaned up {removed_count} completed forms")
        return removed_count 