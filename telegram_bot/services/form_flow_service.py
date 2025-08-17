"""
FormFlowService - Manages form state and flow for event registrations.
Handles step-by-step form progression, state management, and validation.
"""

import asyncio
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
from ..models.form_flow import (
    QuestionType, ValidationRuleType, FormState, ValidationRule,
    SkipConditionItem, SkipCondition, Text, QuestionOption, QuestionDefinition,
    ValidationResult, FormContext, FormStateData, FormProgress, FormData,
    UpdateableFieldDTO, UpdateResult
)
from ..models.registration import CreateRegistrationDTO, RegistrationStatus
from ..models.event import EventDTO

class FormState:
    """Represents the state of a form for a specific user."""
    
    def __init__(self, user_id: str, event_id: Optional[str] = None, language: str = "he"):
        self.user_id = user_id
        self.event_id = event_id
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
    
    def get_answer(self, step: str) -> Optional[Any]:
        """Get answer for a specific step."""
        return self.answers.get(step)
    
    def is_step_completed(self, step: str) -> bool:
        """Check if a specific step is completed."""
        return step in self.answers
    
    def get_completion_percentage(self) -> float:
        """Get form completion percentage."""
        total_steps = 38
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
        self.user_service = UserService(sheets_service)
        self.event_service = EventService(sheets_service)
        self.registration_service = RegistrationService(sheets_service)
        self.active_forms: Dict[str, FormState] = self.get_active_forms()
        self.question_definitions = self._initialize_question_definitions()
            
    def set_telegram_bot(self, bot: Bot):
        self.bot = bot
    
    def _initialize_question_definitions(self) -> Dict[str, QuestionDefinition]:
        """Initialize question definitions following the form order specification."""
        # TODO move outside of the class (config file)
        return {
            # 1. Language selection (every time)
            "language": QuestionDefinition(
                question_id="language",
                question_type=QuestionType.SELECT,
                title=Text(
                    he="באיזו שפה תרצה למלא את הטופס?",
                    en="In which language would you like to fill the form?"),
                required=True,
                save_to="Users",
                order=1,
                options=[
                    QuestionOption(value="he", text=Text(he="עברית", en="Hebrew")),
                    QuestionOption(value="en", text=Text(he="English", en="English"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(
                            he="אנא בחר שפה",
                            en="Please select a language")
                    )
                ]
            ),
            # 2. Event selection (every time)
            "event_selection": QuestionDefinition(
                question_id="event_selection",
                question_type=QuestionType.SELECT,
                title=Text(he="לאיזה אירוע תרצה להירשם?", en="To which event would you like to register?"),
                required=True,
                save_to="Registrations",
                order=2,
                options=self.parse_upcoming_events(),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ]
            ),
            # 3. Event type
            "interested_in_event_types": QuestionDefinition(
                question_id="interested_in_event_types",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מה סוגי האירועים שתרצה להשתתף בהם?", en="What type of events would you like to participate in?"),
                required=True,
                save_to="Users",
                order=3,
                options=[
                    QuestionOption(value="play", text=Text(he="משחק", en="Play")),
                    QuestionOption(value="cuddle", text=Text(he="כירבולייה", en="Cuddle"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ]
            ),
            # 4. would you like to register?
            "would_you_like_to_register": QuestionDefinition(
                question_id="would_you_like_to_register",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם תרצה להירשם לאירוע?", en="Would you like to register to this event?"),
                required=True,
                save_to="Registrations",
                order=4,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ]
            ),
            # 5. Full name (new users only)
            "full_name": QuestionDefinition(
                question_id="full_name",
                question_type=QuestionType.TEXT,
                title=Text(he="מה השם המלא שלך?", en="What is your full name?"),
                required=True,
                save_to="Users",
                order=5,
                placeholder=Text(he="הזן שם מלא", en="Enter full name"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="telegram_id")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן את שמך המלא", en="Please enter your full name")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.MIN_LENGTH,
                        params={"min": 2},
                        error_message=Text(he="השם חייב להכיל לפחות 2 תווים", en="Name must contain at least 2 characters")
                    )
                ]
            ),
            # 6. relevent experience
            "relevent_experience": QuestionDefinition(
                question_id="relevent_experience",
                question_type=QuestionType.TEXT,
                title=Text(he="מה רמת הניסיון שלך באירועים דומים?", en="What is your experience with similar events?"),
                required=True,
                save_to="Users",
                order=6,
                placeholder=Text(he="למשל: משחק בכירבולייה, משחק במשחקים בודדים, משחק במשחקים בצניחה, משחק במשחקים במשחקים בכירבולייה", en="e.g., Play in cuddle, Play in solo, Play in cuddle, Play in bdsm, Play in bdsm in cuddle, Play in bdsm in solo"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן רמת ניסיון", en="Please enter experience")
                    )
                ]
            ),
            # 7. partner or single
            "partner_or_single": QuestionDefinition(
                question_id="partner_or_single",
                question_type=QuestionType.SELECT,
                title=Text(he="האם אתה/את מגיע/ה לבד או עם פרטנר?", en="Are you coming alone or with a partner?"),
                required=True,
                save_to="Registrations",
                order=7,
                options=[
                    QuestionOption(value="single", text=Text(he="לבד", en="Alone")),
                    QuestionOption(value="partner", text=Text(he="עם פרטנר", en="With partner"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 8. partner telegram link
            "partner_telegram_link": QuestionDefinition(
                question_id="partner_telegram_link",
                question_type=QuestionType.TELEGRAM_LINK,
                title=Text(he="אנא שתף לינק לטלגרם של הפרטנר שלך", en="Please share your partner's Telegram link"),
                required=True,
                save_to="Registrations",
                order=8,
                placeholder=Text(he="https://t.me/username", en="https://t.me/username"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="partner_or_single", value="single", operator="equals")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן לינק לטלגרם", en="Please enter Telegram link")
                    ),
                ]
            ),
            # 9. last_sti_test
            "last_sti_test": QuestionDefinition(
                question_id="last_sti_test",
                question_type=QuestionType.DATE,
                title=Text(he="מה התאריך של בדיקת המין האחרונה שלך?", en="What is the date of your last STI test?"),
                required=True,
                save_to="Registrations",
                order=9,
                placeholder=Text(he="DD/MM/YYYY", en="DD/MM/YYYY"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="event_type", value="cuddle", operator="equals")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן תאריך בדיקה", en="Please enter test date")
                    ),
                ]
            ),
            # 10. Facebook profile (new users only)
            "facebook_profile": QuestionDefinition(
                question_id="facebook_profile",
                question_type=QuestionType.FACEBOOK_LINK,
                title=Text(he="אנא שתף לינק לפרופיל הפייסבוק שלך", en="Please share a link to your Facebook profile"),
                required=True,
                save_to="Users",
                order=10,
                placeholder=Text(he="https://facebook.com/username", en="https://facebook.com/username"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="telegram_id")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן לינק לפייסבוק", en="Please enter Facebook link")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.FACEBOOK_LINK,
                        error_message=Text(he="הלינק אינו תקין. אנא הזן לינק תקין לפייסבוק", en="Invalid link. Please enter a valid Facebook link")
                    )
                ]
            ),
            # 11. Birth date (new users only)
            "birth_date": QuestionDefinition(
                question_id="birth_date",
                question_type=QuestionType.DATE,
                title=Text(he="מה תאריך הלידה שלך?", en="What is your birth date?"),
                required=True,
                save_to="Users",
                order=11,
                placeholder=Text(he="DD/MM/YYYY", en="DD/MM/YYYY"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="telegram_id")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן תאריך לידה", en="Please enter birth date")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.AGE_RANGE,
                        params={"min_age": 18, "max_age": 100},
                        error_message=Text(he="הגיל חייב להיות בין 18 ל-100", en="Age must be between 18 and 100")
                    )
                ]
            ),
            # 12. sexual_orientation_and_gender
            "sexual_orientation_and_gender": QuestionDefinition(
                question_id="sexual_orientation_and_gender",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הפרופיל המיני שלך?", en="What is your sexual orientation and gender?"),
                required=True,
                save_to="Users",
                order=12,
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 13. pronouns
            "pronouns": QuestionDefinition(
                question_id="pronouns",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הפרופיל המיני שלך?", en="What is your sexual orientation and gender?"),
                required=False,
                save_to="Users",
                order=13,
                placeholder=Text(he="למשל: זכר, נקבה, אחר", en="e.g., male, female, other"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 14. bdsm_experience
            "bdsm_experience": QuestionDefinition(
                question_id="bdsm_experience",
                question_type=QuestionType.SELECT,
                title=Text(he="מה רמת הניסיון שלך ב-BDSM?", en="What is your BDSM experience level?"),
                required=True,
                save_to="Users",
                order=14,
                options=[
                    QuestionOption(value="none_not_interested", text=Text(he="אין לי נסיון וגם לא מתעניין.ת בבדס\"מ", en="No experience and not interested in BDSM")),
                    QuestionOption(value="none_interested_top", text=Text(he="אין לי נסיון אבל מעניין אותי לנסות לשלוט", en="No experience but interested in trying to top")),
                    QuestionOption(value="none_interested_bottom", text=Text(he="אין לי נסיון אבל מעניין אותי לנסות להישלט", en="No experience but interested in trying to bottom")),
                    QuestionOption(value="experienced_top", text=Text(he="יש לי נסיון בתור טופ/שולט.ת", en="I have experience as a top/dominant")),
                    QuestionOption(value="experienced_bottom", text=Text(he="יש לי נסיון בתור בוטום/נשלט.ת", en="I have experience as a bottom/submissive")),
                    QuestionOption(value="other", text=Text(he="אחר", en="Other"))                
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר רמת ניסיון", en="Please select experience level")
                    )
                ]
            ),
            # 15. bdsm_declaration
            "bdsm_declaration": QuestionDefinition(
                question_id="bdsm_declaration",
                question_type=QuestionType.SELECT,
                title=Text(he="מה הפרופיל המיני שלך?", en="What is your sexual orientation and gender?"),
                required=True,
                save_to="Registrations",
                order=15,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 16. is_play_with_partner_only
            "is_play_with_partner_only": QuestionDefinition(
                question_id="is_play_with_partner_only",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם תרצה להשתתף באירוע בלבד עם פרטנר?", en="Would you like to participate in an event with a partner only?"),
                required=True,
                save_to="Registrations",
                order=16,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 17. desired_play_partners
            "desired_play_partners": QuestionDefinition(
                question_id="desired_play_partners",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מי תרצה להשתתף באירוע?", en="Who would you like to participate with?"),
                required=True,
                save_to="Registrations",
                order=17,
                placeholder=Text(he="למשל: זכר, נקבה, אחר", en="e.g., male, female, other"),
                options=[
                    QuestionOption(value="all_genders", text=Text(he="יש לי עניין עם כל המגדרים", en="I am interested in all genders")),
                    QuestionOption(value="women_only", text=Text(he="יש לי עניין עם נשים* בלבד", en="I am interested in women* only")),
                    QuestionOption(value="men_only", text=Text(he="יש לי עניין עם גברים* בלבד", en="I am interested in men* only")),
                    QuestionOption(value="couples", text=Text(he="יש לי עניין עם זוג", en="I am interested in couples")),
                    QuestionOption(value="partner_dependent", text=Text(he="יש לי עניין אך זה תלוי בהסכמות של בן/בת הזוג", en="I am interested but it depends on my partner's consent"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 18. contact_type
            "contact_type": QuestionDefinition(
                question_id="contact_type",
                question_type=QuestionType.SELECT,
                title=Text(he="מה סוג המגע הרצוי?", en="What type of contact would you like?"),
                required=True,
                save_to="Registrations",
                order=18,
                options=[
                    QuestionOption(value="bdsm_only", text=Text(he="בדס״מ בלבד", en="BDSM only")),
                    QuestionOption(value="bdsm_and_sexual", text=Text(he="בדס״מ ומיניות", en="BDSM and sexual")),
                    QuestionOption(value="other", text=Text(he="אחר", en="Other"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 19. contact_type_other
            "contact_type_other": QuestionDefinition(
                question_id="contact_type_other",
                question_type=QuestionType.TEXT,
                title=Text(he="אחר", en="Other"),
                required=True,
                save_to="Registrations",
                order=19,
                placeholder=Text(he="למשל: בדס״מ בלבד, בדס״מ ומיניות, אחר", en="e.g., BDSM only, BDSM and sexual, Other"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="contact_type", value="other", operator="not_in")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 20 share_bdsm_interests
            "share_bdsm_interests": QuestionDefinition(
                question_id="share_bdsm_interests",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם תרצה לשתף אירועים דומים ב-BDSM?", en="Would you like to share events similar to BDSM?"),
                required=True,
                save_to="Registrations",
                order=20,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 21 limits_preferences_matrix
            "limits_preferences_matrix": QuestionDefinition(
                question_id="limits_preferences_matrix",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
                save_to="Users",
                order=21,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 22 boundaries_text
            "boundaries_text": QuestionDefinition(
                question_id="boundaries_text",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
                save_to="Users",
                order=22,
                placeholder=Text(he="למשל: צליאק, אלרגיה לבוטנים...", en="e.g., celiac, peanut allergy..."),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 23 preferences_text
            "preferences_text": QuestionDefinition(
                question_id="preferences_text",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
                save_to="Users",
                order=23,
                placeholder=Text(he="למשל: צליאק, אלרגיה לבוטנים...", en="e.g., celiac, peanut allergy..."),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 24 bdsm_comments
            "bdsm_comments": QuestionDefinition(
                question_id="bdsm_comments",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
                save_to="Users",
                order=24,
                placeholder=Text(he="למשל: צליאק, אלרגיה לבוטנים...", en="e.g., celiac, peanut allergy..."),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 25 food_restrictions
            "food_restrictions": QuestionDefinition(
                question_id="food_restrictions",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
                save_to="Users",
                order=25,
                placeholder=Text(he="למשל: צליאק, אלרגיה לבוטנים...", en="e.g., celiac, peanut allergy..."),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 26 food_comments
            "food_comments": QuestionDefinition(
                question_id="food_comments",
                question_type=QuestionType.TEXT,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
                save_to="Users",
                order=26,
                placeholder=Text(he="למשל: צליאק, אלרגיה לבוטנים...", en="e.g., celiac, peanut allergy..."),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ]
            ),
            # 27 alcohol_in_event
            "alcohol_in_event": QuestionDefinition(
                question_id="alcohol_in_event",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם תרצה אלכוהול באירוע?", en="Would you like alcohol at the event?"),
                required=True,
                save_to="Registrations",
                order=27,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 28 alcohol_preference
            "alcohol_preference": QuestionDefinition(
                question_id="alcohol_preference",
                question_type=QuestionType.TEXT,
                title=Text(he="מה האלכוהול שלך?", en="What is your alcohol preference?"),
                required=False,
                save_to="Users",
                order=28,
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="alcohol_in_event", operator="equals", value="no")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 29 agree_participant_commitment
            "agree_participant_commitment": QuestionDefinition(
                question_id="agree_participant_commitment",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מסכמ/ת את הפרשנות?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=29,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 30 enthusiastic_verbal_consent_commitment
            "enthusiastic_verbal_consent_commitment": QuestionDefinition(
                question_id="enthusiastic_verbal_consent_commitment",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מסכמ/ת את הפרשנות?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=30,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 31 agree_line_rules
            "agree_line_rules": QuestionDefinition(
                question_id="agree_line_rules",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מסכמ/ת את הפרשנות?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=31,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 32 wants_to_helper
            "wants_to_helper": QuestionDefinition(
                question_id="wants_to_helper",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מעוניין/ת לעזור באירוע?", en="Do you want to help at the event?"),
                required=True,
                save_to="Registrations",
                order=32,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]   
            ),
            # 33 helper_shifts
            "helper_shifts": QuestionDefinition(
                question_id="helper_shifts",
                question_type=QuestionType.SELECT,
                title=Text(he="מתי אתה/את מעוניין/ת לעזור באירוע?", en="When do you want to help at the event?"),
                required=True,
                save_to="Registrations",
                order=33,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 34 is_surtified_DM
            "is_surtified_DM": QuestionDefinition(
                question_id="is_surtified_DM",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מוכנ/ה להיות דמות מורשת?", en="Are you certified to be a DM?"),
                required=True,
                save_to="Users",
                order=34,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 35 wants_to_DM
            "wants_to_DM": QuestionDefinition(
                question_id="wants_to_DM",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מעוניין/ת להיות דמות מורשת?", en="Do you want to be a DM?"),
                required=True,
                save_to="Registrations",
                order=35,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 36 DM_shifts
            "DM_shifts": QuestionDefinition(
                question_id="DM_shifts",
                question_type=QuestionType.SELECT,
                title=Text(he="מתי אתה/את מעוניין/ת להיות דמות מורשת?", en="When do you want to be a DM?"),
                required=True,
                save_to="Registrations",
                order=36,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
        }
    
    def parse_upcoming_events(self) -> List[QuestionOption]:
        """Parse upcoming events from the sheets service."""
        events = self.event_service.get_upcoming_events()
        
        return [QuestionOption(value=event.id, text=Text(he=f"{event.start_date} - {event.name} ({event.event_type})", en=f"{event.start_date} - {event.name} ({event.event_type})")) for event in events]
    
    
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
    
    # async def _get_question(self, step: FormStep, form_state: FormState) -> Dict[str, Any]:
    #     """Get question for a specific step."""
    #     if step == FormStep.LANGUAGE_SELECTION:
    #         return GenericForm.all_fields_dict["language"]
        
    #     elif step == FormStep.EVENT_DETAILS:
    #         # Get event details from sheets
    #         event_details = await self._get_event_details(form_state.event_id)
    #         return {
    #             "type": "event_info",
    #             "event": event_details,
    #             "text": {
    #                 "he": "האם תרצה/י להרשם לאירוע זה?",
    #                 "en": "Would you like to register for this event?"
    #             },
    #             "options": [
    #                 {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
    #                 {"value": "no", "text": {"he": "לא", "en": "No"}}
    #             ],
    #             "required": True
    #         }
        
    #     elif step == FormStep.PERSONAL_INFO:
    #         return {
    #             "type": "personal_info",
    #             "fields": [
    #                 {
    #                     "name": "full_name",
    #                     "type": "text",
    #                     "label": {"he": "שם מלא", "en": "Full Name"},
    #                     "required": True
    #                 },
    #                 {
    #                     "name": "telegram_username",
    #                     "type": "text",
    #                     "label": {"he": "שם משתמש בטלגרם", "en": "Telegram Username"},
    #                     "placeholder": {"he": "@username או t.me/username", "en": "@username or t.me/username"},
    #                     "required": True
    #                 },
    #                 {
    #                     "name": "previous_participation",
    #                     "type": "choice",
    #                     "label": {"he": "האם השתתפת בעבר באירועי Wild Ginger?", "en": "Have you participated in Wild Ginger events before?"},
    #                     "options": [
    #                         {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
    #                         {"value": "no", "text": {"he": "לא", "en": "No"}}
    #                     ],
    #                     "required": True
    #                 },
    #                 {
    #                     "name": "balance_status",
    #                     "type": "choice",
    #                     "label": {"he": "האם מגיע/ה לבד או באיזון?", "en": "Are you coming alone or with a partner?"},
    #                     "options": [
    #                         {"value": "single", "text": {"he": "לבד", "en": "Alone"}},
    #                         {"value": "partner", "text": {"he": "באיזון", "en": "With Partner"}}
    #                     ],
    #                     "required": True
    #                 }
    #             ]
    #         }
        
    #     # Add more steps as needed...
    #     return {"type": "unknown", "text": "Unknown step"}
    
    # async def _get_next_step(self, current_question: str, answer: Any, form_state: FormState) -> str:
    #     """Determine the next step based on current step and answer."""
    #     if current_question == FormStep.LANGUAGE_SELECTION:
    #         form_state.language = answer
    #         return "event_details"
        
    #     elif current_question == FormStep.EVENT_DETAILS:
    #         if answer == "no":
    #             return "completion"
    #         return "personal_info"
        
    #     elif current_question == FormStep.PERSONAL_INFO:
    #         # Check if event-specific questions are needed
    #         event_type = await self._get_event_type(form_state.event_id)
    #         if event_type == "play":
        #             return "event_specific"
    #         else:
    #             return "food_alcohol"
        
    #     # Add more step logic...
    #     return "completion"
    
    # async def _validate_step_answer(self, step: FormStep, answer: Any, form_state: FormState) -> Dict[str, Any]:
    #     """Validate answer for a specific step."""
    #     if step == FormStep.LANGUAGE_SELECTION:
    #         if answer not in ["he", "en"]:
    #             return {
    #                 "valid": False,
    #                 "message": {"he": "אנא בחר/י שפה", "en": "Please select a language"}
    #             }
        
    #     elif step == FormStep.TELEGRAM_USERNAME:
    #         # Validate Telegram username format
    #         is_valid, error_msg = self.validate_telegram_username(answer)
    #         if not is_valid:
    #             return {
    #                 "valid": False,
    #                 "message": {"he": error_msg, "en": error_msg}
    #             }
        
    #     return {"valid": True, "message": ""}
    
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
        return {
            "completed": True,
            "form_id": f"{form_state.user_id}_{form_state.event_id}",
            "answers": form_state.answers,
            "message": {
                "he": "תודה על ההרשמה! נציג יצור איתך קשר בקרוב.",
                "en": "Thank you for registering! A representative will contact you soon."
            }
        } 
        
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
            
            return {"valid": True, "message": ""}
            
        except Exception as e:
            self.log_error(f"Error validating answer: {e}")
            return {"valid": False, "message": "Validation error"}
    
    async def _get_next_question_for_field(self, current_field: str, form_state: FormState) -> Optional[Dict[str, Any]]:
        """Get the next question after answering a specific field."""
        try:
            # Get the order of the current field
            current_question = self.question_definitions.get(current_field)
            if not current_question:
                return None
            
            current_order = current_question.order
                        
            if form_state.completed:
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
                if next_question.question_id == "would_you_like_to_register":
                    # sent event details
                    event_details = await self._get_event_details(form_state.event_id)
                    description = self.get_event_description(event_details)
                    await self.send_telegram_text_message(description, form_state.language, form_state.user_id)
                form_state.current_question = next_question.question_id
                self.save_active_forms()
                return next_question
            else:
                # Form is complete
                return await self._complete_form(form_state)
                
        except Exception as e:
            self.log_error(f"Error getting next question: {e}")
            return None
    
    async def send_telegram_text_message(self, text: str, language: str, user_id: str):
        """Send a text message to a user."""
        await self.bot.send_message(chat_id=user_id, text=text)
    
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
** כל אירועינו הינם להטבק פרנדלי, ואנו עושות את המיטב כדי לייצר מרחב נעים ומזמין לאנשימות מכל הקשת. 🏳️‍🌈💖
*** הרשמה בטופס זה אינה מהווה אישור הגעה. זאת הזמנה ובדיקת עניין בלבד. במידה ויש התאמה נחזור אליך. 🙃😊

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
                        if field_value == condition.value:
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
            
            # Determine which table to save to based on save_to field
            if question_def.save_to == "Users":
                # Save to users table
                success = self.sheets_service.update_user_cell(user_id, "telegram_user_id", "Users", question_field, answer)
            else:
                # Save to registration table
                # TODO get reg_id from user_id
                success = self.sheets_service.update_user_cell(user_id, "telegram_user_id", "Registrations", question_field, answer)
            
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
        registration = CreateRegistrationDTO(user_id=user_id, event_id=event_id, status=RegistrationStatus.FORM_INCOMPLETE)
        result = await self.registration_service.create_new_registration(registration)
        if not result:
            self.log_error(f"Failed to save event selection to sheets for user {user_id}, event {event_id}")
            return False
        
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
    