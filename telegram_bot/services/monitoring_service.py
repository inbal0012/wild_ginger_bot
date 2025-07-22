from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from datetime import datetime
import asyncio
import logging

from ..config.settings import settings
from ..services.sheets_service import SheetsService
from ..services.admin_service import AdminService
from ..exceptions import ServiceException, SheetsConnectionException

if TYPE_CHECKING:
    from telegram.ext import Application

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring Sheet1 for new registrations and duplicating to managed sheet"""
    
    def __init__(self, 
                 sheets_service: SheetsService = None,
                 admin_service: AdminService = None):
        self.sheets_service = sheets_service or SheetsService()
        self.admin_service = admin_service or AdminService()
        
        # Configuration
        self.sheet1_range = "Sheet1!A1:ZZ1000"  # Range to read from Sheet1
        self.monitoring_interval = 300  # 5 minutes in seconds
        
        # Bot application reference for notifications
        self.bot_application: Optional['Application'] = None
        
        # Background monitoring task management
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Column mapping configuration (Sheet1 -> Managed Sheet)
        self.column_mappings = {
            'Submission ID': 0,  # Column A
            'שם מלא': 1,         # Column B  
            'שם הפרטנר': 2,      # Column C
            'האם תרצו להמשיך בעברית או באנגלית': 3,  # Column D
            'האם השתתפת בעבר באחד מאירועי Wild Ginger': 4,  # Column E
        }
    
    def set_bot_application(self, bot_application: 'Application'):
        """Set the bot application reference for sending notifications"""
        self.bot_application = bot_application
    
    async def start_monitoring(self):
        """Start the background sheet monitoring"""
        if self.is_monitoring:
            logger.warning("Sheet monitoring is already running")
            return
        
        if not self.sheets_service.spreadsheet:
            logger.warning("Google Sheets service not available - monitoring disabled")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 Sheet monitoring started - checking every 5 minutes")
    
    async def stop_monitoring(self):
        """Stop the background sheet monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️ Sheet monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop that runs every 5 minutes"""
        logger.info("🔄 Sheet monitoring loop started")
        
        while self.is_monitoring:
            try:
                await self.check_for_new_registrations()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                logger.info("📴 Sheet monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)  # Continue monitoring even on error
    
    async def check_for_new_registrations(self):
        """Check Sheet1 for new entries and duplicate them to managed sheet"""
        try:
            logger.info("🔍 Checking for new registrations in Sheet1...")
            
            # Get data from both sheets
            sheet1_data = await self._get_sheet1_data()
            if not sheet1_data:
                logger.warning("Could not access Sheet1")
                return
            
            managed_data = await self._get_managed_sheet_data()
            if not managed_data:
                logger.warning("Could not access managed sheet")
                return
            
            # Find new registrations
            new_registrations = await self._find_new_registrations(sheet1_data, managed_data)
            
            if new_registrations:
                logger.info(f"📝 Found {len(new_registrations)} new registrations")
                
                # Process each new registration
                for submission_id, row_data in new_registrations:
                    await self._process_new_registration(submission_id, row_data, sheet1_data['headers'])
            else:
                logger.debug("✅ No new registrations found")
                
        except Exception as e:
            logger.error(f"Error checking for new registrations: {e}")
            raise ServiceException(f"Failed to check for new registrations: {e}")
    
    async def _get_sheet1_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data from Sheet1 (original form responses)"""
        if not self.sheets_service.spreadsheet:
            return None
        
        try:
            result = self.sheets_service.spreadsheet.spreadsheets().values().get(
                spreadsheetId=self.sheets_service.spreadsheet_id,
                range=self.sheet1_range
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
                
            headers = values[0] if values else []
            rows = values[1:] if len(values) > 1 else []
            
            return {'headers': headers, 'rows': rows}
            
        except Exception as e:
            logger.error(f"Error reading Sheet1: {e}")
            return None
    
    async def _get_managed_sheet_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data from managed sheet"""
        return self.sheets_service.get_sheet_data()
    
    async def _find_new_registrations(self, 
                                    sheet1_data: Dict[str, Any], 
                                    managed_data: Dict[str, Any]) -> List[Tuple[str, List]]:
        """Find registrations that exist in Sheet1 but not in managed sheet"""
        try:
            # Get existing submission IDs from managed sheet
            managed_submission_ids = set()
            managed_headers = managed_data['headers']
            managed_column_indices = self.sheets_service.get_column_indices(managed_headers)
            submission_id_col = managed_column_indices.get('submission_id')
            
            if submission_id_col is not None:
                for row in managed_data['rows']:
                    if len(row) > submission_id_col and row[submission_id_col]:
                        managed_submission_ids.add(row[submission_id_col])
            
            # Find submission ID column in Sheet1
            sheet1_headers = sheet1_data['headers']
            sheet1_submission_col = None
            
            for i, header in enumerate(sheet1_headers):
                if 'Submission ID' in header:
                    sheet1_submission_col = i
                    break
            
            if sheet1_submission_col is None:
                logger.error("Could not find Submission ID column in Sheet1")
                return []
            
            # Find new registrations
            new_registrations = []
            for row in sheet1_data['rows']:
                if len(row) > sheet1_submission_col and row[sheet1_submission_col]:
                    submission_id = row[sheet1_submission_col]
                    
                    # If this submission ID is not in managed sheet, it's new
                    if submission_id not in managed_submission_ids:
                        new_registrations.append((submission_id, row))
            
            return new_registrations
            
        except Exception as e:
            logger.error(f"Error finding new registrations: {e}")
            return []
    
    async def _process_new_registration(self, submission_id: str, row_data: List, sheet1_headers: List[str]):
        """Process a single new registration"""
        try:
            # Duplicate to managed sheet
            success = await self._duplicate_to_managed_sheet(row_data, sheet1_headers)
            
            if success:
                # Notify admins about new registration
                await self._notify_admin_new_registration(submission_id, row_data, sheet1_headers)
                logger.info(f"✅ Processed new registration: {submission_id}")
            else:
                logger.error(f"❌ Failed to duplicate registration: {submission_id}")
                
        except Exception as e:
            logger.error(f"Error processing new registration {submission_id}: {e}")
    
    async def _duplicate_to_managed_sheet(self, row_data: List, sheet1_headers: List[str]) -> bool:
        """Duplicate a row from Sheet1 to the managed sheet"""
        if not self.sheets_service.spreadsheet:
            logger.warning("Google Sheets not available - cannot duplicate data")
            return False
        
        try:
            # Get current managed sheet data to find the next empty row
            managed_data = await self._get_managed_sheet_data()
            if not managed_data:
                logger.error("Could not access managed sheet")
                return False
            
            # Find the next empty row in managed sheet
            next_row = len(managed_data['rows']) + 4  # +4 for header and starting from row 3
            
            # Map Sheet1 data to managed sheet format
            mapped_row = self._map_sheet1_to_managed(row_data, sheet1_headers)
            
            # Insert the row
            range_name = f"managed!A{next_row}:ZZ{next_row}"
            
            result = self.sheets_service.spreadsheet.spreadsheets().values().update(
                spreadsheetId=self.sheets_service.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [mapped_row]}
            ).execute()
            
            logger.info(f"✅ Duplicated new registration to managed sheet at row {next_row}")
            return True
            
        except Exception as e:
            logger.error(f"Error duplicating to managed sheet: {e}")
            return False
    
    def _map_sheet1_to_managed(self, row_data: List, sheet1_headers: List[str]) -> List[str]:
        """Map Sheet1 row data to managed sheet format"""
        try:
            managed_row = [''] * 30  # Initialize with empty values
            
            # Map specific columns based on headers
            for i, header in enumerate(sheet1_headers):
                if i < len(row_data):
                    value = row_data[i] if row_data[i] else ''
                    
                    # Map to managed sheet columns based on configuration
                    for sheet1_header, managed_col in self.column_mappings.items():
                        if sheet1_header in header:
                            if managed_col < len(managed_row):
                                managed_row[managed_col] = value
                            break
            
            return managed_row
            
        except Exception as e:
            logger.error(f"Error mapping Sheet1 to managed format: {e}")
            return [''] * 30
    
    async def _notify_admin_new_registration(self, submission_id: str, row_data: List, sheet1_headers: List[str]):
        """Notify admins about a new registration"""
        try:
            if not settings.admin_user_ids:
                logger.warning("No admin user IDs configured for notifications")
                return
            
            # Extract name from row data
            name = "Unknown"
            for i, header in enumerate(sheet1_headers):
                if 'שם מלא' in header and i < len(row_data):
                    name = row_data[i] if row_data[i] else "Unknown"
                    break
            
            # Create notification message
            message = (
                f"🆕 **New Registration Alert**\n\n"
                f"**Name:** {name}\n"
                f"**Submission ID:** {submission_id}\n"
                f"**Status:** Automatically copied to managed sheet\n\n"
                f"Please review and process this registration."
            )
            
            # Send notification to all admins
            if self.bot_application:
                for admin_id in settings.admin_user_ids:
                    try:
                        await self.bot_application.bot.send_message(chat_id=admin_id, text=message)
                        logger.info(f"✅ Notified admin {admin_id} about new registration: {submission_id}")
                    except Exception as e:
                        logger.error(f"❌ Error notifying admin {admin_id}: {e}")
            else:
                logger.warning("Bot application not set - cannot send admin notifications")
                
        except Exception as e:
            logger.error(f"Error notifying admins about new registration: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current status of the monitoring system"""
        return {
            'is_monitoring': self.is_monitoring,
            'monitoring_interval': self.monitoring_interval,
            'sheet1_range': self.sheet1_range,
            'has_bot_application': self.bot_application is not None,
            'sheets_service_available': self.sheets_service.spreadsheet is not None,
            'admin_count': len(settings.admin_user_ids),
            'column_mappings_count': len(self.column_mappings)
        }
    
    async def manual_check(self) -> Dict[str, Any]:
        """Manually trigger a check for new registrations (for testing/admin use)"""
        try:
            logger.info("🔍 Manual check for new registrations triggered")
            await self.check_for_new_registrations()
            
            return {
                'success': True,
                'message': "✅ Manual check completed successfully",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual check: {e}")
            return {
                'success': False,
                'message': f"❌ Manual check failed: {e}",
                'timestamp': datetime.now().isoformat()
            }
    
    def update_column_mappings(self, new_mappings: Dict[str, int]):
        """Update the column mappings configuration"""
        try:
            self.column_mappings.update(new_mappings)
            logger.info(f"✅ Updated column mappings: {len(self.column_mappings)} mappings configured")
            
        except Exception as e:
            logger.error(f"Error updating column mappings: {e}")
    
    def update_monitoring_interval(self, interval_seconds: int):
        """Update the monitoring interval"""
        if interval_seconds < 60:  # Minimum 1 minute
            logger.warning("Monitoring interval cannot be less than 60 seconds")
            return
        
        self.monitoring_interval = interval_seconds
        logger.info(f"✅ Updated monitoring interval to {interval_seconds} seconds ({interval_seconds//60} minutes)") 