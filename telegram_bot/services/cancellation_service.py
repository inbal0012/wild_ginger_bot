from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from ..config.settings import settings
from ..services.sheets_service import SheetsService
from ..services.message_service import MessageService
from ..exceptions import RegistrationNotFoundException, ServiceException

logger = logging.getLogger(__name__)

class CancellationService:
    """Service for handling user registration cancellations"""
    
    def __init__(self, 
                 sheets_service: SheetsService = None,
                 message_service: MessageService = None):
        self.sheets_service = sheets_service or SheetsService()
        self.message_service = message_service or MessageService()
    
    async def cancel_user_registration(self, 
                                     user_id: int, 
                                     reason: str, 
                                     language_code: str = 'en') -> Dict[str, Any]:
        """Cancel a user's registration with reason and timing analysis"""
        try:
            # Find user's registration
            registration = await self._find_user_registration(user_id, language_code)
            
            if not registration:
                return {
                    'success': False,
                    'message': self._get_no_registration_message(language_code),
                    'requires_reason': False
                }
            
            submission_id = registration['submission_id']
            user_language = registration.get('language', language_code)
            
            # Validate reason
            if not reason:
                return {
                    'success': False,
                    'message': self._get_reason_required_message(user_language),
                    'requires_reason': True
                }
            
            # Determine if this is a last-minute cancellation
            is_last_minute = self._is_last_minute_cancellation(registration)
            
            # Update cancellation status in Google Sheets
            success = await self.sheets_service.update_cancellation_status(
                submission_id=submission_id,
                cancelled=True,
                reason=reason,
                is_last_minute=is_last_minute
            )
            
            if success:
                logger.info(f"Registration {submission_id} cancelled by user {user_id}: {reason}")
                
                return {
                    'success': True,
                    'message': self._get_cancellation_success_message(
                        user_language, reason, is_last_minute
                    ),
                    'is_last_minute': is_last_minute,
                    'submission_id': submission_id
                }
            else:
                logger.error(f"Failed to update cancellation status for {submission_id}")
                return {
                    'success': False,
                    'message': self._get_cancellation_error_message(user_language),
                    'requires_reason': False
                }
                
        except Exception as e:
            logger.error(f"Error cancelling registration for user {user_id}: {e}")
            raise ServiceException(f"Failed to cancel registration: {e}")
    
    async def _find_user_registration(self, user_id: int, fallback_language: str) -> Optional[Dict[str, Any]]:
        """Find user's registration by Telegram user ID"""
        try:
            # Try to find by Telegram User ID
            registration = await self.sheets_service.find_submission_by_telegram_id(str(user_id))
            
            if registration:
                return registration
            
            # TODO: Could also check a user mapping cache/database here
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding registration for user {user_id}: {e}")
            return None
    
    def _is_last_minute_cancellation(self, registration: Dict[str, Any]) -> bool:
        """Determine if cancellation is considered last-minute"""
        try:
            # Method 1: If payment was completed, assume event is soon (last minute)
            if registration.get('paid', False):
                return True
            
            # Method 2: If we have event date, check days until event
            event_date_str = registration.get('event_date')
            if event_date_str:
                return self._check_days_until_event(event_date_str, threshold_days=7)
            
            # Method 3: If approved, assume it's getting close to event
            if registration.get('approved', False):
                return True
            
            # Default: not last minute if still in early stages
            return False
            
        except Exception as e:
            logger.error(f"Error determining last-minute status: {e}")
            return False
    
    def _check_days_until_event(self, event_date_str: str, threshold_days: int = 7) -> bool:
        """Check if cancellation is within threshold days of event"""
        try:
            if not event_date_str:
                return False
            
            # Parse event date (try multiple formats)
            event_date = None
            date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
            
            for date_format in date_formats:
                try:
                    event_date = datetime.strptime(event_date_str, date_format)
                    break
                except ValueError:
                    continue
            
            if not event_date:
                logger.warning(f"Could not parse event date: {event_date_str}")
                return False
            
            # Check if cancellation is within threshold days of event
            cancellation_date = datetime.now()
            days_before_event = (event_date - cancellation_date).days
            
            return days_before_event <= threshold_days
            
        except Exception as e:
            logger.error(f"Error checking days until event: {e}")
            return False
    
    def _get_no_registration_message(self, language_code: str) -> str:
        """Get message for when no registration is found"""
        if language_code == 'he':
            return self.message_service.get_message('he', 'no_submission_linked')
        else:
            return self.message_service.get_message('en', 'no_submission_linked')
    
    def _get_reason_required_message(self, language: str) -> str:
        """Get message requesting cancellation reason"""
        if language == 'he':
            return "אנא ספק סיבה לביטול (לדוגמה: /cancel מחלה פתאומית)"
        else:
            return "Please provide a reason for cancellation (e.g., /cancel sudden illness)"
    
    def _get_cancellation_success_message(self, language: str, reason: str, is_last_minute: bool) -> str:
        """Get success message for completed cancellation"""
        if language == 'he':
            message = f"הרשמתך בוטלה.\n\nסיבה: {reason}"
            if is_last_minute:
                message += "\n\n⚠️ שים לב: זהו ביטול ברגע האחרון וזה יילקח בחשבון בבקשות עתידיות."
        else:
            message = f"Your registration has been cancelled.\n\nReason: {reason}"
            if is_last_minute:
                message += "\n\n⚠️ Note: This is a last-minute cancellation and will be taken into account for future applications."
        
        return message
    
    def _get_cancellation_error_message(self, language: str) -> str:
        """Get error message for failed cancellation"""
        if language == 'he':
            return "❌ שגיאה בביטול הרשמה. אנא פנה לתמיכה."
        else:
            return "❌ Error cancelling registration. Please contact support."
    
    async def get_cancellation_statistics(self) -> Dict[str, Any]:
        """Get statistics about cancellations (for admin use)"""
        try:
            # Get all registrations
            all_registrations = await self.sheets_service.get_all_registrations()
            
            # Count cancellations
            total_cancellations = 0
            last_minute_cancellations = 0
            cancellation_reasons = {}
            
            for registration in all_registrations:
                if registration.get('cancelled', False):
                    total_cancellations += 1
                    
                    if registration.get('last_minute_cancellation', False):
                        last_minute_cancellations += 1
                    
                    reason = registration.get('cancellation_reason', 'No reason provided')
                    cancellation_reasons[reason] = cancellation_reasons.get(reason, 0) + 1
            
            return {
                'total_registrations': len(all_registrations),
                'total_cancellations': total_cancellations,
                'last_minute_cancellations': last_minute_cancellations,
                'cancellation_rate': total_cancellations / len(all_registrations) if all_registrations else 0,
                'last_minute_rate': last_minute_cancellations / total_cancellations if total_cancellations else 0,
                'cancellation_reasons': cancellation_reasons
            }
            
        except Exception as e:
            logger.error(f"Error getting cancellation statistics: {e}")
            raise ServiceException(f"Failed to get cancellation statistics: {e}")
    
    async def admin_cancel_registration(self, 
                                      submission_id: str, 
                                      reason: str, 
                                      admin_user_id: int,
                                      is_last_minute: bool = False) -> Dict[str, Any]:
        """Admin-initiated cancellation of a registration"""
        try:
            # Verify admin privileges (could add admin check here)
            logger.info(f"Admin {admin_user_id} cancelling registration {submission_id}")
            
            # Update cancellation status
            success = await self.sheets_service.update_cancellation_status(
                submission_id=submission_id,
                cancelled=True,
                reason=f"Admin cancellation: {reason}",
                is_last_minute=is_last_minute
            )
            
            if success:
                # Get registration data for notification
                registration = await self.sheets_service.find_submission_by_id(submission_id)
                
                return {
                    'success': True,
                    'message': f"✅ Registration {submission_id} cancelled successfully by admin",
                    'registration': registration
                }
            else:
                return {
                    'success': False,
                    'message': f"❌ Failed to cancel registration {submission_id}"
                }
                
        except Exception as e:
            logger.error(f"Error in admin cancellation of {submission_id}: {e}")
            raise ServiceException(f"Failed to cancel registration: {e}") 