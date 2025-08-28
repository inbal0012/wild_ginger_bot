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

class Status(Enum):
    # pending, approved, rejected, cancelled, uninterested
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    UNINTERESTED = "uninterested"

class RegistrationStage(Enum):
    # form, partner form, get to know, payment, group, arrived
    FORM = "form"
    PARTNER_FORM = "partner_form"
    GET_TO_KNOW = "get_to_know"
    PAYMENT = "payment"
    GROUP = "group"
    ARRIVED = "arrived"

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
    get_to_know_status: str 
    group_status: str
    arrived: bool
    ginger_first_try: bool = True
    form_complete: bool = False
    
@dataclass
class PartnerInfo:
    name: str
    status: str
    registration_complete: bool
    reminder_sent: bool = False
    telegram_linked: bool = False 