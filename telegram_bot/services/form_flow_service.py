"""
FormFlowService - Manages form state and flow for event registrations.
Handles step-by-step form progression, state management, and validation.
"""

import os
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
from ..models.registration import CreateRegistrationDTO, RegistrationStatus, Status
from ..models.event import EventDTO
from ..utils.validate_social_link import validate_social_link
from ..utils.utils import str_to_Text

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
        self.completion_date = None
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
            "registration_id": self.registration_id,
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
        self.extra_texts: Dict[str, Text] = self._initialize_extra_text()
        self.admin_chat_id = os.getenv("ADMIN_USER_IDS")
            
    def set_telegram_bot(self, bot: Bot):
        self.bot = bot
    
    def _initialize_extra_text(self) -> Dict[str, Text]:
        """Get extra text for a specific question."""
        return{
            "full_name": Text(he="*פרטים אישיים*\nאיזה כיף שאתה מתעניין באירוע! נעבור על כמה שאלות כל מנת להכיר אותך טוב יותר.", 
                            en="*Personal details*\nIt's great that you're interested in the event! We'll go through a few questions to get to know you better."),
            "bdsm_experience": Text(he='*בואו נדבר בדס"מ*\nנעים מהכיר! היות ומדובר על אירוע בדסמי נעבור כעת על כמה שאלות בנושא.', 
                                    en="*Let's talk BDSM*\nNice to meet you! Since this is a BDSM event, we'll go through a few questions on the subject."),
            "food_restrictions": Text(he="*אוכל ושאר ירקות*", en="*Food, truffles, and trifles*"),
            "agree_participant_commitment": Text(he="*חוקים*\n כמעט סוף. בואו נעבור על חוקי הליין, המקום וכו'.", 
                                                en="*Rules*\n Almost done. Let's go through the line rules, the place, and so on."),
            "wants_to_helper": Text(he="*הלפרים ו DM-ים*\nזהו! סיימנו, אך לפני שאני משחרר אתכם, אשמח לדעת האם תרצו לעזור באירוע (בתמורה להנחה בעלות האירוע)", 
                                    en="*Helpers and DMs*\nThat's it! We're done, but before I let you go, I'd like to know if you'd like to help at the event (in exchange for a discount on the event's cost)"),
            "wants_to_DM": Text(he=f"לטובת שמירה מיטבית על המרחב ועל מנת שכולנו נוכל גם להנות, נהיה צוות של דיאמים. DM מקבל כניסה זוגית חינם", 
                                en=f"We will have a team of DMs to preserve the safety of the space and everyone in it so that we can all enjoy ourselves. DM gets a free pair entry"),
            "completion": Text(he="תודה שנרשמת לאירוע! ניתן להתחיל מחדש בכל עת עם הפקודה /start", 
                                en="Thank you for filling out the form! You can start over at any time with the /start command")
        }
    
    def _initialize_question_definitions(self) -> Dict[str, QuestionDefinition]:
        """Initialize question definitions following the form order specification."""
        skip = Text(he="ניתן לדלג על השאלה. רשמו 'המשך'", en="you can skip the question. write 'continue'")
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
            # 2. Event type
            "interested_in_event_types": QuestionDefinition(
                question_id="interested_in_event_types",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="מה סוגי האירועים שתרצה להשתתף בהם?", en="What type of events would you like to participate in?"),
                required=True,
                save_to="Users",
                order=2,
                options=[
                    QuestionOption(value="play", text=Text(he="משחק", en="Play")),
                    QuestionOption(value="cuddle", text=Text(he="כירבולייה", en="Cuddle"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אירוע", en="Please select an event")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="interested_in_event_types")
                    ]
                )
            ),
            
            # 3. Event selection (every time)
            "event_selection": QuestionDefinition(
                question_id="event_selection",
                question_type=QuestionType.SELECT,
                title=Text(he="לאיזה אירוע תרצה להירשם?", en="To which event would you like to register?"),
                required=True,
                save_to="Registrations",
                order=3,
                options=self.parse_upcoming_events(),
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
                        SkipConditionItem(type="user_exists", field="telegram_user_id")
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
            # 6. relevant experience
            "relevant_experience": QuestionDefinition(
                question_id="relevant_experience",
                question_type=QuestionType.TEXT,
                title=Text(he="מה רמת הניסיון שלך באירועים דומים?", en="What is your experience with similar events?"),
                required=True,
                save_to="Users",
                order=6,
                # placeholder=Text(he="למשל: משחק בכירבולייה, משחק במשחקים בודדים, משחק במשחקים בצניחה, משחק במשחקים במשחקים בכירבולייה", en="e.g., Play in cuddle, Play in solo, Play in cuddle, Play in bdsm, Play in bdsm in cuddle, Play in bdsm in solo"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן רמת ניסיון", en="Please enter experience")
                    )
                ],
                # TODO skip_condition=SkipCondition(
                #     operator="OR",
                #     conditions=[
                #         SkipConditionItem(type="user_exists", field="telegram_id")
                #     ]
                # ),
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
                placeholder=Text(he="https://t.me/username Or @username", en="https://t.me/username Or @username"),
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
                    ValidationRule(
                        rule_type=ValidationRuleType.TELEGRAM_LINK,
                        error_message=Text(he="הלינק אינו תקין. אנא הזן לינק תקין לטלגרם\nhttps://t.me/username Or @username", en="Invalid link. Please enter a valid Telegram link\nhttps://t.me/username Or @username")
                    )
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
                    ValidationRule(
                        rule_type=ValidationRuleType.DATE_RANGE,
                        error_message=Text(he="התאריך אינו תקין. אנא הזן תאריך תקין", en="Invalid date. Please enter a valid date")
                    )
                ]
            ),
            # 10. Facebook profile (new users only)
            "facebook_profile": QuestionDefinition(
                question_id="facebook_profile",
                question_type=QuestionType.FACEBOOK_LINK,
                title=Text(he="אנא שתף לינק לפרופיל הפייסבוק או האינסטגרם שלך", en="Please share a link to your Facebook OR Instagram profile"),
                required=True,
                save_to="Users",
                order=10,
                placeholder=Text(he="https://facebook.com/username Or https://instagram.com/username", en="https://facebook.com/username Or https://instagram.com/username"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="facebook_profile")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן לינק לפייסבוק או לאינסטגרם", en="Please enter Facebook or Instagram link")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.FACEBOOK_LINK,
                        error_message=Text(he="הלינק אינו תקין. אנא הזן לינק תקין לפייסבוק או לאינסטגרם", en="Invalid link. Please enter a valid Facebook or Instagram link")
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
                        SkipConditionItem(type="user_exists", field="birth_date")
                    ]
                ),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא הזן תאריך לידה", en="Please enter birth date")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.DATE_RANGE,
                        error_message=Text(he="התאריך אינו תקין. אנא הזן תאריך תקין", en="Invalid date. Please enter a valid date")
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
                title=Text(he="נטייה מינית ומגדר", en="Sexual orientation and gender"),
                required=True,
                save_to="Users",
                order=12,
                placeholder=Text(he="למשל: זכר סטרייט, אישה לסבית, אחר", 
                                en="for example: male straight, female bi, other"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="sexual_orientation_and_gender")
                    ]
                ),

            ),
            # 13. pronouns
            "pronouns": QuestionDefinition(
                question_id="pronouns",
                question_type=QuestionType.TEXT,
                title=Text(he="מה לשון הפניה שלך?", en="What are your pronouns?"),
                required=False,
                save_to="Users",
                order=13,
                placeholder=Text(he=f"למשל: את / אתה / הם\n{skip.he}", 
                                en=f"for example: she/he/they\n{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="user_exists", field="pronouns")
                    ]
                ),
            ),
            # 14. bdsm_experience
            "bdsm_experience": QuestionDefinition(
                question_id="bdsm_experience",
                question_type=QuestionType.MULTI_SELECT,
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
            # TODO bdsm_experience other
            # 15. bdsm_declaration
            "bdsm_declaration": QuestionDefinition(
                question_id="bdsm_declaration",
                question_type=QuestionType.SELECT,
                title=Text(he='האירוע הינו בדסמ פרנדלי, ויכלול אקטים בדס"מים / מיניים שונים על פי רצון המשתתפים. איני מחוייב.ת להשתתף באף אקט ואסרב בנימוס אם יציעו לי אקט שאיני מעוניין.ת בו', 
                            en="The event is BDSM friendly, and will include various BDSM / sexual acts according to the wishes of the participants. I am not obliged to participate in any act and will politely refuse an offer for an act that I am not interested in."),
                required=True,
                save_to="Registrations",
                order=15,
                options=[
                    QuestionOption(value="yes", text=Text(he="כמובן", en="of course")),
                    QuestionOption(value="no", text=Text(he="לא ברור לי הסעיף, אשמח להבהרה", en="I don't understand, please clarify"))
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
                question_type=QuestionType.SELECT,
                title=Text(he="האם תהיה מעוניין לשחק אך ורק עם הפרטנר שתגיעו איתו או גם עם אנשים נוספים?", 
                            en="would you like to play only with the partner you will come with or also with other people?"),
                required=True,
                save_to="Registrations",
                order=16,
                options=[
                    QuestionOption(value="partner_only", text=Text(he="רק עם פרטנר", en="Only with my partner")),
                    QuestionOption(value="other_people", text=Text(he="גם עם אחרים", en="Also with other people"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="partner_or_single", value="single", operator="equals")
                    ]
                )
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
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="is_play_with_partner_only", value="partner_only", operator="equals")
                    ]
                )
            ),
            # 18. contact_type
            "contact_type": QuestionDefinition(
                question_id="contact_type",
                question_type=QuestionType.SELECT,
                title=Text(he="באיזה סוג מגע תהיה מעוניינ.ת?", en="What type of contact would you like?"),
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
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="is_play_with_partner_only", value="partner_only", operator="equals")
                    ]
                )
            ),
            # 19. contact_type_other
            "contact_type_other": QuestionDefinition(
                question_id="contact_type_other",
                question_type=QuestionType.TEXT,
                title=Text(he="אנא פרט לגבי סוג המגע הרצוי", en="Please elaborate on the type of contact you would like"),
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
                title=Text(he="אשמח לשמוע על הגבולות והעדפות שלכם", 
                            en="We would live to hear about your limits and preferences"),
                required=True,
                save_to="Registrations",
                order=20,
                options=[
                    QuestionOption(value="yes", text=Text(he="יאאלה", en="Sure")),
                    QuestionOption(value="no", text=Text(he="לא מעוניין לשתף", en="Don't want to share"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]
            ),
            # 21 limits_preferences_matrix
            # TODO understand how to do this
            "limits_preferences_matrix": QuestionDefinition(
                question_id="limits_preferences_matrix",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="גבולות והעדפות?", en="limits and preferences?"),
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
                title=Text(he="גבולות - טקסט חופשי", en="Boundaries - free text"),
                required=True,
                save_to="Users",
                order=22,
                placeholder=Text(he=f"תרשמו במילים שלכם\n{skip.he}", en=f"Write in your own words\n{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="share_bdsm_interests", operator="equals", value="no")
                    ]
                )
            ),
            # 23 preferences_text
            "preferences_text": QuestionDefinition(
                question_id="preferences_text",
                question_type=QuestionType.TEXT,
                title=Text(he="העדפות - טקסט חופשי", en="Preferences - free text"),
                required=True,
                save_to="Users",
                order=23,
                placeholder=Text(he=f"תרשמו במילים שלכם\n{skip.he}", en=f"Write in your own words\n{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="share_bdsm_interests", operator="equals", value="no")
                    ]
                )
            ),
            # 24 bdsm_comments
            "bdsm_comments": QuestionDefinition(
                question_id="bdsm_comments",
                question_type=QuestionType.TEXT,
                title=Text(he="הערות חופשיות בנושא BDSM", en="Anything else you'd like to share?"),
                required=False,
                save_to="Users",
                order=24,
                placeholder=Text(he=f"{skip.he}", en=f"{skip.en}"),
            ),
            # 25 food_restrictions
            "food_restrictions": QuestionDefinition(
                question_id="food_restrictions",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="האם יש מגבלות אוכל?", en="Are there any food restrictions?"),
                required=True,
                save_to="Users",
                order=25,
                options=[
                    QuestionOption(value="no", text=Text(he="לא", en="No")),
                    QuestionOption(value="vegetarian", text=Text(he="צמחוני", en="Vegetarian")),
                    QuestionOption(value="vegan", text=Text(he="טבעוני", en="Vegan")),
                    QuestionOption(value="kosher", text=Text(he="כשרות", en="Kosher")),
                    QuestionOption(value="allergies", text=Text(he="אלרגיות", en="Allergies")),
                    QuestionOption(value="gluten_free", text=Text(he="ללא גלוטן", en="Gluten free")),
                    QuestionOption(value="lactose_free", text=Text(he="ללא לקטוז", en="Lactose free")),
                    QuestionOption(value="other", text=Text(he="אחר", en="Other"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר לפחות אופציה אחת", en="Please select at least one option")
                    )
                ]
            ),
            # 26 food_comments
            "food_comments": QuestionDefinition(
                question_id="food_comments",
                question_type=QuestionType.TEXT,
                title=Text(he="אנא פרטו בנושא הגבלות אוכל", en="Please elaborate on the food restrictions"),
                required=False,
                save_to="Users",
                order=26,
                placeholder=Text(he=f"{skip.he}", en=f"{skip.en}"),
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.MAX_LENGTH,
                        params={"max": 200},
                        error_message=Text(he="הטקסט ארוך מדי. אנא קצר", en="Text is too long. Please shorten")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="food_restrictions", operator="equals", value="no")
                    ]
                )
            ),
            # 27 alcohol_in_event
            "alcohol_in_event": QuestionDefinition(
                question_id="alcohol_in_event",
                question_type=QuestionType.SELECT,
                title=Text(he="האם תרצה אלכוהול באירוע (בתוספת תשלום)?", en="Would you like alcohol at the event (with additional payment)?"),
                required=True,
                save_to="Registrations",
                order=27,
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe")),
                    QuestionOption(value="no", text=Text(he="לא", en="No")),
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
                placeholder=Text(he=f"{skip.he}", en=f"{skip.en}"),
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="alcohol_in_event", operator="equals", value="no")
                    ]
                )
            ),
            # 29 agree_participant_commitment
            "agree_participant_commitment": QuestionDefinition(
                question_id="agree_participant_commitment",
                question_type=QuestionType.SELECT,
                title=Text(he="האם זה מובן?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=29,
                options=[
                    QuestionOption(value="yes", text=Text(he="הבנתי את הכתוב ומה שמצופה ממני כמשתתפ/ת. אני מסכימ/ה ומאשר/ת", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא הבנתי או אני לא בטוח/ה שהבנתי מה מצופה ממני כמשתתפ/ת באירוע", en="No")),
                    QuestionOption(value="else", text=Text(he="אחר - נחזור אליך כדי לברר", en="No"))
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
                title=Text(he="האם זה ברור שיש לקבל הסכמה מפורשת לכל מגע ואינטראקציה עם אדם אחר?", en="Do you agree to the terms?"),
                required=True,
                save_to="Registrations",
                order=30,
                options=[
                    QuestionOption(value="yes", text=Text(he="ברור בהחלט", en="Yes")),
                    QuestionOption(value="no", text=Text(he="לא ברור לי, אשמח להבהרה", en="No"))
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
                question_type=QuestionType.TEXT,
                title=Text(he="האם קראת את חוקי הליין ואתה מאשר אותם?", en="Do you agree to the line rules?"),
                required=True,
                save_to="Registrations",
                order=31,
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא קרא את חוקי הליין היטב ואשר אותם", en="Please read the line rules carefully and agree to them")
                    ),
                    ValidationRule(
                        rule_type=ValidationRuleType.REGEX,
                        params={"regex": r'זנגביל|ginger'},
                        error_message=Text(he="אנא קרא את חוקי הליין היטב ואשר אותם", en="Please read the line rules carefully and agree to them")
                    )
                ]
            ),
            # 32 agree_place_rules  
            "agree_place_rules": QuestionDefinition(
                question_id="agree_place_rules",
                question_type=QuestionType.SELECT,
                title=Text(he="האם קראת את חוקי המקום ואתה מאשר אותם?", en="Do you agree to the place rules?"),
                required=False,
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
            # 33 wants_to_helper
            "wants_to_helper": QuestionDefinition(
                question_id="wants_to_helper",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מעוניין/ת לעזור באירוע?", en="Do you want to help at the event?"),
                required=True,
                save_to="Registrations",
                order=33,
                placeholder=Text(he=f'על מנת להרים כזאת הפקה אנו זקוקות לעזרה. אם תוכל ותרצי נשמח שתבואו מוקדם / תשארו לעזור לנו לנקות אחרי בתמורה להנחה בעלות האירוע. הלפרים מקבלים 25% הנחה. ניתן לצבור ע"י בחירת שניהם. ', 
                                en=f"{skip.en}"),
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ]   
            ),
            # 34 helper_shifts
            "helper_shifts": QuestionDefinition(
                question_id="helper_shifts",
                question_type=QuestionType.SELECT,
                title=Text(he="מתי אתה/את מעוניין/ת לעזור באירוע?", en="When do you want to help at the event?"),
                required=True,
                save_to="Registrations",
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
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="wants_to_helper", operator="equals", value="no")
                    ]
                )
            ),
            # 35 is_surtified_DM
            "is_surtified_DM": QuestionDefinition(
                question_id="is_surtified_DM",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם את/ה DM מוסמך?", en="Are you certified to be a DM?"),
                required=True,
                save_to="Users",
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
            # 36 wants_to_DM
            "wants_to_DM": QuestionDefinition(
                question_id="wants_to_DM",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם תרצו להצטרף לצוות ה-DM-ים?", en="Do you want to be a DM?"),
                required=True,
                save_to="Registrations",
                order=36,
                placeholder=Text(he=f"לטובת שמירה מיטבית על המרחב ועל מנת שכולנו נוכל גם להנות, נהיה צוות של דיאמים. DM מקבל כניסה זוגית חינם", 
                                en=f"{skip.en}"),
                options=[
                    QuestionOption(value="yes", text=Text(he="כן", en="Yes")),
                    QuestionOption(value="maybe", text=Text(he="אולי", en="Maybe")),
                    QuestionOption(value="no", text=Text(he="לא", en="No"))
                ],
                validation_rules=[
                    ValidationRule(
                        rule_type=ValidationRuleType.REQUIRED,
                        error_message=Text(he="אנא בחר אופציה", en="Please select an option")
                    )
                ],
                skip_condition=SkipCondition(
                    operator="OR",
                    conditions=[
                        SkipConditionItem(type="field_value", field="is_surtified_DM", operator="equals", value="no")
                    ]
                )
            ),
            # 37 DM_shifts
            "DM_shifts": QuestionDefinition(
                question_id="DM_shifts",
                question_type=QuestionType.MULTI_SELECT,
                title=Text(he="איזה משמרות יכולות להתאים לך?", en="When do you want to be a DM?"),
                required=True,
                save_to="Registrations",
                order=37,
                placeholder=Text(he=f"אשתדל לאפשר לכל אחד את הבחירות שלו.", 
                                en=f"{skip.en}"),
                options=self.parse_DM_shifts(),
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
    
    
    async def _update_form_completion_status(self, form_state: FormState) -> bool:
        """Update form completion status in Google Sheets."""
        try:
            if not form_state.registration_id:
                self.log_error(f"No registration ID for user {form_state.user_id}")
                return False
            
            success = await self.registration_service.update_registration_by_registration_id(form_state.registration_id, "form_complete", True)
            
            status = Status.PENDING if form_state.get_answer("would_you_like_to_register") == "yes" else Status.UNINTERESTED
            success = await self.registration_service.update_registration_by_registration_id(form_state.registration_id, "status", status.value)
                        
            if success:
                self.log_info(f"Updated form completion status for registration {form_state.registration_id}")
            else:
                self.log_error(f"Failed to update form completion status for registration {form_state.registration_id}")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error updating form completion status for {form_state.user_id}: {e}")
            return False
    
    async def _handle_special_completion_logic(self, form_state: FormState) -> None:
        """Handle special completion logic based on form answers."""
        try:
            # Handle "would_you_like_to_register = no" case
            if form_state.get_answer("would_you_like_to_register") == "no":
                self.log_info(f"User {form_state.user_id} chose not to register - marking as not interested")
                # Could add special handling here like sending a different message
                return
            
            # Handle returning participant logic
            if form_state.get_answer("returning_participant") == "yes":
                self.log_info(f"User {form_state.user_id} is a returning participant - auto-marking get-to-know complete")
                # Auto-mark get-to-know complete for returning participants
                await self._auto_mark_get_to_know_complete(form_state)
            
            # Handle partner registration logic
            if form_state.get_answer("partner_or_single") == "partner":
                partner_link = form_state.get_answer("partner_telegram_link")
                if partner_link:
                    self.log_info(f"User {form_state.user_id} has partner {partner_link} - will need partner completion")
                    # add partner reg link to message
                    return {
                        "message": f"המשך להרשמה של בעלת החברה: {partner_link}",
                        "partner_link": partner_link
                    }
                    # Could trigger partner notification here
            
        except Exception as e:
            self.log_error(f"Error handling special completion logic for {form_state.user_id}: {e}")
    
    
    def _create_partner_registration_link(self, form_state: FormState) -> str:
        """Get partner link from form state."""
        return f"https://t.me/{form_state.get_answer('partner_telegram_link')}?text={self._create_partner_registration_message(form_state)}"
    
    def _create_partner_registration_message(self, form_state: FormState) -> str:
        """Get partner link from form state."""
        if form_state.get_language() == "he":
            return f"המשך להרשמה של בעלת החברה: {self._create_partner_registration_link(form_state)}"
        else:
            return f"Continue to partner registration: {self._create_partner_registration_link(form_state)}"
    
    async def _get_event_details(self, event_id: str) -> EventDTO:
        """Get event details from sheets."""
        # TODO: Implement actual event details retrieval
        return self.event_service.get_event_by_id(event_id)
    
    async def _get_event_type(self, event_id: str) -> str:
        """Get event type from sheets."""
        # TODO: Implement actual event type retrieval
        return self.event_service.get_event_type(event_id)
    
    async def _complete_form(self, form_state: FormState) -> Dict[str, Any]:
        """Handle form completion with comprehensive workflow."""
        try:
            self.log_info(f"Starting form completion for user {form_state.user_id}")
            
            # 1. Mark form as completed in memory
            form_state.completed = True
            form_state.completion_date = datetime.now()
            
            # 2. Update form completion status in Google Sheets
            form_complete_updated = await self._update_form_completion_status(form_state)
            if not form_complete_updated:
                self.log_error(f"Failed to update form completion status for {form_state.user_id}")
                # Don't fail the entire completion, just log the error
                        
            # 3. Handle special completion logic based on answers
            await self._handle_special_completion_logic(form_state)
            
            # 4. Send completion message to user
            completion_message = await self._get_completion_message(form_state)
            
            # 5. Clean up form state from memory and save to file storage
            form = self.active_forms.pop(str(form_state.user_id), None)
            self.save_active_forms()
            
            # 6. Log completion
            self.log_info(f"Form completed successfully for user {form_state.user_id}")
            
            # 7. Notify admins about form completion
            await self.notify_admins(form_state)
            
            return {
                "completed": True,
                "form_id": f"{form_state.user_id}_{form_state.event_id}",
                "registration_id": form_state.registration_id,
                "user_id": form_state.user_id,
                "answers": form_state.answers,
                "message": completion_message,
                "completion_date": form_state.completion_date.isoformat()
            }
            
        except Exception as e:
            self.log_error(f"Error completing form for user {form_state.user_id}: {e}")
            return self._create_error_response(f"Form completion failed: {str(e)}")
    
    async def notify_admins(self, form_state: FormState):
        """Notify admins about form completion."""
        message = f"Form completed by user {form_state.user_id}\n"
        message += f"Event: {form_state.event_id}\n"
        message += f"Registration ID: {form_state.registration_id}\n"
        message += f"Answers: \n"
        for key, value in form_state.answers.items():
            message += f"\t{key}: {value}\n"
            
        await self.bot.send_message(chat_id=self.admin_chat_id, text=message)
    
    async def _auto_mark_get_to_know_complete(self, form_state: FormState) -> bool:
        """Auto-mark get-to-know complete for returning participants."""
        try:
            if not form_state.registration_id:
                return False
            
            from telegram_bot_polling import update_get_to_know_complete
            success = update_get_to_know_complete(form_state.registration_id, True)
            
            if success:
                self.log_info(f"Auto-marked get-to-know complete for returning participant {form_state.user_id}")
            else:
                self.log_error(f"Failed to auto-mark get-to-know complete for {form_state.user_id}")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error auto-marking get-to-know complete for {form_state.user_id}: {e}")
            return False
    
    async def _get_completion_message(self, form_state: FormState) -> Dict[str, str]:
        """Get appropriate completion message based on form answers."""
        try:
            if form_state.get_answer("would_you_like_to_register") == "no":
                if form_state.get_language() == "he":
                    return "תודה על העניין שלך! אם תשנה את דעתך, אתה תמיד יכול לחזור ולהרשם."
                else:
                    return "Thank you for your interest! If you change your mind, you can always come back and register."
            
            # Default completion message
            if form_state.get_language() == "he":
                return "🎉 תודה על ההרשמה! הטופס הושלם בהצלחה.\n\nנציג יצור איתך קשר בקרוב עם פרטים נוספים על האירוע.\n\nאתה יכול לבדוק את הסטטוס שלך בכל זמן עם הפקודה /status"
            else:
                return "🎉 Thank you for registering! The form has been completed successfully.\n\nA representative will contact you soon with more details about the event.\n\nYou can check your status anytime using the /status command"
            
        except Exception as e:
            self.log_error(f"Error getting completion message for {form_state.user_id}: {e}")
            return {
                "he": "תודה על ההרשמה! נציג יצור איתך קשר בקרוב.",
                "en": "Thank you for registering! A representative will contact you soon."
            }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response for form completion."""
        return {
            "completed": False,
            "error": error_message,
            "message": {
                "he": "אירעה שגיאה בהשלמת הטופס. אנא נסה שוב או פנה לתמיכה.",
                "en": "An error occurred while completing the form. Please try again or contact support."
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
                    try:
                        birth_date = datetime.strptime(answer, "%d/%m/%Y")
                    except (ValueError, TypeError):
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
                        
            # Check if this is the last question (order 37) or if the user doesn't want to register
            if current_order >= len(self.question_definitions) or form_state.get_answer("would_you_like_to_register") == "no":
                return await self._complete_form(form_state)
            
            # skip BDSM for cuddles
            if current_order == 13 and self.event_service.get_event_type(form_state.event_id) == "cuddle":
                current_order = self.question_definitions["food_restrictions"].order
            
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
** כל אירועינו הינם להטבק פרנדלי, ואנו עושות את המיטב כדי לייצר מרחב נעים ומזמין לאנשימות מכל הקשת. 🏳️‍🌈��
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
                        data = user_data[self.user_service.headers[condition.field]]
                        if data != "":
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
            elif question_def.question_id == "relevant_experience":
                event_type = await self._get_event_type(self.active_forms[user_id].event_id)
                return await self.user_service.save_relevant_experience(user_id, event_type, answer)
            
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
    