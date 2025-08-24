"""
FormFlowService - Manages form state and flow for event registrations.
Handles step-by-step form progression, state management, and validation.
Uses configurable form definitions for easy customization.
"""

import asyncio
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from .base_service import BaseService
from .sheets_service import SheetsService
from .user_service import UserService
from .event_service import EventService
from .registration_service import RegistrationService
from .file_storage_service import FileStorageService
from telegram import Update, Bot
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode
from ..models.form_flow import (
    QuestionType, ValidationRuleType, FormState, ValidationRule,
    SkipConditionItem, SkipCondition, Text, QuestionOption, QuestionDefinition,
    ValidationResult, FormContext, FormStateData, FormProgress, FormData,
    UpdateableFieldDTO, UpdateResult
)
from ..models.registration import CreateRegistrationDTO, RegistrationStatus
from ..models.event import EventDTO
from ..utils.validate_social_link import validate_social_link
from ..utils.utils import str_to_Text
from ..config.form_config_loader import load_form_config

class FormState:
    """Represents the state of a form for a specific user."""
    
    def __init__(self, user_id: str, event_id: Optional[str] = None, language: str = "he"):
        self.user_id = user_id
        self.event_id = event_id
        self.registration_id = None
        self.language = language
        self.current_question = "language"
        self.answers: Dict[str, Any] = {}
        self.completed = False
        self.created_at = asyncio.get_event_loop().time()
        self.updated_at = asyncio.get_event_loop().time()
    
    def update_answer(self, step: str, answer: Any) -> None:
        """Update answer for a specific step."""
        self.answers[step] = answer
        self.current_question = step
        self.updated_at = asyncio.get_event_loop().time()
        
        if (step == "event_selection"):
            self.event_id = answer
        elif step == "language":
            self.language = answer
        elif (step == "would_you_like_to_register" and answer == "no"):
            self.completed = True
    
    def update_registration_id(self, registration_id: str) -> None:
        self.registration_id = registration_id
        self.updated_at = asyncio.get_event_loop().time()
        
    def update_current_question(self, question: str) -> None:
        self.current_question = question
        self.updated_at = asyncio.get_event_loop().time()
    
    def get_answer(self, step: str) -> Optional[Any]:
        """Get answer for a specific step."""
        return self.answers.get(step)
    
    def is_step_completed(self, step: str) -> bool:
        """Check if a specific step is completed."""
        return step in self.answers
    
    def get_completion_percentage(self) -> float:
        """Get form completion percentage."""
        total_steps = 37
        completed_steps = len(self.answers)
        return (completed_steps / total_steps) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FormState to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "event_id": self.event_id,
            "language": self.language,
            "current_question": self.current_question,
            "answers": self.answers,
            "completed": self.completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
    def get_language(self):
        return self.language
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormState':
        """Create FormState from dictionary."""
        form_state = cls(
            user_id=data["user_id"],
            event_id=data.get("event_id"),
            language=data.get("language", "he")
        )
        form_state.registration_id = data.get("registration_id")
        form_state.current_question = data.get("current_question", "language")
        form_state.answers = data.get("answers", {})
        form_state.completed = data.get("completed", False)
        form_state.created_at = data.get("created_at", asyncio.get_event_loop().time())
        form_state.updated_at = data.get("updated_at", asyncio.get_event_loop().time())
        return form_state


