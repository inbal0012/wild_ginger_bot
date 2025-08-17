from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

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
class CreateRegistrationDTO:
    user_id: str
    event_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = RegistrationStatus.FORM_INCOMPLETE.value

@dataclass
class RegistrationData:
    id: str
    event_id: str
    user_id: str
    status: str
    partner_telegram_link: str
    payment_status: str
    payment_method: str
    registration_date: str
    payment_date: str
    partner_or_single: str
    intro_opt_in: str
    intro_text: str
    intro_posted_at: str
    created_at: str
    updated_at: str
    would_you_like_to_register: bool
    last_sti_test: str
    bdsm_declaration: bool
    is_play_with_partner_only: bool
    desired_play_partners: str
    contact_type: str
    contact_type_other: str
    share_bdsm_interests: bool
    alcohol_in_event: str # yes / no / maybe
    agree_participant_commitment: bool
    enthusiastic_verbal_consent_commitment: bool
    agree_line_rules: bool
    wants_to_helper: bool
    helper_shifts: str
    wants_to_DM: bool
    DM_shifts: str
    
@dataclass
class PartnerInfo:
    name: str
    status: str
    registration_complete: bool
    reminder_sent: bool = False
    telegram_linked: bool = False 