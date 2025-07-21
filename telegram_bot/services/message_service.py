from typing import Dict, Any

from ..config.settings import settings

class MessageService:
    def __init__(self):
        self.messages = settings.messages
    
    def get_message(self, language: str, key: str, **kwargs) -> str:
        """Get a message in the specified language with optional formatting"""
        try:
            message = self.messages[language][key]
            if kwargs:
                return message.format(**kwargs)
            return message
        except KeyError:
            # Fallback to English if key not found
            try:
                message = self.messages['en'][key]
                if kwargs:
                    return message.format(**kwargs)
                return message
            except KeyError:
                return f"Message key '{key}' not found"
    
    def build_partner_status_text(self, status_data: Dict[str, Any], language: str) -> str:
        """Build detailed partner status text"""
        labels = self.messages[language]['status_labels']
        
        # Check if user has partners
        partner_names = status_data.get('partner_names', [])
        partner_status = status_data.get('partner_status', {})
        partner_complete = status_data.get('partner', False)  # Boolean from Google Sheets
        
        if not partner_names:
            # No partners - coming alone
            if language == 'he':
                return f"{labels['partner']}: מגיע.ה לבד"
            else:
                return f"{labels['partner']}: Coming alone"
        
        # Has partners - show detailed status
        registered_partners = partner_status.get('registered_partners', [])
        missing_partners = partner_status.get('missing_partners', [])
        
        # If we have detailed partner status, show it
        if len(partner_names) > 1:
            if language == 'he':
                partner_header = f"{labels['partner']}: סטטוס הפרטנרים שלך:"
            else:
                partner_header = f"{labels['partner']}: Your partners' status:"
            
            partner_lines = [partner_header]
            
            # Show registered partners
            if registered_partners:
                registered_text = ', '.join(registered_partners)
                completed_text = 'השלמו' if len(registered_partners) > 1 else 'השלים'
                if language == 'he':
                    partner_lines.append(f"    ✅ {registered_text} {completed_text} את הטופס")
                else:
                    partner_lines.append(f"    ✅ {registered_text} completed the form")
            
            # Show missing partners
            if missing_partners:
                missing_text = ', '.join(missing_partners)
                if language == 'he':
                    partner_lines.append(f"    ❌ {missing_text} עוד לא השלים את הטופס")
                else:
                    partner_lines.append(f"    ❌ {missing_text} hasn't completed the form yet")
            
            return '\n'.join(partner_lines)
        
        # Fallback to simple partner status when no detailed info available
        else:
            partner_alias = status_data.get('partner_alias', '')
            if partner_complete:
                if partner_alias:
                    return f"{labels['partner']}: ✅ ({partner_alias})"
                else:
                    return f"{labels['partner']}: ✅"
            else:
                if partner_alias:
                    return f"{labels['partner']}: ❌ ({partner_alias})"
                else:
                    return f"{labels['partner']}: ❌"

    def build_status_message(self, status_data: Dict[str, Any], language: str = 'en') -> str:
        """Build formatted status message"""
        # Handle invalid language codes gracefully
        if language not in self.messages:
            language = 'en'
        
        labels = self.messages[language]['status_labels']
        
        # Build detailed partner text
        partner_text = self.build_partner_status_text(status_data, language)
        
        # Build status text (with safe defaults for malformed data)
        status_text = labels['approved'] if status_data.get('approved', False) else labels['waiting_review']
        
        # Build payment text
        payment_text = labels['paid'] if status_data.get('paid', False) else labels['not_paid']
        
        # Build group text
        group_text = labels['group_open'] if status_data.get('group_open', False) else labels['group_not_open']
        
        # Construct the message (with safe defaults for malformed data)
        message = (
            f"{labels['form']}: {'✅' if status_data.get('form', False) else '❌'}\n"
            f"{partner_text}\n"
            f"{labels['get_to_know']}: {'✅' if status_data.get('get_to_know', False) else '❌'}\n"
            f"{labels['status']}: {status_text}\n"
            f"{labels['payment']}: {payment_text}\n"
            f"{labels['group']}: {group_text}\n\n"
        )
        
        return message
    
    def get_help_message(self, language: str = 'en') -> str:
        """Get help message"""
        return self.get_message(language, 'help')
    
    def get_welcome_message(self, language: str = 'en', name: str = None) -> str:
        """Get welcome message"""
        if name:
            return self.get_message(language, 'welcome', name=name)
        else:
            return self.get_message(language, 'welcome_no_name')
    
    def get_submission_not_found_message(self, language: str = 'en', submission_id: str = '') -> str:
        """Get submission not found message"""
        return self.get_message(language, 'submission_not_found', submission_id=submission_id)
    
    def get_no_submission_linked_message(self, language: str = 'en') -> str:
        """Get no submission linked message"""
        return self.get_message(language, 'no_submission_linked')
    
    def format_admin_digest(self, admin_data: Dict[str, Any]) -> str:
        """Format admin digest message"""
        digest_parts = []
        
        digest_parts.append("📊 **Weekly Admin Digest**\n")
        digest_parts.append(f"Total Registrations: {admin_data.get('total_registrations', 0)}")
        digest_parts.append(f"Pending Approvals: {admin_data.get('pending_approvals', 0)}")
        digest_parts.append(f"Approved: {admin_data.get('approved', 0)}")
        digest_parts.append(f"Payment Pending: {admin_data.get('payment_pending', 0)}")
        
        if admin_data.get('recent_registrations'):
            digest_parts.append("\n🆕 Recent Registrations:")
            for reg in admin_data['recent_registrations'][:5]:  # Show latest 5
                digest_parts.append(f"• {reg.get('alias', 'Unknown')} ({reg.get('submission_id', 'N/A')})")
        
        return "\n".join(digest_parts) 