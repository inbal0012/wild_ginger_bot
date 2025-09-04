"""
PollDataService - Manages poll data storage and retrieval from Google Sheets.
Handles creating, updating, deleting, and querying poll information.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from .base_service import BaseService
from .sheets_service import SheetsService

from telegram import PollAnswer

class PollDataService(BaseService):
    """
    Service for managing poll data in Google Sheets.
    Handles CRUD operations for polls and their associated data.
    """
    
    def __init__(self, sheets_service: SheetsService):
        """Initialize the poll data service."""
        super().__init__()
        self.sheets_service = sheets_service
        self.sheet_name = "PollData"
        self._ensure_poll_data_sheet_exists()
    
    def _ensure_poll_data_sheet_exists(self) -> None:
        """Ensure the PollData sheet exists with proper structure."""
        try:
            sheet_data = self.sheets_service.get_data_from_sheet(self.sheet_name)
            if not sheet_data or 'headers' not in sheet_data or not sheet_data['headers']:
                # Create the sheet with proper headers
                headers = ['poll_id', 'poll_data', 'created_at', 'updated_at']
                initial_data = {
                    'headers': headers,
                    'rows': []
                }
                success = self.sheets_service.update_sheet(self.sheet_name, initial_data)
                if success:
                    self.log_info("Created PollData sheet with proper structure")
                else:
                    self.log_error("Failed to create PollData sheet")
        except Exception as e:
            self.log_error(f"Error ensuring PollData sheet exists: {e}")
    
    async def save_single_poll(self, poll_id: str, poll_info: Dict[str, Any]) -> bool:
        """
        Save a single poll to Google Sheets efficiently.
        
        Args:
            poll_id: Unique identifier for the poll
            poll_info: Poll information dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Get existing sheet data
            sheet_data = self.sheets_service.get_data_from_sheet(self.sheet_name)
            
            headers = sheet_data['headers']
            existing_rows = sheet_data['rows']
            
            # Find column indices
            poll_id_col = headers.index('poll_id') 
            poll_data_col = headers.index('poll_data') 
            created_at_col = headers.index('created_at') 
            updated_at_col = headers.index('updated_at') 
            
            # Find existing row for this poll
            existing_row_index = None
            for i, row in enumerate(existing_rows):
                if len(row) > poll_id_col and row[poll_id_col] == poll_id:
                    existing_row_index = i
                    break
            
            poll_json = json.dumps(poll_info, default=str)
            current_time = datetime.now().isoformat()
            
            if existing_row_index is not None:
                # Update existing row
                row = existing_rows[existing_row_index]
                # Ensure the row has enough columns
                while len(row) < len(headers):
                    row.append('')
                row[poll_data_col] = poll_json
                row[updated_at_col] = current_time
                success = self.sheets_service.update_range(f"{self.sheet_name}!A{existing_row_index + 2}:D{existing_row_index + 2}", row)
                if success:
                    self.log_info(f"Updated poll {poll_id} in Google Sheets")
                else:
                    self.log_error(f"Failed to update poll {poll_id} in Google Sheets")
            else:
                # Add new row
                new_row = [''] * len(headers)
                new_row[poll_id_col] = poll_id
                new_row[poll_data_col] = poll_json
                new_row[created_at_col] = current_time
                new_row[updated_at_col] = current_time
                success = await self.sheets_service.append_row(self.sheet_name, new_row)
                if success:
                    self.log_info(f"Added new poll {poll_id} to Google Sheets")
                else:
                    self.log_error(f"Failed to add new poll {poll_id} to Google Sheets")
            return success
            # Save back to sheets
        except Exception as e:
            self.log_error(f"Error saving poll {poll_id} to Google Sheets: {e}")
            return False

    def save_multiple_polls(self, poll_data: Dict[str, Any]) -> bool:
        """
        Save multiple poll data entries to Google Sheets efficiently.
        Note: For single polls, use save_single_poll() for better performance.
        
        Args:
            poll_data: Dictionary mapping poll_id to poll information
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Get existing sheet data
            sheet_data = self.sheets_service.get_data_from_sheet(self.sheet_name)
            
            # Prepare headers if sheet doesn't exist
            if not sheet_data or 'headers' not in sheet_data or not sheet_data['headers']:
                headers = ['poll_id', 'poll_data', 'created_at', 'updated_at']
                sheet_data = {'headers': headers, 'rows': []}
            
            headers = sheet_data['headers']
            existing_rows = sheet_data['rows']
            
            # Find column indices
            poll_id_col = headers.index('poll_id') if 'poll_id' in headers else 0
            poll_data_col = headers.index('poll_data') if 'poll_data' in headers else 1
            created_at_col = headers.index('created_at') if 'created_at' in headers else 2
            updated_at_col = headers.index('updated_at') if 'updated_at' in headers else 3
            
            # Create a map of existing poll IDs to row indices
            poll_to_row = {}
            for i, row in enumerate(existing_rows):
                if len(row) > poll_id_col and row[poll_id_col]:
                    poll_to_row[row[poll_id_col]] = i
            
            # Update or add poll data
            for poll_id, poll_info in poll_data.items():
                poll_json = json.dumps(poll_info, default=str)
                current_time = datetime.now().isoformat()
                
                if poll_id in poll_to_row:
                    # Update existing row
                    row_index = poll_to_row[poll_id]
                    # Ensure the row has enough columns
                    while len(existing_rows[row_index]) < len(headers):
                        existing_rows[row_index].append('')
                    existing_rows[row_index][poll_data_col] = poll_json
                    existing_rows[row_index][updated_at_col] = current_time
                else:
                    # Add new row
                    new_row = [''] * len(headers)
                    new_row[poll_id_col] = poll_id
                    new_row[poll_data_col] = poll_json
                    new_row[created_at_col] = current_time
                    new_row[updated_at_col] = current_time
                    existing_rows.append(new_row)
            
            # Save back to sheets
            success = self.sheets_service.update_sheet(self.sheet_name, sheet_data)
            if success:
                self.log_info(f"Saved {len(poll_data)} poll data entries to Google Sheets")
            return success
            
        except Exception as e:
            self.log_error(f"Error saving poll data to Google Sheets: {e}")
            return False

    # Legacy method - kept for backward compatibility
    def save_poll_data(self, poll_data: Dict[str, Any]) -> bool:
        """
        Legacy method: Save multiple poll data entries to Google Sheets.
        Note: This method is deprecated. Use save_single_poll() for single polls
        or save_multiple_polls() for multiple polls for better performance.
        
        Args:
            poll_data: Dictionary mapping poll_id to poll information
            
        Returns:
            True if saved successfully, False otherwise
        """
        return self.save_multiple_polls(poll_data)
    
    def load_poll_data(self) -> Dict[str, Any]:
        """
        Load all poll data from Google Sheets.
        
        Returns:
            Dictionary mapping poll_id to poll information
        """
        try:
            sheet_data = self.sheets_service.get_data_from_sheet(self.sheet_name)
            poll_data = {}
            
            if not sheet_data or 'rows' not in sheet_data:
                self.log_info("No poll data sheet found, returning empty dict")
                return {}
            
            headers = sheet_data['headers']
            rows = sheet_data['rows']
            
            # Find column indices
            poll_id_col = headers.index('poll_id') if 'poll_id' in headers else 0
            poll_data_col = headers.index('poll_data') if 'poll_data' in headers else 1
            
            for row in rows:
                if len(row) > max(poll_id_col, poll_data_col) and row[poll_id_col] and row[poll_data_col]:
                    try:
                        # Parse the JSON poll data
                        poll_info = json.loads(row[poll_data_col])
                        poll_data[row[poll_id_col]] = poll_info
                    except Exception as e:
                        self.log_error(f"Error loading poll data for poll {row[poll_id_col]}: {e}")
                        continue
            
            self.log_info(f"Loaded {len(poll_data)} poll data entries from Google Sheets")
            return poll_data
            
        except Exception as e:
            self.log_error(f"Error loading poll data from Google Sheets: {e}")
            return {}
    
    def get_poll_by_id(self, poll_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific poll by ID from Google Sheets.
        
        Args:
            poll_id: Unique identifier for the poll
            
        Returns:
            Poll information dictionary or None if not found
        """
        try:
            sheet_data = self.sheets_service.get_data_from_sheet(self.sheet_name)
            if not sheet_data or 'rows' not in sheet_data:
                return None
            
            headers = sheet_data['headers']
            rows = sheet_data['rows']
            
            # Find column indices
            poll_id_col = headers.index('poll_id') if 'poll_id' in headers else 0
            poll_data_col = headers.index('poll_data') if 'poll_data' in headers else 1
            
            for row in rows:
                if len(row) > max(poll_id_col, poll_data_col) and row[poll_id_col] == poll_id and row[poll_data_col]:
                    try:
                        poll_info = json.loads(row[poll_data_col])
                        return poll_info
                    except Exception as e:
                        self.log_error(f"Error loading poll data for poll {poll_id}: {e}")
                        return None
            
            return None
            
        except Exception as e:
            self.log_error(f"Error getting poll {poll_id} from Google Sheets: {e}")
            return None
    
    def create_poll(self, poll_id: str, poll_info: Dict[str, Any]) -> bool:
        """
        Create a new poll in Google Sheets.
        
        Args:
            poll_id: Unique identifier for the poll
            poll_info: Poll information dictionary
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Check if poll already exists
            existing_poll = self.get_poll_by_id(poll_id)
            if existing_poll:
                self.log_warning(f"Poll {poll_id} already exists, use update_poll instead")
                return False
            
            # Use efficient single poll save
            return self.save_single_poll(poll_id, poll_info)
            
        except Exception as e:
            self.log_error(f"Error creating poll {poll_id}: {e}")
            return False
    
    async def update_poll(self, poll_answer: PollAnswer) -> bool:
        """
        Update an existing poll in Google Sheets.
        
        Args:
            poll_id: Unique identifier for the poll
            poll_info: Updated poll information dictionary
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            poll_id = poll_answer.poll_id
            user_id = poll_answer.user.id
            selected_options = poll_answer.option_ids
            
            poll_info = self.get_poll_by_id(poll_id)
            if not poll_info:
                self.log_error(f"Poll {poll_id} not found")
                return False
            
            # update poll data
            poll_info['votes'] = {i: [] for i in range(len(poll_info['options']))}
            
            # Add new votes
            for option_id in selected_options:
                poll_info['votes'][option_id].append(user_id)
            
            self.log_info(f"Poll {poll_id}: User {user_id} voted for options {selected_options}")

            # Save poll data
            return await self.save_single_poll(poll_id, poll_info)
            
        except Exception as e:
            self.log_error(f"Error updating poll {poll_id}: {e}")
            return False
    
    def remove_poll_data(self, poll_id: str) -> bool:
        """
        Remove poll data from Google Sheets.
        
        Args:
            poll_id: Unique identifier for the poll to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            sheet_data = self.sheets_service.get_data_from_sheet(self.sheet_name)
            if not sheet_data or 'rows' not in sheet_data:
                return True  # Nothing to remove
            
            headers = sheet_data['headers']
            rows = sheet_data['rows']
            
            # Find poll_id column index
            poll_id_col = headers.index('poll_id') if 'poll_id' in headers else 0
            
            # Find and remove the row with this poll_id
            for i, row in enumerate(rows):
                if len(row) > poll_id_col and row[poll_id_col] == poll_id:
                    rows.pop(i)
                    break
            
            # Save updated sheet
            success = self.sheets_service.update_sheet(self.sheet_name, sheet_data)
            if success:
                self.log_info(f"Removed poll data for poll {poll_id} from Google Sheets")
            return success
            
        except Exception as e:
            self.log_error(f"Error removing poll data for poll {poll_id} from Google Sheets: {e}")
            return False
    
    def get_polls_by_creator(self, creator_id: str) -> List[Dict[str, Any]]:
        """
        Get all polls created by a specific user.
        
        Args:
            creator_id: User ID of the poll creator
            
        Returns:
            List of poll information dictionaries
        """
        try:
            all_polls = self.load_poll_data()
            creator_polls = []
            
            for poll_id, poll_info in all_polls.items():
                if poll_info.get('creator') == creator_id:
                    poll_info['poll_id'] = poll_id  # Add poll_id to the info
                    creator_polls.append(poll_info)
            
            return creator_polls
            
        except Exception as e:
            self.log_error(f"Error getting polls by creator {creator_id}: {e}")
            return []
    
    def get_active_polls(self) -> List[Dict[str, Any]]:
        """
        Get all active (non-expired) polls.
        
        Returns:
            List of active poll information dictionaries
        """
        try:
            all_polls = self.load_poll_data()
            active_polls = []
            current_time = datetime.now()
            
            for poll_id, poll_info in all_polls.items():
                # Check if poll has an expiration time
                if 'expires_at' in poll_info:
                    try:
                        expires_at = datetime.fromisoformat(poll_info['expires_at'])
                        if current_time < expires_at:
                            poll_info['poll_id'] = poll_id
                            active_polls.append(poll_info)
                    except (ValueError, TypeError):
                        # If expiration time is invalid, consider poll active
                        poll_info['poll_id'] = poll_id
                        active_polls.append(poll_info)
                else:
                    # No expiration time, consider poll active
                    poll_info['poll_id'] = poll_id
                    active_polls.append(poll_info)
            
            return active_polls
            
        except Exception as e:
            self.log_error(f"Error getting active polls: {e}")
            return []
    
    def get_polls_by_type(self, poll_type: str) -> List[Dict[str, Any]]:
        """
        Get all polls of a specific type.
        
        Args:
            poll_type: Type of poll to filter by
            
        Returns:
            List of poll information dictionaries
        """
        try:
            all_polls = self.load_poll_data()
            type_polls = []
            
            for poll_id, poll_info in all_polls.items():
                if poll_info.get('type') == poll_type:
                    poll_info['poll_id'] = poll_id
                    type_polls.append(poll_info)
            
            return type_polls
            
        except Exception as e:
            self.log_error(f"Error getting polls by type {poll_type}: {e}")
            return []
    
    def search_polls(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search polls by question text or other searchable fields.
        
        Args:
            search_term: Text to search for
            
        Returns:
            List of matching poll information dictionaries
        """
        try:
            all_polls = self.load_poll_data()
            matching_polls = []
            search_term_lower = search_term.lower()
            
            for poll_id, poll_info in all_polls.items():
                # Search in question text
                question = poll_info.get('question', '')
                if search_term_lower in question.lower():
                    poll_info['poll_id'] = poll_id
                    matching_polls.append(poll_info)
                    continue
                
                # Search in other text fields
                for field, value in poll_info.items():
                    if isinstance(value, str) and search_term_lower in value.lower():
                        poll_info['poll_id'] = poll_id
                        matching_polls.append(poll_info)
                        break
            
            return matching_polls
            
        except Exception as e:
            self.log_error(f"Error searching polls for term '{search_term}': {e}")
            return []
    
    def get_poll_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all polls.
        
        Returns:
            Dictionary containing poll statistics
        """
        try:
            all_polls = self.load_poll_data()
            stats = {
                'total_polls': len(all_polls),
                'active_polls': len(self.get_active_polls()),
                'poll_types': {},
                'creators': {},
                'total_votes': 0
            }
            
            for poll_info in all_polls.values():
                # Count poll types
                poll_type = poll_info.get('type', 'unknown')
                stats['poll_types'][poll_type] = stats['poll_types'].get(poll_type, 0) + 1
                
                # Count creators
                creator = poll_info.get('creator', 'unknown')
                stats['creators'][creator] = stats['creators'].get(creator, 0) + 1
                
                # Count total votes
                votes = poll_info.get('votes', {})
                if isinstance(votes, dict):
                    for option_votes in votes.values():
                        if isinstance(option_votes, list):
                            stats['total_votes'] += len(option_votes)
            
            return stats
            
        except Exception as e:
            self.log_error(f"Error getting poll statistics: {e}")
            return {}
    
    def cleanup_expired_polls(self) -> int:
        """
        Remove expired polls from the system.
        
        Returns:
            Number of polls removed
        """
        try:
            all_polls = self.load_poll_data()
            expired_polls = []
            current_time = datetime.now()
            
            for poll_id, poll_info in all_polls.items():
                if 'expires_at' in poll_info:
                    try:
                        expires_at = datetime.fromisoformat(poll_info['expires_at'])
                        if current_time >= expires_at:
                            expired_polls.append(poll_id)
                    except (ValueError, TypeError):
                        # Invalid expiration time, skip
                        continue
            
            # Remove expired polls
            removed_count = 0
            for poll_id in expired_polls:
                if self.remove_poll_data(poll_id):
                    removed_count += 1
            
            if removed_count > 0:
                self.log_info(f"Cleaned up {removed_count} expired polls")
            
            return removed_count
            
        except Exception as e:
            self.log_error(f"Error cleaning up expired polls: {e}")
            return 0 