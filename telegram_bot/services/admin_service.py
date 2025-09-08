from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from ..config.settings import settings
from ..services.sheets_service import SheetsService
from ..services.message_service import MessageService
from ..exceptions import RegistrationNotFoundException, ServiceException, UnauthorizedOperationException

logger = logging.getLogger(__name__)

class AdminService:
    """Service for handling all admin-related functionality"""
    
    def __init__(self, sheets_service: SheetsService = None, message_service: MessageService = None):
        self.sheets_service = sheets_service or SheetsService()
        self.message_service = message_service or MessageService()
        
        # Cache for admin user verification
        self._admin_users_cache = None
        self._cache_updated = None
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user has admin privileges"""
        # Refresh cache every hour
        now = datetime.now()
        if self._admin_users_cache is None or (self._cache_updated and (now - self._cache_updated).total_seconds() > 3600):
            self._admin_users_cache = set(settings.admin_user_ids)
            self._cache_updated = now
        
        return user_id in self._admin_users_cache
    
    def require_admin(self, user_id: int) -> None:
        """Raise exception if user is not admin"""
        if not self.is_admin(user_id):
            raise UnauthorizedOperationException(f"User {user_id} does not have admin privileges")
    
    async def get_dashboard_stats(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard statistics and pending approvals"""
        self.require_admin(user_id)
        
        try:
            # Get all registrations
            registrations = await self.sheets_service.get_all_registrations()
            
            # Initialize statistics
            stats = {
                'total': 0,
                'ready_for_review': 0,
                'approved': 0,
                'paid': 0,
                'partner_pending': 0,
                'cancelled': 0
            }
            
            pending_approvals = []
            
            for registration in registrations:
                stats['total'] += 1
                
                # Count by status
                if registration.get('cancelled', False):
                    stats['cancelled'] += 1
                elif not registration.get('partner', False):
                    stats['partner_pending'] += 1
                elif (registration.get('form', False) and 
                      registration.get('partner', False) and 
                      registration.get('get_to_know', False) and 
                      not registration.get('approved', False)):
                    stats['ready_for_review'] += 1
                    pending_approvals.append({
                        'name': registration.get('alias', 'Unknown'),
                        'submission_id': registration.get('submission_id'),
                        'partner': registration.get('partner_alias', 'Solo') if registration.get('partner_alias') else 'Solo'
                    })
                elif registration.get('approved', False) and registration.get('paid', False):
                    stats['paid'] += 1
                elif registration.get('approved', False):
                    stats['approved'] += 1
            
            return {
                'stats': stats,
                'pending_approvals': pending_approvals
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise ServiceException(f"Failed to retrieve dashboard statistics: {e}")
    
    def format_dashboard_message(self, dashboard_data: Dict[str, Any]) -> str:
        """Format dashboard statistics into a readable message"""
        stats = dashboard_data['stats']
        pending_approvals = dashboard_data['pending_approvals']
        
        message = (
            f"🔧 **Admin Dashboard**\n\n"
            f"**Registration Statistics:**\n"
            f"• Total: {stats['total']}\n"
            f"• Ready for Review: {stats['ready_for_review']}\n"
            f"• Approved: {stats['approved']}\n"
            f"• Paid: {stats['paid']}\n"
            f"• Partner Pending: {stats['partner_pending']}\n"
            f"• Cancelled: {stats['cancelled']}\n\n"
        )
        
        if pending_approvals:
            message += f"**Pending Approvals ({len(pending_approvals)}):**\n"
            for approval in pending_approvals[:10]:  # Show first 10
                partner_info = f" + {approval['partner']}" if approval['partner'] != 'Solo' else ""
                message += f"• {approval['name']}{partner_info} (`{approval['submission_id']}`)\n"
            
            if len(pending_approvals) > 10:
                message += f"• ... and {len(pending_approvals) - 10} more\n"
        
        message += f"\n**Available Commands:**\n"
        message += f"• `/admin_approve SUBM_ID` - Approve registration\n"
        message += f"• `/admin_reject SUBM_ID` - Reject registration\n"
        message += f"• `/admin_status SUBM_ID` - Check registration status\n"
        message += f"• `/admin_digest` - Generate weekly digest\n"
        
        return message
    
    async def approve_registration(self, submission_id: str, admin_user_id: int, admin_name: str = "Admin") -> Dict[str, Any]:
        """Approve a registration and notify user"""
        self.require_admin(admin_user_id)
        
        try:
            # Update approval status in sheets
            success = await self.sheets_service.update_admin_approval(submission_id, True)
            
            if not success:
                return {
                    'success': False,
                    'message': f"❌ Failed to approve registration {submission_id}. Please check the submission ID."
                }
            
            # Get user data for notification
            registration = await self.sheets_service.find_submission_by_id(submission_id)
            
            if registration and registration.get('telegram_user_id'):
                await self._notify_user_approval(registration, submission_id)
                
                # Notify other admins
                await self._notify_admins_about_action(
                    admin_name, "approved", submission_id, 
                    registration.get('alias', 'Unknown')
                )
            
            return {
                'success': True,
                'message': f"✅ Registration {submission_id} approved successfully!",
                'registration': registration
            }
            
        except Exception as e:
            logger.error(f"Error approving registration {submission_id}: {e}")
            raise ServiceException(f"Failed to approve registration: {e}")
    
    async def reject_registration(self, submission_id: str, reason: str, admin_user_id: int, admin_name: str = "Admin") -> Dict[str, Any]:
        """Reject a registration with reason and notify user"""
        self.require_admin(admin_user_id)
        
        try:
            # Update approval status in sheets (set to false)
            success = await self.sheets_service.update_admin_approval(submission_id, False, reason)
            
            if not success:
                return {
                    'success': False,
                    'message': f"❌ Failed to reject registration {submission_id}. Please check the submission ID."
                }
            
            # Get user data for notification
            registration = await self.sheets_service.find_submission_by_id(submission_id)
            
            if registration and registration.get('telegram_user_id'):
                await self._notify_user_rejection(registration, submission_id, reason)
                
                # Notify other admins
                await self._notify_admins_about_action(
                    admin_name, "rejected", submission_id, 
                    registration.get('alias', 'Unknown'), reason
                )
            
            return {
                'success': True,
                'message': f"✅ Registration {submission_id} rejected successfully!",
                'registration': registration
            }
            
        except Exception as e:
            logger.error(f"Error rejecting registration {submission_id}: {e}")
            raise ServiceException(f"Failed to reject registration: {e}")
    
    async def get_registration_status(self, submission_id: str, admin_user_id: int) -> Dict[str, Any]:
        """Get detailed status of a registration for admin view"""
        self.require_admin(admin_user_id)
        
        try:
            registration = await self.sheets_service.find_submission_by_id(submission_id)
            
            if not registration:
                return {
                    'success': False,
                    'message': f"❌ Registration {submission_id} not found.",
                    'registration': None
                }
            
            return {
                'success': True,
                'registration': registration,
                'message': self._format_admin_status_message(registration, submission_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting registration status {submission_id}: {e}")
            raise ServiceException(f"Failed to get registration status: {e}")
    
    def _format_admin_status_message(self, registration: Dict[str, Any], submission_id: str) -> str:
        """Format detailed registration status for admin view"""
        # Format partner information
        partner_info = ""
        if registration.get('partner_names'):
            partner_status = registration.get('partner_status', {})
            registered_partners = partner_status.get('registered_partners', [])
            missing_partners = partner_status.get('missing_partners', [])
            
            if registered_partners:
                partner_info += f"**Registered Partners:** {', '.join(registered_partners)}\n"
            if missing_partners:
                partner_info += f"**Missing Partners:** {', '.join(missing_partners)}\n"
        elif registration.get('partner_alias'):
            partner_info = f"**Partner:** {registration['partner_alias']}\n"
        else:
            partner_info = "**Partner:** Coming alone\n"
        
        message = (
            f"📋 **Registration Status: {submission_id}**\n\n"
            f"**Name:** {registration.get('alias', 'Unknown')}\n"
            f"**Language:** {registration.get('language', 'Unknown')}\n"
            f"**Telegram ID:** {registration.get('telegram_user_id', 'Not linked')}\n\n"
            f"{partner_info}\n"
            f"**Progress:**\n"
            f"• Form: {'✅' if registration.get('form', False) else '❌'}\n"
            f"• Partner: {'✅' if registration.get('partner', False) else '❌'}\n"
            f"• Get-to-know: {'✅' if registration.get('get_to_know', False) else '❌'}\n"
            f"• Approved: {'✅' if registration.get('approved', False) else '❌'}\n"
            f"• Paid: {'✅' if registration.get('paid', False) else '❌'}\n"
            f"• Group: {'✅' if registration.get('group_open', False) else '❌'}\n\n"
            f"**Returning Participant:** {'Yes' if registration.get('is_returning_participant', False) else 'No'}\n"
            f"**Cancelled:** {'Yes' if registration.get('cancelled', False) else 'No'}"
        )
        
        return message
    
    async def generate_weekly_digest(self, admin_user_id: int) -> Dict[str, Any]:
        """Generate and send weekly digest to all admins"""
        self.require_admin(admin_user_id)
        
        try:
            # Get all registrations for statistics
            registrations = await self.sheets_service.get_all_registrations()
            
            # Count registrations by status
            stats = {
                'total': 0,
                'pending_approval': 0,
                'approved': 0,
                'paid': 0,
                'partner_pending': 0,
                'cancelled': 0
            }
            
            recent_registrations = []
            
            for registration in registrations:
                stats['total'] += 1
                
                # Count by status
                if registration.get('cancelled', False):
                    stats['cancelled'] += 1
                elif not registration.get('partner', False):
                    stats['partner_pending'] += 1
                elif registration.get('approved', False) and registration.get('paid', False):
                    stats['paid'] += 1
                elif registration.get('approved', False):
                    stats['approved'] += 1
                elif (registration.get('form', False) and 
                      registration.get('partner', False) and 
                      registration.get('get_to_know', False)):
                    stats['pending_approval'] += 1
                
                # Add to recent registrations (would normally filter by date)
                recent_registrations.append({
                    'name': registration.get('alias', 'Unknown'),
                    'submission_id': registration.get('submission_id'),
                    'status': 'Ready for Review' if (
                        registration.get('form', False) and 
                        registration.get('partner', False) and 
                        registration.get('get_to_know', False) and 
                        not registration.get('approved', False)
                    ) else 'In Progress'
                })
            
            # Format digest message
            digest_message = self._format_weekly_digest(stats, recent_registrations)
            
            # Send to all admins
            await self._send_digest_to_admins(digest_message)
            
            return {
                'success': True,
                'message': "✅ Weekly digest sent to all admins!",
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly digest: {e}")
            raise ServiceException(f"Failed to generate weekly digest: {e}")
    
    def _format_weekly_digest(self, stats: Dict[str, int], recent_registrations: List[Dict[str, Any]]) -> str:
        """Format weekly digest message"""
        message = (
            f"📊 **Weekly Registration Digest**\n\n"
            f"**Total Registrations:** {stats['total']}\n"
            f"**Pending Approval:** {stats['pending_approval']}\n"
            f"**Approved:** {stats['approved']}\n"
            f"**Paid:** {stats['paid']}\n"
            f"**Partner Pending:** {stats['partner_pending']}\n"
            f"**Cancelled:** {stats['cancelled']}\n\n"
        )
        
        if stats['pending_approval'] > 0:
            message += f"⚠️  **{stats['pending_approval']} registrations need your review!**\n\n"
        
        if recent_registrations[:5]:  # Show first 5
            message += "**Recent Activity:**\n"
            for reg in recent_registrations[:5]:
                message += f"• {reg['name']} ({reg['submission_id']}) - {reg['status']}\n"
        
        return message
    
    async def _notify_user_approval(self, registration: Dict[str, Any], submission_id: str):
        """Notify user that their registration was approved"""
        try:
            user_language = registration.get('language', 'en')
            telegram_user_id = registration.get('telegram_user_id')
            
            if user_language == 'he':
                user_message = f"🎉 הרשמתך אושרה!\n\nמזהה הגשה: {submission_id}\n\nהצעד הבא: השלמת התשלום."
            else:
                user_message = f"🎉 Your registration has been approved!\n\nSubmission ID: {submission_id}\n\nNext step: Complete payment."
            
            # TODO: Implement actual user notification via Telegram bot
            logger.info(f"📤 Would notify user {telegram_user_id} about approval: {user_message}")
            
        except Exception as e:
            logger.error(f"Failed to notify user about approval: {e}")
    
    async def _notify_user_rejection(self, registration: Dict[str, Any], submission_id: str, reason: str):
        """Notify user that their registration was rejected"""
        try:
            user_language = registration.get('language', 'en')
            telegram_user_id = registration.get('telegram_user_id')
            
            if user_language == 'he':
                user_message = f"❌ הרשמתך נדחתה\n\nמזהה הגשה: {submission_id}\n\nסיבה: {reason}\n\nאתה מוזמן לנסות שוב באירוע הבא."
            else:
                user_message = f"❌ Your registration has been rejected\n\nSubmission ID: {submission_id}\n\nReason: {reason}\n\nYou're welcome to try again for the next event."
            
            # TODO: Implement actual user notification via Telegram bot
            logger.info(f"📤 Would notify user {telegram_user_id} about rejection: {user_message}")
            
        except Exception as e:
            logger.error(f"Failed to notify user about rejection: {e}")
    
    async def _notify_admins_about_action(self, admin_name: str, action: str, submission_id: str, user_name: str, reason: str = ""):
        """Notify other admins about approval/rejection actions"""
        try:
            if action == "approved":
                message = (
                    f"✅ Registration approved by {admin_name}\n\n"
                    f"**Submission ID:** {submission_id}\n"
                    f"**User:** {user_name}"
                )
            elif action == "rejected":
                message = (
                    f"❌ Registration rejected by {admin_name}\n\n"
                    f"**Submission ID:** {submission_id}\n"
                    f"**User:** {user_name}\n"
                    f"**Reason:** {reason}"
                )
            else:
                return
            
            # TODO: Implement actual admin notification system
            logger.info(f"📤 Would notify admins about {action}: {message}")
            
        except Exception as e:
            logger.error(f"Failed to notify admins about {action}: {e}")
    
    async def _send_digest_to_admins(self, digest_message: str):
        """Send digest message to all admins"""
        try:
            # TODO: Implement actual admin notification system
            logger.info(f"📊 Would send weekly digest to {len(settings.admin_user_ids)} admins")
            logger.info(f"Digest content: {digest_message}")
            
        except Exception as e:
            logger.error(f"Failed to send digest to admins: {e}")
    
    async def notify_admins(self, message: str, notification_type: str = "general") -> bool:
        """Send notification to all admins"""
        try:
            # Check if this notification type is enabled
            # TODO: Implement actual admin notification system
            logger.info(f"📢 Admin notification ({notification_type}): {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
            return False
    
    async def send_group_welcome_message(self, new_member, chat_id: int, bot) -> bool:
        """Send welcome message to new group member"""
        try:
            # Get user language preference (default to English)
            user_language = 'he' if new_member.language_code == 'he' else 'en'
            
            # Get welcome message based on language
            welcome_message = self._get_group_welcome_message(user_language, new_member.first_name)
            
            # Send welcome message to the group
            await bot.send_message(
                chat_id=chat_id,
                text=welcome_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"📢 Welcome message sent to new member {new_member.id} in group {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome message to new member: {e}")
            return False
    
    def _get_group_welcome_message(self, language: str, member_name: str) -> str:
        """Get localized welcome message for new group members"""
        if language == 'he':
            return (
                f"🎉 ברוכים הבאים {member_name}!\n\n"
                f"אני הבוט של Wild Ginger. ואני כאן כי כלנית עושה בדיקות למערכת שלה. 😜😁\n\n"
                f"על מנת שיהיה לנו אירוע יותר נעים וכיפי אנא כתבו פוסט היכרות. הוא יכול להיות קצר או ארוך כרצונכם.\n"
                f'נשמח אם תרשמו מאיפה אתם בארץ ע"מ לעודד טרמפים\n'
                f'מעבר לכך מוזמנים לספר ככל העולה על דעתכם'
            )
        else:
            return (
                f"🎉 Welcome {member_name}!\n\n"
                f"I'm the Wild Ginger bot and I'm here because Kalanit is testing her system 😜😁.\n\n"
                f"To make this event more fun and pleasant, please write a get-to-know post. It can be short or long as you wish.\n"
                f'We would appreciate it if you would share where you are from to promote carpooling\n'
                f'In addition, we invite you to share whatever you want about yourself'
                
            ) 