from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

class RegistrationStatus(Enum):
    FORM_INCOMPLETE = "form_incomplete"
    WAITING_FOR_PARTNER = "waiting_for_partner"
    PARTNER_REMINDER_SENT = "partner_reminder_sent"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_CONFIRMED = "payment_confirmed"
    GROUP_OPENED = "group_opened"
    CANCELLED = "cancelled"

@dataclass
class StepProgress:
    form: bool = False
    partner: bool = False
    get_to_know: bool = False
    approved: bool = False
    paid: bool = False
    group_access: bool = False

@dataclass
class RegistrationData:
    submission_id: str
    telegram_user_id: str
    user_name: str
    partner_name: Optional[str] = None
    status: RegistrationStatus = RegistrationStatus.FORM_INCOMPLETE
    step_progress: Optional[StepProgress] = None
    form_data: Optional[Dict[str, str]] = None
    vibe_data: Optional[Dict[str, str]] = None
    admin_notes: str = ""
    last_updated: str = ""
    language: str = "en"
    
    def __post_init__(self):
        if self.step_progress is None:
            self.step_progress = StepProgress()
        if self.form_data is None:
            self.form_data = {}
        if self.vibe_data is None:
            self.vibe_data = {}
    
@dataclass
class PartnerInfo:
    name: str
    status: str
    registration_complete: bool
    reminder_sent: bool = False
    telegram_linked: bool = False 