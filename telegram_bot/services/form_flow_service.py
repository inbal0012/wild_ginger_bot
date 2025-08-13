"""
FormFlowService - Manages form state and flow for event registrations.
Handles step-by-step form progression, state management, and validation.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from .base_service import BaseService
from .sheets_service import SheetsService
from .file_storage_service import FileStorageService
from forms.generic_form import GenericForm


class FormStep(Enum):
    """Enumeration of form steps."""
    LANGUAGE_SELECTION = "language_selection"
    EVENT_DETAILS = "event_details"
    PERSONAL_INFO = "personal_info"
    EVENT_SPECIFIC = "event_specific"
    FOOD_ALCOHOL = "food_alcohol"
    RULES_AGREEMENT = "rules_agreement"
    HELPERS_DM = "helpers_dm"
    THEME = "theme"
    COMPLETION = "completion"


class FormState:
    """Represents the state of a form for a specific user."""
    
    def __init__(self, user_id: str, event_id: Optional[str] = None, language: str = "he"):
        self.user_id = user_id
        self.event_id = event_id
        self.language = language
        self.current_step = FormStep.LANGUAGE_SELECTION
        self.answers: Dict[str, Any] = {}
        self.completed = False
        self.created_at = asyncio.get_event_loop().time()
        self.updated_at = asyncio.get_event_loop().time()
    
    def update_answer(self, step: str, answer: Any) -> None:
        """Update answer for a specific step."""
        self.answers[step] = answer
        self.updated_at = asyncio.get_event_loop().time()
    
    def get_answer(self, step: str) -> Optional[Any]:
        """Get answer for a specific step."""
        return self.answers.get(step)
    
    def is_step_completed(self, step: str) -> bool:
        """Check if a specific step is completed."""
        return step in self.answers
    
    def get_completion_percentage(self) -> float:
        """Get form completion percentage."""
        total_steps = len(FormStep)
        completed_steps = len(self.answers)
        return (completed_steps / total_steps) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FormState to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "event_id": self.event_id,
            "language": self.language,
            "current_step": self.current_step.value,
            "answers": self.answers,
            "completed": self.completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormState':
        """Create FormState from dictionary."""
        form_state = cls(
            user_id=data["user_id"],
            event_id=data.get("event_id"),
            language=data.get("language", "he")
        )
        form_state.current_step = FormStep(data["current_step"])
        form_state.answers = data.get("answers", {})
        form_state.completed = data.get("completed", False)
        form_state.created_at = data.get("created_at", asyncio.get_event_loop().time())
        form_state.updated_at = data.get("updated_at", asyncio.get_event_loop().time())
        return form_state


class FormFlowService(BaseService):
    """
    Service for managing form flow and state.
    Handles step-by-step form progression, state management, and validation.
    """
    
    
    def __init__(self, sheets_service: SheetsService):
        """Initialize the form flow service."""
        super().__init__()
        self.sheets_service = sheets_service
        self.file_storage = FileStorageService()
        self.active_forms: Dict[str, FormState] = self.get_active_forms()
        
    def get_active_forms(self) -> Dict[str, FormState]:
        """Get all active forms from file storage."""
        try:
            forms_data = self.file_storage.load_data("active_forms", {})
            active_forms = {}
            
            for user_id, form_dict in forms_data.items():
                try:
                    active_forms[user_id] = FormState.from_dict(form_dict)
                except Exception as e:
                    self.log_error(f"Error loading form state for user {user_id}: {e}")
                    continue
            
            self.log_info(f"Loaded {len(active_forms)} active forms from storage")
            return active_forms
            
        except Exception as e:
            self.log_error(f"Error loading active forms: {e}")
            return {}
    
    def save_active_forms(self) -> bool:
        """Save active forms to file storage."""
        try:
            forms_data = {}
            for user_id, form_state in self.active_forms.items():
                forms_data[user_id] = form_state.to_dict()
            
            success = self.file_storage.save_data("active_forms", forms_data)
            if success:
                self.log_info(f"Saved {len(self.active_forms)} active forms to storage")
            return success
            
        except Exception as e:
            self.log_error(f"Error saving active forms: {e}")
            return False
    
    async def initialize(self) -> None:
        """Initialize form flow service."""
        self.log_info("Initializing FormFlowService")
        pass
    
    async def shutdown(self) -> None:
        """Clean up form flow service resources."""
        self.log_info("Shutting down FormFlowService")
        pass
    
    async def start_form(self, user_id: str, event_id: Optional[str] = None, language: str = "he") -> Dict[str, Any]:
        """
        Start a new form for a user.
        
        Args:
            user_id: User identifier
            event_id: Event identifier
            language: Preferred language (he/en)
            
        Returns:
            Dictionary with first question and form metadata
        """
        # is returning user?
        self.sheets_service.find_submission_by_telegram_id(user_id)
        
        # Create new form state
        form_state = FormState(user_id, event_id, language)
        self.active_forms[user_id] = form_state
        
        # Save to storage
        self.save_active_forms()
        
        # Get first question
        first_question = await self._get_question(FormStep.LANGUAGE_SELECTION, form_state)
        
        return {
            "form_id": f"{user_id}_{event_id}",
            "current_step": FormStep.LANGUAGE_SELECTION.value,
            "question": first_question,
            "progress": 0.0
        }
    
    async def process_answer(self, user_id: str, answer: Any) -> Dict[str, Any]:
        """
        Process user answer and return next question.
        
        Args:
            user_id: User identifier
            answer: User's answer
            
        Returns:
            Dictionary with next question or completion status
        """
        if user_id not in self.active_forms:
            raise ValueError(f"No active form found for user {user_id}")
        
        form_state = self.active_forms[user_id]
        
        # Validate current step answer
        validation_result = await self._validate_step_answer(
            form_state.current_step, answer, form_state
        )
        
        if not validation_result["valid"]:
            return {
                "error": True,
                "message": validation_result["message"],
                "question": await self._get_question(form_state.current_step, form_state)
            }
        
        # Save answer
        form_state.update_answer(form_state.current_step.value, answer)
        
        # Move to next step
        next_step = await self._get_next_step(form_state.current_step, answer, form_state)
        form_state.current_step = next_step
        
        # Save to storage after any changes
        self.save_active_forms()
        
        if next_step == FormStep.COMPLETION:
            # Form completed
            form_state.completed = True
            return await self._complete_form(form_state)
        else:
            # Get next question
            next_question = await self._get_question(next_step, form_state)
            return {
                "form_id": f"{form_state.user_id}_{form_state.event_id}",
                "current_step": next_step.value,
                "question": next_question,
                "progress": form_state.get_completion_percentage()
            }
    
    async def get_form_state(self, user_id: str) -> Optional[FormState]:
        """
        Get current form state for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Form state or None if not found
        """
        return self.active_forms.get(user_id)
    
    async def _get_question(self, step: FormStep, form_state: FormState) -> Dict[str, Any]:
        """Get question for a specific step."""
        if step == FormStep.LANGUAGE_SELECTION:
            return GenericForm.all_fields_dict["language"]
        
        elif step == FormStep.EVENT_DETAILS:
            # Get event details from sheets
            event_details = await self._get_event_details(form_state.event_id)
            return {
                "type": "event_info",
                "event": event_details,
                "text": {
                    "he": "האם תרצה/י להרשם לאירוע זה?",
                    "en": "Would you like to register for this event?"
                },
                "options": [
                    {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                    {"value": "no", "text": {"he": "לא", "en": "No"}}
                ],
                "required": True
            }
        
        elif step == FormStep.PERSONAL_INFO:
            return {
                "type": "personal_info",
                "fields": [
                    {
                        "name": "full_name",
                        "type": "text",
                        "label": {"he": "שם מלא", "en": "Full Name"},
                        "required": True
                    },
                    {
                        "name": "telegram_username",
                        "type": "text",
                        "label": {"he": "שם משתמש בטלגרם", "en": "Telegram Username"},
                        "placeholder": {"he": "@username או t.me/username", "en": "@username or t.me/username"},
                        "required": True
                    },
                    {
                        "name": "previous_participation",
                        "type": "choice",
                        "label": {"he": "האם השתתפת בעבר באירועי Wild Ginger?", "en": "Have you participated in Wild Ginger events before?"},
                        "options": [
                            {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                            {"value": "no", "text": {"he": "לא", "en": "No"}}
                        ],
                        "required": True
                    },
                    {
                        "name": "balance_status",
                        "type": "choice",
                        "label": {"he": "האם מגיע/ה לבד או באיזון?", "en": "Are you coming alone or with a partner?"},
                        "options": [
                            {"value": "single", "text": {"he": "לבד", "en": "Alone"}},
                            {"value": "partner", "text": {"he": "באיזון", "en": "With Partner"}}
                        ],
                        "required": True
                    }
                ]
            }
        
        # Add more steps as needed...
        return {"type": "unknown", "text": "Unknown step"}
    
    async def _get_next_step(self, current_step: FormStep, answer: Any, form_state: FormState) -> FormStep:
        """Determine the next step based on current step and answer."""
        if current_step == FormStep.LANGUAGE_SELECTION:
            form_state.language = answer
            return FormStep.EVENT_DETAILS
        
        elif current_step == FormStep.EVENT_DETAILS:
            if answer == "no":
                return FormStep.COMPLETION
            return FormStep.PERSONAL_INFO
        
        elif current_step == FormStep.PERSONAL_INFO:
            # Check if event-specific questions are needed
            event_type = await self._get_event_type(form_state.event_id)
            if event_type == "play":
                return FormStep.EVENT_SPECIFIC
            else:
                return FormStep.FOOD_ALCOHOL
        
        # Add more step logic...
        return FormStep.COMPLETION
    
    async def _validate_step_answer(self, step: FormStep, answer: Any, form_state: FormState) -> Dict[str, Any]:
        """Validate answer for a specific step."""
        if step == FormStep.LANGUAGE_SELECTION:
            if answer not in ["he", "en"]:
                return {
                    "valid": False,
                    "message": {"he": "אנא בחר/י שפה", "en": "Please select a language"}
                }
        
        elif step == FormStep.TELEGRAM_USERNAME:
            # Validate Telegram username format
            is_valid, error_msg = self.validate_telegram_username(answer)
            if not is_valid:
                return {
                    "valid": False,
                    "message": {"he": error_msg, "en": error_msg}
                }
        
        return {"valid": True, "message": ""}
    
    async def _get_event_details(self, event_id: str) -> Dict[str, Any]:
        """Get event details from sheets."""
        # TODO: Implement actual event details retrieval
        return {
            "id": event_id,
            "title": {"he": "אירוע לדוגמה", "en": "Sample Event"},
            "date": "2024-02-15",
            "time": "21:00-04:00",
            "location": {"he": "תל אביב", "en": "Tel Aviv"},
            "pricing": {
                "single": 100,
                "couple": 200
            }
        }
    
    async def _get_event_type(self, event_id: str) -> str:
        """Get event type from sheets."""
        # TODO: Implement actual event type retrieval
        return "play"  # Default for testing
    
    async def _complete_form(self, form_state: FormState) -> Dict[str, Any]:
        """Handle form completion."""
        return {
            "completed": True,
            "form_id": f"{form_state.user_id}_{form_state.event_id}",
            "answers": form_state.answers,
            "message": {
                "he": "תודה על ההרשמה! נציג יצור איתך קשר בקרוב.",
                "en": "Thank you for registering! A representative will contact you soon."
            }
        } 
        
    
    def validate_telegram_username(self, username: str) -> Tuple[bool, str]:
        """
        Validate Telegram username format.
        
        Args:
            username: Telegram username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # TODO: Implement Telegram username validation
        pass
    