class FormFlowService(BaseService):
    """
    Service for managing form flow and state.
    Handles step-by-step form progression, state management, and validation.
    Uses configurable form definitions for easy customization.
    """
    
    def __init__(self, sheets_service: SheetsService, config_source: str = "python"):
        """Initialize the form flow service."""
        super().__init__()
        self.sheets_service = sheets_service
        self.file_storage = FileStorageService()
        self.user_service = UserService(sheets_service)
        self.event_service = EventService(sheets_service)
        self.registration_service = RegistrationService(sheets_service)
        self.active_forms: Dict[str, FormState] = self.get_active_forms()
        
        # Load configuration
        self.config_loader = load_form_config(config_source)
        self.question_definitions = self.config_loader.load_question_definitions()
        self.extra_texts: Dict[str, Text] = self.config_loader.load_extra_texts()
        
        # Validate configuration
        validation_result = self.config_loader.validate_config()
        if not validation_result["valid"]:
            self.log_error(f"Configuration validation failed: {validation_result['errors']}")
        if validation_result["warnings"]:
            self.log_warning(f"Configuration warnings: {validation_result['warnings']}")
            
    def set_telegram_bot(self, bot: Bot):
        self.bot = bot
    
    def parse_upcoming_events(self) -> List[QuestionOption]:
        """Parse upcoming events from the sheets service."""
        events = self.event_service.get_upcoming_events()
        
        return [QuestionOption(value=event.id, text=Text(he=f"{event.start_date} - {event.name} ({event.event_type})", en=f"{event.start_date} - {event.name} ({event.event_type})")) for event in events]
    
    def parse_DM_shifts(self) -> List[QuestionOption]:
        """Parse DM shifts from the sheets service."""
        # TODO
        return [
            QuestionOption(value="first", text=Text(he="21:00-1:00", en="21:00-1:00")),
            QuestionOption(value="second", text=Text(he="01:00-4:00", en="01:00-4:00")),
        ]
        
        shifts = self.event_service.get_DM_shifts()
        return [QuestionOption(value=shift.id, text=Text(he=f"{shift.start_date} - {shift.name}", en=f"{shift.start_date} - {shift.name}")) for shift in shifts]
    
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
        try:
            # Check if user already has an active form
            if user_id in self.active_forms:
                self.log_info(f"User {user_id} already has an active form")
                form_state = self.active_forms[user_id]
            else:
                # Create new form state
                form_state = FormState(user_id, event_id, language)
                self.active_forms[user_id] = form_state
                
                # Save to storage
                self.save_active_forms()
            
            # Get the first question (language selection)
            first_question_def = self.question_definitions.get("language")
            if not first_question_def:
                raise ValueError("Language question definition not found")
            
            return first_question_def
            
        except Exception as e:
            self.log_error(f"Error starting form for user {user_id}: {e}")
            return None
    
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
            form_state.current_question, answer, form_state
        )
        
        if not validation_result["valid"]:
            return {
                "error": True,
                "message": validation_result["message"],
                "question": await self._get_question(form_state.current_question, form_state)
            }
        
        # Save answer
        form_state.update_answer(form_state.current_question, answer)
        
        # Move to next step
        next_step = await self._get_next_step(form_state.current_question, answer, form_state)
        form_state.current_question = next_step
        
        # Save to storage after any changes
        self.save_active_forms()
        
        if next_step == False:
            # Form completed
            form_state.completed = True
            return await self._complete_form(form_state)
        else:
            # Get next question
            next_question = await self._get_question(next_step, form_state)
            return {
                "form_id": f"{form_state.user_id}_{form_state.event_id}",
                "current_question": next_step,
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
    
    async def handle_poll_answer(self, question_field: str, user_id: str, selected_options: List[int]):
        """Handle poll answer from Telegram."""
        try:
            # Get the form state for this user
            form_state = self.active_forms.get(str(user_id))
            if not form_state:
                self.log_error(f"No active form found for user {user_id}")
                return
            
            # Get the question definition
            if question_field not in self.question_definitions:
                self.log_error(f"Question field {question_field} not found in definitions")
                return
            
            question_def = self.question_definitions[question_field]
            
            # Convert selected options to answer values
            answer_values = []
            for option_id in selected_options:
                if option_id < len(question_def.options):
                    answer_values.append(question_def.options[option_id].value)
            
            # For single select, take the first value
            answer = answer_values[0] if len(answer_values) == 1 else answer_values
            
            # Validate the answer
            validation_result = await self._validate_question_answer(question_def, answer, form_state)
            if not validation_result["valid"]:
                self.log_error(f"Validation failed for user {user_id}: {validation_result['message']}")
                return
            
            # Update form state with the answer
            form_state.update_answer(question_field, answer)
            
            # Save answer to the appropriate table
            await self.save_answer_to_sheets(str(user_id), question_field, answer)
            
            # Save form state
            self.save_active_forms()
            
            # Get next question or complete form
            next_question = await self._get_next_question_for_field(question_field, form_state)
            return next_question
            
        except Exception as e:
            self.log_error(f"Error handling poll answer for user {user_id}: {e}")
            return None
    
    async def handle_text_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text answer from Telegram."""
        user_id = update.effective_user.id
        try:
            # Get the form state for this user
            form_state = self.active_forms.get(str(user_id))
            if not form_state:
                self.log_error(f"No active form found for user {user_id}")
                return
            
            question_field = form_state.current_question
            # Get the question definition
            if question_field not in self.question_definitions:
                self.log_error(f"Question field {question_field} not found in definitions")
                return
            
            question_def = self.question_definitions[question_field]
            
            # For single select, take the first value
            answer = update.message.text
            
            if answer == "המשך" or answer == "continue":
                self.log_info(f"User {user_id} skipped question {question_field}")
            else:
                # Validate the answer
                validation_result = await self._validate_question_answer(question_def, answer, form_state)
                if not validation_result["valid"]:
                    self.log_error(f"Validation failed for user {user_id}: {validation_result['message']}")
                    return validation_result
            
            # Update form state with the answer
            form_state.update_answer(question_field, answer)
            
            # Save answer to the appropriate table
            await self.save_answer_to_sheets(str(user_id), question_field, answer)
            
            # Save form state
            self.save_active_forms()
            
            # Get next question or complete form
            next_question = await self._get_next_question_for_field(question_field, form_state)
            return next_question
            
        except Exception as e:
            self.log_error(f"Error handling text answer for user {user_id}: {e}")
            return None
    
    async def _validate_question_answer(self, question_def: QuestionDefinition, answer: Any, form_state: FormState) -> Dict[str, Any]:
        """Validate answer for a specific question."""
        try:
            # Check if required
            if question_def.required and (answer is None or answer == ""):
                return {
                    "valid": False,
                    "message": question_def.validation_rules[0].error_message.get(form_state.language, "Required field")
                }
            
            # Apply validation rules
            for rule in question_def.validation_rules:
                if rule.rule_type == ValidationRuleType.REQUIRED:
                    if not answer or answer == "":
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Required field")
                        }
                
                elif rule.rule_type == ValidationRuleType.DATE_RANGE:
                    if not re.match(r'^(\d{2})/(\d{2})/(\d{4})$', answer):
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Invalid date")
                        }
                        
                elif rule.rule_type == ValidationRuleType.AGE_RANGE:
                    if not self._validate_age_range(answer, rule.params):
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Invalid age")
                        }
                        
                elif rule.rule_type == ValidationRuleType.MIN_LENGTH:
                    if len(str(answer)) < rule.params.get("min", 0):
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Too short")
                        }
                
                elif rule.rule_type == ValidationRuleType.MAX_LENGTH:
                    if len(str(answer)) > rule.params.get("max", 1000):
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Too long")
                        }
                elif rule.rule_type == ValidationRuleType.TELEGRAM_LINK:
                    # https://t.me/username OR @username
                    if not re.match(r'^https?://t\.me/[a-zA-Z0-9_]+$', answer) and not re.match(r'^@[a-zA-Z0-9_]+$', answer):
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Invalid Telegram link")
                        }
                elif rule.rule_type == ValidationRuleType.FACEBOOK_LINK:
                    validation_result = validate_social_link(answer)
                    if not validation_result.is_valid:
                        return {
                            "valid": False,
                            "message": rule.error_message.get(form_state.language, "Invalid Facebook link")
                        }
                        
                elif rule.rule_type == ValidationRuleType.REGEX:
                    try:
                        pattern = rule.params.get("regex")
                        text = str(answer or "")
                        reg = re.search(pattern, text)
                        if reg is None:
                            self.set_ginger_first_try(form_state.registration_id, False)
                            return {
                                    "valid": False,
                                    "message": rule.error_message.get(form_state.language, "Invalid answer")
                                }
                    except Exception as e:
                        self.log_error(f"Error validating answer: {e}")
                        return {"valid": False, "message": "Validation error"}
            
            return {"valid": True, "message": ""}
            
        except Exception as e:
            self.log_error(f"Error validating answer: {e}")
            return {"valid": False, "message": "Validation error"}
        
    def _validate_age_range(self, birth_date_str: str, params: Dict[str, Any]) -> bool:
        """Validate age range from birth date."""
        try:
            birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y")
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            min_age = params.get("min_age", 18)
            max_age = params.get("max_age", 100)
            
            return min_age <= age <= max_age
        except (ValueError, TypeError):
            return False
    
    def set_ginger_first_try(self, registration_id: str, value: bool):
        """Set ginger first try for a user."""
        self.registration_service.set_ginger_first_try(registration_id, value)

    async def _get_next_question_for_field(self, current_field: str, form_state: FormState) -> Optional[Dict[str, Any]]:
        """Get the next question after answering a specific field."""
        try:
            # Get the order of the current field
            current_question = self.question_definitions.get(current_field)
            if not current_question:
                return None
            
            current_order = current_question.order
                        
            # Check if this is the last question (order 37)
            if current_order >= len(self.question_definitions):
                return await self._complete_form(form_state)
            
            # Find the next question in order
            next_question = None
            for field_name, question_def in self.question_definitions.items():
                if question_def.order > current_order:
                    # Check if this question should be skipped
                    if not await self._should_skip_question(question_def, form_state):
                        next_question = question_def
                        break
            
            if next_question:
                await self.extra_text_to_send(next_question, form_state)
                form_state.current_question = next_question.question_id
                self.save_active_forms()
                return next_question
            else:
                # Form is complete
                return await self._complete_form(form_state)
                
        except Exception as e:
            self.log_error(f"Error getting next question: {e}")
            return None
    
    async def extra_text_to_send(self, question_def: QuestionDefinition, form_state: FormState) -> str:
        """Get extra text to send for a specific question."""
        if question_def.question_id in self.extra_texts:
            await self.send_telegram_text_message(self.extra_texts[question_def.question_id].get(form_state.language), form_state.language, form_state.user_id)
            
        if question_def.question_id == "would_you_like_to_register":
            # sent event details
            event_details = await self._get_event_details(form_state.event_id)
            description = self.get_event_description(event_details)
            await self.send_telegram_text_message(description, form_state.language, form_state.user_id)
        elif question_def.question_id == "agree_participant_commitment":
            event_details = await self._get_event_details(form_state.event_id)
            await self.send_telegram_text_message(event_details.participant_commitment, form_state.language, form_state.user_id)
        elif question_def.question_id == "agree_line_rules":
            event_details = await self._get_event_details(form_state.event_id)
            await self.send_telegram_text_message(event_details.line_rules, form_state.language, form_state.user_id)
        elif question_def.question_id == "agree_place_rules":
            event_details = await self._get_event_details(form_state.event_id)
            await self.send_telegram_text_message(event_details.place_rules, form_state.language, form_state.user_id)
    
    async def send_telegram_text_message(self, text: str, language: str, user_id: str):
        """Send a text message to a user."""
        try:    
            await self.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            self.log_error(f"Error sending text message to user {user_id}: {e}")
    
    def get_event_description(self, event_details: EventDTO) -> str:
        """Get event description from event details."""
        return f'''
י Wild Ginger גאים להציג:
{event_details.name}
יום {event_details.start_date}, {event_details.start_time}-{event_details.end_time}, ב {event_details.location}

{event_details.schedule}

{event_details.description}


מחיר:
השתתפות בתשלום לצורך כיסוי עלויות.
-> זוג - {event_details.price_couple} ₪ לזוג
-> נשים / גברים / א-בינאריים יחידימות - {event_details.price_single} ₪ ליחיד

מחיר השתתפות כולל:
{event_details.price_include}

אלכוהול בתוספת תשלום.

ניתן להוזיל את המחיר ע"י הצטרפות לצוות כהלפר ו/או דיאמ (פרטים בעמוד האחרון)


* ההרשמה באיזון משחקי. (כלומר מישהו שאתם מתכוונים לשחק איתו)
אנו מברכים שילובים או עירבובים לפי רצון המשתתפים. אך מצפים שתביאו חטיף מהבית ולא שתבואו לצוד באירוע.
** כל אירועינו הינם להטבק פרנדלי, ואנו עושות את המיטב כדי לייצר מרחב נעים ומזמין לאנשימות מכל הקשת. 🏳️‍🌈💖
*** הרשמה בטופס זה אינה מהווה אישור הגעה. זאת הזמנה ובדיקת עניין בלבד. במידה ויש התאמה נחזור אליך. 🙃😊

    '''
    
    async def _should_skip_question(self, question_def: QuestionDefinition, form_state: FormState) -> bool:
        """Check if a question should be skipped based on conditions."""
        if not question_def.skip_condition:
            return False
        
        try:
            for condition in question_def.skip_condition.conditions:
                if condition.type == "field_value":
                    field_value = form_state.get_answer(condition.field)
                    if condition.operator == "equals":
                        if field_value == condition.value or (not field_value) or field_value == "":
                            return True
                    elif condition.operator == "not_in":
                        if field_value not in condition.value:
                            return True
                
                elif condition.type == "user_exists":
                    # Check if user exists in sheets
                    user_data = self.user_service.get_user_by_telegram_id(form_state.user_id)
                    if user_data:
                        if user_data[self.user_service.headers[question_def.question_id]] == condition.value:
                            return True
                
                elif condition.type == "event_type":
                    # Check event type
                    event_type = await self._get_event_type(form_state.event_id)
                    if condition.operator == "equals" and event_type == condition.value:
                        return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error checking skip condition: {e}")
            return False
    
    async def save_answer_to_sheets(self, user_id: str, question_field: str, answer: Any) -> bool:
        """
        Save answer to the appropriate table based on the question's save_to field.
        
        Args:
            user_id: User identifier
            question_field: Question field name
            answer: User's answer
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Get the question definition
            question_def = self.question_definitions.get(question_field)
            if not question_def:
                self.log_error(f"Question definition not found for field {question_field}")
                return False
            
            if question_def.question_id == "event_selection":
                return await self.save_event_selection_to_sheets(user_id, answer)
            elif question_def.question_id == "relevent_experience":
                event_type = await self._get_event_type(self.active_forms[user_id].event_id)
                answer = str({event_type: answer})
            
            # Determine which table to save to based on save_to field
            if question_def.save_to == "Users":
                # Save to users table
                success = self.sheets_service.update_cell(user_id, "telegram_user_id", "Users", question_field, answer)
            else:
                # Save to registration table
                # TODO get reg_id from user_id
                form = self.active_forms[user_id]
                event_id = form.event_id
                reg_id = self.registration_service.get_registration_id_by_user_id(user_id, event_id)
                if not reg_id:
                    self.log_error(f"No registration found for user {user_id}, event {event_id}")
                    return False
                success = self.sheets_service.update_cell(reg_id, "registration_id", "Registrations", question_field, answer)
            
            if success:
                self.log_info(f"Saved answer for user {user_id}, field {question_field} to {question_def.save_to} table")
            else:
                self.log_error(f"Failed to save answer for user {user_id}, field {question_field} to {question_def.save_to} table")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error saving answer to sheets: {e}")
            return False
    
    async def save_event_selection_to_sheets(self, user_id: str, event_id: Any) -> bool:
        """
        Save event selection to the appropriate table based on the question's save_to field.
        """
        # TODO make sure the event_id is valid
        # TODO make sure the user_id is valid
        # TODO make sure the user is not already registered for this event
        registration = CreateRegistrationDTO(user_id=user_id, event_id=event_id, status=RegistrationStatus.FORM_INCOMPLETE)
        result = await self.registration_service.create_new_registration(registration)
        if not result:
            self.log_error(f"Failed to save event selection to sheets for user {user_id}, event {event_id}")
            return False
        
        self.active_forms[user_id].registration_id = registration.id
        self.save_active_forms()
        return result
    
    async def validate_telegram_username(self, username: str) -> Tuple[bool, str]:
        """
        Validate Telegram username format.
        
        Args:
            username: Telegram username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # TODO: Implement Telegram username validation
        pass
    
    async def _get_event_details(self, event_id: str) -> EventDTO:
        """Get event details from sheets."""
        # TODO: Implement actual event details retrieval
        return self.event_service.get_event_by_id(event_id)
    
    async def _get_event_type(self, event_id: str) -> str:
        """Get event type from sheets."""
        # TODO: Implement actual event type retrieval
        return "play"  # Default for testing
    
    async def _complete_form(self, form_state: FormState) -> Dict[str, Any]:
        """Handle form completion."""
        try:
            # Mark form as completed
            form_state.completed = True
            self.save_active_forms()
            
            # Send completion message
            completion_text = self.extra_texts["completion"].get(form_state.language, self.extra_texts["completion"]["he"])
            await self.send_telegram_text_message(completion_text, form_state.language, form_state.user_id)
            
            # Update registration status to completed
            if form_state.registration_id:
                await self.registration_service.update_registration_status(
                    form_state.registration_id, 
                    RegistrationStatus.COMPLETED
                )
            
            return {
                "completed": True,
                "form_id": f"{form_state.user_id}_{form_state.event_id}",
                "answers": form_state.answers,
                "message": {
                    "he": "תודה על ההרשמה! נציג יצור איתך קשר בקרוב.",
                    "en": "Thank you for registering! A representative will contact you soon."
                }
            }
        except Exception as e:
            self.log_error(f"Error completing form for user {form_state.user_id}: {e}")
            return {
                "completed": False,
                "error": True,
                "message": {
                    "he": "אירעה שגיאה בהשלמת הטופס. אנא נסה שוב.",
                    "en": "An error occurred while completing the form. Please try again."
                }
            } 