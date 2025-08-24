"""
New FormFlowService - Manages form state and flow for event registrations.
Following the form order specification and sequence diagram.
Handles step-by-step form progression, state management, and validation.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from .base_service import BaseService
from .sheets_service import SheetsService
from .file_storage_service import FileStorageService
from .user_service import UserService
from ..models.form_flow import (
    QuestionType, ValidationRuleType, FormState, ValidationRule,
    SkipConditionItem, SkipCondition, Text, QuestionOption, QuestionDefinition,
    ValidationResult, FormContext, FormStateData, FormProgress, FormData,
    UpdateableFieldDTO, UpdateResult
)


class NewFormFlowService(BaseService):
    """
    New FormFlowService following the form order specification and sequence diagram.
    Handles step-by-step form progression, state management, and validation.
    """
    
    def __init__(self, sheets_service: SheetsService, user_service: UserService):
        """Initialize the new form flow service."""
        super().__init__()
        self.sheets_service = sheets_service
        self.user_service = user_service
        self.file_storage = FileStorageService()
        
        # In-memory storage for form states (in production, use Redis or database)
        self.form_states: Dict[int, FormStateData] = {}
        
        # Question definitions following the form order specification
        self.question_definitions = self._initialize_question_definitions()
    
    async def initialize(self) -> None:
        """Initialize the form flow service."""
        self.log_info("Initializing NewFormFlowService")
        # Load any existing form states from storage
        await self._load_form_states()
    
    async def shutdown(self) -> None:
        """Clean up form flow service resources."""
        self.log_info("Shutting down NewFormFlowService")
        # Save form states to storage
        await self._save_form_states()
    
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
                title=Text(he="באיזה אירוע תרצה להשתתף?", en="In which event would you like to participate?"),
                required=True,
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
                question_type=QuestionType.SELECT,
                title=Text(he="מה סוגי האירועים שתרצה להשתתף בהם?", en="What type of events would you like to participate in?"),
                required=True,
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
                order=3,
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
                order=4,
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
                question_type=QuestionType.MATRIX,
                title=Text(he="מה הסוגים הטכנולוגיים שלך?", en="What is your type of technology?"),
                required=True,
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
                question_type=QuestionType.SELECT,
                title=Text(he="האם תרצה אלכוהול באירוע?", en="Would you like alcohol at the event?"),
                required=True,
                order=28,
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
            # 29 agree_participant_commitment
            "agree_participant_commitment": QuestionDefinition(
                question_id="agree_participant_commitment",
                question_type=QuestionType.BOOLEAN,
                title=Text(he="האם אתה/את מסכמ/ת את הפרשנות?", en="Do you agree to the terms?"),
                required=True,
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
        return [QuestionOption(value="play", text=Text(he="משחק", en="Play")),
                QuestionOption(value="cuddle", text=Text(he="כירבולייה", en="Cuddle"))]
        events = self.sheets_service.get_upcoming_events()
        return [QuestionOption(value=event.id, text=Text(he=event.name, en=event.name)) for event in events]
    
    async def start_form(self, user_id: int, event_id: Optional[str] = None) -> QuestionDefinition:
        """
        Start a new form for a user.
        
        Args:
            user_id: Telegram user ID
            event_id: Event ID to register for
            
        Returns:
            First question to ask the user
        """
        self.log_info(f"Starting form for user {user_id} for event {event_id}")
        
        # Get event type from event_id (this would come from event service)
        event_type = await self._get_event_type(event_id)
        
        # Create form state
        form_state = FormStateData(
            user_id=user_id,
            event_id=event_id,
            current_state=FormState.STARTED,
            language="he"  # Default language
        )
        
        # Save form state
        self.form_states[user_id] = form_state
        
        # Get first question
        first_question = await self._get_next_question(user_id)
        
        # Set the current question ID
        if first_question:
            form_state.current_question_id = first_question.question_id
            self.form_states[user_id] = form_state
        
        return first_question
    
    async def process_answer(self, user_id: int, answer: Any) -> ValidationResult:
        """
        Process user answer and validate it.
        
        Args:
            user_id: Telegram user ID
            answer: User's answer
            
        Returns:
            Validation result with next question or errors
        """
        self.log_info(f"Processing answer for user {user_id}: {answer}")
        
        # Get current form state
        form_state = self.form_states.get(user_id)
        if not form_state:
            return ValidationResult(
                isValid=False,
                errors=["No active form found. Please start a new form."]
            )
        
        # Get current question
        current_question_id = form_state.current_question_id
        if not current_question_id:
            return ValidationResult(
                isValid=False,
                errors=["No current question found."]
            )
        
        current_question = self.question_definitions.get(current_question_id)
        if not current_question:
            return ValidationResult(
                isValid=False,
                errors=["Invalid question ID."]
            )
        
        # Validate answer
        validation_result = await self._validate_answer(current_question, answer, form_state.language)
        
        if validation_result.isValid:
            # Save answer
            form_state.answers[current_question_id] = answer
            form_state.current_state = FormState.IN_PROGRESS
            form_state.last_activity = datetime.now()
            
            # Get next question
            next_question = await self._get_next_question(user_id)
            if next_question:
                form_state.current_question_id = next_question.question_id
                validation_result.nextQuestion = next_question
            else:
                # Form completed
                form_state.current_state = FormState.COMPLETED
                form_state.current_question_id = None
        else:
            # Validation failed
            form_state.current_state = FormState.VALIDATION_ERROR
            form_state.validation_errors[current_question_id] = validation_result.errors
        
        # Update form state
        self.form_states[user_id] = form_state
        
        return validation_result
    
    async def get_current_question(self, user_id: int) -> Optional[QuestionDefinition]:
        """
        Get the current question for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Current question definition or None if no active form
        """
        form_state = self.form_states.get(user_id)
        if not form_state or not form_state.current_question_id:
            return None
        
        return self.question_definitions.get(form_state.current_question_id)
    
    async def get_form_progress(self, user_id: int) -> Optional[FormProgress]:
        """
        Get form progress for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Form progress or None if no active form
        """
        form_state = self.form_states.get(user_id)
        if not form_state:
            return None
        
        # Calculate progress
        all_questions = await self._get_filtered_questions(user_id, form_state.event_id)
        completed_questions = len(form_state.answers)
        total_questions = len(all_questions)
        completion_percentage = (completed_questions / total_questions * 100) if total_questions > 0 else 0
        
        current_question = None
        if form_state.current_question_id:
            current_question = self.question_definitions.get(form_state.current_question_id)
        
        return FormProgress(
            user_id=user_id,
            event_id=form_state.event_id,
            current_question=current_question,
            completed_questions=completed_questions,
            total_questions=total_questions,
            completion_percentage=completion_percentage,
            language=form_state.language
        )
    
    async def complete_form(self, user_id: int) -> Optional[FormData]:
        """
        Complete the form and return form data.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Form data or None if form not completed
        """
        form_state = self.form_states.get(user_id)
        if not form_state or form_state.current_state != FormState.COMPLETED:
            return None
        
        form_data = FormData(
            user_id=user_id,
            event_id=form_state.event_id,
            answers=form_state.answers.copy(),
            language=form_state.language,
            completed_at=datetime.now()
        )
        
        # Clean up form state
        del self.form_states[user_id]
        
        return form_data
    
    async def cancel_form(self, user_id: int) -> None:
        """
        Cancel the form for a user.
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self.form_states:
            self.form_states[user_id].current_state = FormState.CANCELLED
            del self.form_states[user_id]
            self.log_info(f"Form cancelled for user {user_id}")
    
    async def _get_next_question(self, user_id: int) -> Optional[QuestionDefinition]:
        """
        Get the next question for a user based on current answers and skip conditions.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Next question definition or None if form is complete
        """
        form_state = self.form_states.get(user_id)
        if not form_state:
            return None
        
        # Get all questions for this user and event
        all_questions = await self._get_filtered_questions(user_id, form_state.event_id)
        
        # Find the next question that should be asked
        for question in all_questions:
            if question.question_id not in form_state.answers:
                # Check if this question should be skipped
                should_skip = await self._evaluate_skip_condition(
                    question.skip_condition, user_id, form_state
                )
                if not should_skip:
                    return question
        
        return None
    
    async def _get_filtered_questions(self, user_id: int, event_id: str) -> List[QuestionDefinition]:
        """
        Get filtered questions for a user based on skip conditions.
        
        Args:
            user_id: Telegram user ID
            event_id: Event ID
            
        Returns:
            List of questions that should be asked
        """
        form_state = self.form_states.get(user_id)
        if not form_state:
            return []
        
        # Get event type
        event_type = await self._get_event_type(event_id)
        
        # Create context for skip condition evaluation
        context = FormContext(
            user_id=user_id,
            event_id=event_id,
            event_type=event_type,
            answers=form_state.answers,
            language=form_state.language
        )
        
        # Filter questions based on skip conditions
        filtered_questions = []
        for question in self.question_definitions.values():
            should_skip = await self._evaluate_skip_condition(
                question.skip_condition, user_id, form_state
            )
            if not should_skip:
                filtered_questions.append(question)
        
        # Sort by order
        filtered_questions.sort(key=lambda q: q.order)
        
        return filtered_questions
    
    async def _evaluate_skip_condition(
        self, skip_condition: Optional[SkipCondition], user_id: int, form_state: FormStateData
    ) -> bool:
        """
        Evaluate whether a question should be skipped.
        
        Args:
            skip_condition: Skip condition to evaluate
            user_id: Telegram user ID
            form_state: Current form state
            
        Returns:
            True if question should be skipped, False otherwise
        """
        if not skip_condition:
            return False
        
        # Evaluate each condition
        condition_results = []
        for condition in skip_condition.conditions:
            result = await self._evaluate_condition(condition, user_id, form_state)
            condition_results.append(result)
        
        # Apply operator
        if skip_condition.operator == "AND":
            return all(condition_results)
        elif skip_condition.operator == "OR":
            return any(condition_results)
        elif skip_condition.operator == "NOT":
            return not condition_results[0] if condition_results else False
        else:
            return False
    
    async def _evaluate_condition(
        self, condition: SkipConditionItem, user_id: int, form_state: FormStateData
    ) -> bool:
        """
        Evaluate a single skip condition.
        
        Args:
            condition: Condition to evaluate
            user_id: Telegram user ID
            form_state: Current form state
            
        Returns:
            True if condition is met, False otherwise
        """
        if condition.type == "user_exists":
            # Check if user exists in database
            existing_user = self.user_service.get_user_by_telegram_id(str(user_id))
            return existing_user is not None
        
        elif condition.type == "event_type":
            # Check event type
            event_type = await self._get_event_type(form_state.event_id)
            return self._compare_values(event_type, condition.value, condition.operator)
        
        elif condition.type == "field_value":
            # Check field value from answers
            field_value = form_state.answers.get(condition.field)
            return self._compare_values(field_value, condition.value, condition.operator)
        
        else:
            return False
    
    def _compare_values(self, actual: Any, expected: Any, operator: str = "equals") -> bool:
        """
        Compare two values using the specified operator.
        
        Args:
            actual: Actual value
            expected: Expected value
            operator: Comparison operator
            
        Returns:
            True if comparison is true, False otherwise
        """
        if operator == "equals":
            return actual == expected
        elif operator == "not_equals":
            return actual != expected
        elif operator == "in":
            return actual in expected if isinstance(expected, (list, tuple)) else False
        elif operator == "not_in":
            return actual not in expected if isinstance(expected, (list, tuple)) else False
        else:
            return False
    
    async def _validate_answer(
        self, question: QuestionDefinition, answer: Any, language: str
    ) -> ValidationResult:
        """
        Validate a user answer against question validation rules.
        
        Args:
            question: Question definition
            answer: User's answer
            language: User's language preference
            
        Returns:
            Validation result
        """
        errors = []
        
        for rule in question.validation_rules:
            is_valid, error_message = await self._validate_rule(rule, answer, language)
            if not is_valid:
                errors.append(error_message)
        
        return ValidationResult(isValid=len(errors) == 0, errors=errors)
    
    async def _validate_rule(
        self, rule: ValidationRule, answer: Any, language: str
    ) -> Tuple[bool, str]:
        """
        Validate a single validation rule.
        
        Args:
            rule: Validation rule
            answer: User's answer
            language: User's language preference
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        error_message = rule.error_message.get(language)
        
        if rule.rule_type == ValidationRuleType.REQUIRED:
            if not answer or (isinstance(answer, str) and not answer.strip()):
                return False, error_message
        
        elif rule.rule_type == ValidationRuleType.MIN_LENGTH:
            if isinstance(answer, str) and len(answer) < rule.params.get("min", 0):
                return False, error_message
        
        elif rule.rule_type == ValidationRuleType.MAX_LENGTH:
            if isinstance(answer, str) and len(answer) > rule.params.get("max", 0):
                return False, error_message
        
        elif rule.rule_type == ValidationRuleType.FACEBOOK_LINK:
            if not self._validate_facebook_link(answer):
                return False, error_message
        
        elif rule.rule_type == ValidationRuleType.TELEGRAM_LINK:
            if not self._validate_telegram_link(answer):
                return False, error_message
        
        elif rule.rule_type == ValidationRuleType.STI_TEST_DATE:
            if not await self._validate_sti_test_date(answer):
                return False, error_message
        
        elif rule.rule_type == ValidationRuleType.AGE_RANGE:
            if not self._validate_age_range(answer, rule.params):
                return False, error_message
        
        return True, ""
    
    def _validate_facebook_link(self, url: str) -> bool:
        """Validate Facebook link format."""
        if not url:
            return False
        
        facebook_regex = r'^https?://(www\.)?facebook\.com/[a-zA-Z0-9.]+$'
        return bool(re.match(facebook_regex, url))
    
    def _validate_telegram_link(self, link: str) -> bool:
        """Validate Telegram link format."""
        if not link:
            return False
        
        telegram_regex = r'^https?://t\.me/[a-zA-Z0-9_]+$'
        return bool(re.match(telegram_regex, link))
    
    async def _validate_sti_test_date(self, date_str: str) -> bool:
        """Validate STI test date (must be within 3 months)."""
        try:
            test_date = datetime.strptime(date_str, "%d/%m/%Y")
            # three_months_ago = datetime.now() - timedelta(days=90)
            return True # test_date >= three_months_ago
        except (ValueError, TypeError):
            return False
    
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
    
    async def _get_event_type(self, event_id: str) -> str:
        """
        Get event type from event ID.
        This would typically come from an event service.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event type ("play" or "cuddle")
        """
        # TODO: Implement proper event service integration
        # For now, assume play events have "play" in the ID, cuddle events have "cuddle"
        if "cuddle" in event_id.lower():
            return "cuddle"
        else:
            return "play"
    
    async def _load_form_states(self) -> None:
        """Load form states from storage."""
        # TODO: Implement loading from persistent storage
        pass
    
    async def _save_form_states(self) -> None:
        """Save form states to storage."""
        # TODO: Implement saving to persistent storage
        pass 