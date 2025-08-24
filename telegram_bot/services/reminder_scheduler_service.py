from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from telegram_bot.services.reminder_service import ReminderService
from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.services.admin_service import AdminService


# --- Automatic Reminder System ---
class ReminderScheduler:
    """Handles automatic reminders based on time and user state"""
    
    def __init__(self, bot_application, reminder_service: ReminderService = None, sheets_service: SheetsService = None, admin_service: AdminService = None):
        self.bot = bot_application
        self.reminder_service = reminder_service or ReminderService()
        self.sheets_service = sheets_service or SheetsService()
        self.admin_service = admin_service or AdminService()
        self.reminder_intervals = {
            'partner_pending': 24 * 60 * 60,  # 24 hours in seconds
            'payment_pending': 3 * 24 * 60 * 60,  # 3 days
            'group_opening': 7 * 24 * 60 * 60,  # 7 days before event
            'event_reminder': 24 * 60 * 60,  # 1 day before event
            'weekly_digest': 7 * 24 * 60 * 60,  # 7 days
        }
        self.last_reminder_check = {}
        self.last_weekly_digest = None
        
    def quick_completion_check(self, row, column_indices):
        """Quick check if user needs any reminders without expensive parsing"""
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
        
        # Get essential info without expensive parsing
        submission_id = get_cell_value('submission_id')
        telegram_user_id = get_cell_value('telegram_user_id')
        
        if not submission_id or not telegram_user_id:
            return None  # Can't process without these
        
        # Check completion status
        partner_complete = get_boolean_value('partner_complete', False)
        approved = get_boolean_value('admin_approved', False)
        paid = get_boolean_value('payment_complete', False)
        group_open = get_boolean_value('group_access', False)
        
        return {
            'submission_id': submission_id,
            'telegram_user_id': telegram_user_id,
            'partner_complete': partner_complete,
            'approved': approved,
            'paid': paid,
            'group_open': group_open,
            'needs_reminders': not (partner_complete and approved and paid and group_open)
        }
    
    async def check_and_send_reminders(self):
        """Check all users and send appropriate reminders"""
        print("🔔 Checking for pending reminders...")
        
        # Get all sheet data
        sheet_data = self.sheets_service.get_sheet_data() 
        if not sheet_data:
            print("⚠️  No sheet data available for reminder checking")
            return
        
        headers = sheet_data['headers']
        rows = sheet_data['rows']
        column_indices = self.sheets_service.get_column_indices(headers)
        
        # Counters for efficiency tracking
        total_users = 0
        skipped_users = 0
        processed_users = 0
        reminders_sent = 0
        
        # Process each user
        for row in rows:
            try:
                # Quick pre-check without expensive parsing
                quick_check = self.quick_completion_check(row, column_indices)
                if not quick_check:
                    continue
                
                total_users += 1
                
                # Skip if user doesn't need any reminders
                if not quick_check['needs_reminders']:
                    skipped_users += 1
                    print(f"⏭️  Skipping {quick_check['submission_id']} - fully complete (quick check)")
                    continue
                
                # Only do expensive parsing if user needs reminders
                user_data = parse_submission_row(row, column_indices)
                if not user_data or not user_data.get('submission_id'):
                    continue
                
                processed_users += 1
                
                # Check if user needs reminders
                result = await self.check_user_reminders(user_data)
                
            except Exception as e:
                print(f"❌ Error processing reminder for row: {e}")
                continue
        
        print(f"📊 Reminder check summary: {total_users} users total, {skipped_users} skipped (quick check), {processed_users} processed")
        
        # Check if it's time for weekly digest
        await self.check_weekly_digest()
    
    async def check_user_reminders(self, user_data: Dict):
        """Check if a specific user needs any reminders"""
        submission_id = user_data.get('submission_id')
        telegram_user_id = user_data.get('telegram_user_id')
        user_name = user_data.get('alias', 'Unknown')
        
        if not telegram_user_id:
            return  # Can't send reminders without Telegram ID
        
        # Early exit if user is fully complete - no need to check any reminders
        if (user_data.get('partner', False) and 
            user_data.get('approved', False) and 
            user_data.get('paid', False) and 
            user_data.get('group_open', False)):
            print(f"⏭️  Skipping {user_name} - fully complete")
            return  # User is fully complete, no reminders needed
        
        # Check different reminder types (only if needed)
        if not user_data.get('partner', False):
            await self.check_partner_reminder(user_data)
        else:
            print(f"⏭️  Skipping partner check for {user_name} - partner complete")
        
        if user_data.get('approved', False) and not user_data.get('paid', False):
            await self.check_payment_reminder(user_data)
        
        if user_data.get('paid', False) and not user_data.get('group_open', False):
            await self.check_group_reminder(user_data)
        
        if user_data.get('group_open', False):
            await self.check_event_reminder(user_data)
    
    async def check_partner_reminder(self, user_data: Dict):
        """Check if user needs a partner reminder"""
        # Early exit if partner is already complete
        if user_data.get('partner', False):
            return  # Partner requirements already met
        
        submission_id = user_data.get('submission_id')
        partner_status = user_data.get('partner_status', {})
        missing_partners = partner_status.get('missing_partners', [])
        
        if not missing_partners:
            print(f"⏭️  No missing partners for {user_data.get('alias', 'Unknown')}")
            return  # No missing partners
        
        # Check if 24 hours have passed since last partner reminder
        last_reminder_key = f"{submission_id}_partner"
        now = datetime.now()
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (now - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['partner_pending']:
                print(f"⏭️  Too soon for partner reminder for {user_data.get('alias', 'Unknown')}")
                return  # Too soon for another reminder
        
        # Send partner reminder
        print(f"🔔 Sending partner reminder to {user_data.get('alias', 'Unknown')} for missing: {missing_partners}")
        await self.send_automatic_partner_reminder(user_data, missing_partners)
        self.last_reminder_check[last_reminder_key] = now
        
        # Also notify admins about the partner delay
        await self.admin_service.notify_partner_delay(
            submission_id=user_data.get('submission_id', 'Unknown'),
            user_name=user_data.get('alias', 'Unknown'),
            missing_partners=missing_partners
        )
    
    async def check_payment_reminder(self, user_data: Dict):
        """Check if user needs a payment reminder"""
        # Early exit conditions moved to check_user_reminders for efficiency
        submission_id = user_data.get('submission_id')
        last_reminder_key = f"{submission_id}_payment"
        now = datetime.now()
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (now - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['payment_pending']:
                return  # Too soon for another reminder
        
        # Send payment reminder
        await self.send_automatic_payment_reminder(user_data)
        self.last_reminder_check[last_reminder_key] = now
        
        # Calculate days since approval (simplified - in reality you'd track approval timestamp)
        days_overdue = 3  # Simplified - this would be calculated from actual approval date
        
        # Notify admins about payment overdue
        await notify_payment_overdue(
            submission_id=user_data.get('submission_id', 'Unknown'),
            user_name=user_data.get('alias', 'Unknown'),
            days_overdue=days_overdue
        )
    
    async def check_group_reminder(self, user_data: Dict):
        """Check if user needs a group opening reminder"""
        # Early exit conditions moved to check_user_reminders for efficiency
        
        # TODO: Check if it's 7 days before event
        # For now, simulate group opening reminder
        submission_id = user_data.get('submission_id')
        last_reminder_key = f"{submission_id}_group"
        now = datetime.now()
        
        if last_reminder_key in self.last_reminder_check:
            time_since_last = (now - self.last_reminder_check[last_reminder_key]).total_seconds()
            if time_since_last < self.reminder_intervals['group_opening']:
                return  # Too soon for another reminder
        
        # Send group opening reminder
        await self.send_automatic_group_reminder(user_data)
        self.last_reminder_check[last_reminder_key] = now
    
    async def check_event_reminder(self, user_data: Dict):
        """Check if user needs an event reminder"""
        if not user_data.get('group_open'):
            return  # Group not open yet
        
        # TODO: Check if it's 1 day before event
        # This would require event date information
        pass
    
    async def check_weekly_digest(self):
        """Check if it's time to send weekly digest to admins"""
        now = datetime.now()
        
        # Check if it's time for weekly digest (every 7 days)
        if self.last_weekly_digest:
            time_since_last = (now - self.last_weekly_digest).total_seconds()
            if time_since_last < self.reminder_intervals['weekly_digest']:
                return  # Too soon for another digest
        
        # Send weekly digest
        print("📊 Sending weekly admin digest...")
        await send_weekly_admin_digest()
        self.last_weekly_digest = now
    
    async def send_automatic_partner_reminder(self, user_data: Dict, missing_partners: List[str]):
        """Send automatic partner reminder"""
        telegram_user_id = user_data.get('telegram_user_id')
        language = user_data.get('language', 'en')
        
        if not telegram_user_id:
            return
        
        try:
            if language == 'he':
                if len(missing_partners) == 1:
                    message = f"🔔 תזכורת: עדיין מחכים ל{missing_partners[0]} להשלים את הטופס. רוצה לשלוח להם תזכורת? השתמש ב /remind_partner"
                else:
                    missing_names = ', '.join(missing_partners)
                    message = f"🔔 תזכורת: עדיין מחכים ל{missing_names} להשלים את הטופס. השתמש ב /remind_partner"
            else:
                if len(missing_partners) == 1:
                    message = f"🔔 Reminder: Still waiting for {missing_partners[0]} to complete the form. Want to send them a reminder? Use /remind_partner"
                else:
                    missing_names = ', '.join(missing_partners)
                    message = f"🔔 Reminder: Still waiting for {missing_names} to complete the form. Use /remind_partner"
            
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await self.reminder_service.log_reminder_sent(
                submission_id=user_data.get('submission_id'),
                partner_name=', '.join(missing_partners),
                reminder_type='automatic_partner_reminder'
            )
            
        except Exception as e:
            print(f"❌ Error sending automatic partner reminder: {e}")
    
    async def send_automatic_payment_reminder(self, user_data: Dict):
        """Send automatic payment reminder"""
        telegram_user_id = user_data.get('telegram_user_id')
        language = user_data.get('language', 'en')
        
        if not telegram_user_id:
            return
        
        try:
            if language == 'he':
                message = "💸 תזכורת תשלום: הרשמתך אושרה! אנא השלם את התשלום כדי לאשר את מקומך באירוע."
            else:
                message = "💸 Payment reminder: Your registration has been approved! Please complete payment to confirm your spot at the event."
            
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await self.reminder_service.log_reminder_sent(
                submission_id=user_data.get('submission_id'),
                partner_name='',
                reminder_type='automatic_payment_reminder'
            )
            
        except Exception as e:
            print(f"❌ Error sending automatic payment reminder: {e}")
    
    async def send_automatic_group_reminder(self, user_data: Dict):
        """Send automatic group opening reminder"""
        telegram_user_id = user_data.get('telegram_user_id')
        language = user_data.get('language', 'en')
        
        if not telegram_user_id:
            return
        
        try:
            if language == 'he':
                message = "👥 הקבוצה פתוחה! קבוצת האירוע שלך פתוחה עכשיו. בואו להכיר או פשוט לצפות בשקט - מה שמתאים לכם! 🧘"
            else:
                message = "👥 Group is open! Your event group is now open. Come meet others, share vibes, or just lurk quietly if that's your vibe! 🧘"
            
            await self.bot.bot.send_message(chat_id=telegram_user_id, text=message)
            
            # Log the reminder
            await self.reminder_service.log_reminder_sent(
                submission_id=user_data.get('submission_id'),
                partner_name='',
                reminder_type='automatic_group_reminder'
            )
            
        except Exception as e:
            print(f"❌ Error sending automatic group reminder: {e}")
