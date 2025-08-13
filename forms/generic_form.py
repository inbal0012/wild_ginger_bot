"""
Generic Form Implementation - Handles registration forms for all event types.
Based on the generic form template with support for play and cuddle events.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Event types supported by the system."""
    PLAY = "play"
    CUDDLE = "cuddle"


class Language(Enum):
    """Supported languages."""
    HEBREW = "he"
    ENGLISH = "en"


@dataclass
class FormField:
    """Represents a form field."""
    name: str
    step_id: str
    type: str  # text, choice, checkbox, date, etc.
    label: Dict[str, str]  # Language-specific labels
    required: bool = False
    placeholder: Optional[Dict[str, str]] = None
    options: Optional[List[Dict[str, Any]]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    conditional: Optional[Dict[str, Any]] = None  # Conditions for showing this field


@dataclass
class FormStep:
    """Represents a form step."""
    id: str
    title: Dict[str, str]
    fields: List[FormField]
    conditional: Optional[Dict[str, Any]] = None  # Conditions for showing this step


class GenericForm:
    """
    Generic form implementation that handles all event types.
    Supports both play and cuddle events with conditional steps.
    """
    
    # 
    
    all_fields_dict: Dict[str, FormField] = {
        # Language and Event Selection
        "language": FormField(
            name="language",
            step_id="language_selection",
            type="choice",
            label={
                "he": "באיזו שפה תרצה/י להמשיך?",
                "en": "In which language would you like to continue?"
            },
            required=True,
            options=[
                {"value": "he", "text": {"he": "עברית", "en": "Hebrew"}},
                {"value": "en", "text": {"he": "English", "en": "English"}}
            ]
        ),
        "upcoming_events": FormField(
            name="upcoming_events",
            step_id="upcoming_events",
            type="checkbox",
            label={
                "he": "לאיזה אירועים תרצה/י להרשם?",
                "en": "For which events would you like to register?"
            },
            required=True,
            options=[
                #TODO dynamically get upcoming events from sheets
                {"value": "play", "text": {"he": "פלי", "en": "Play"}},
                {"value": "cuddle", "text": {"he": "כירבולייה", "en": "Cuddle"}}
            ]
        ),
        "interested_in_event_types": FormField(
            name="interested_in_event_types",
            step_id="temp",
            type="checkbox",
            label={
                "he": "באיזה סוגי אירועים את/ה מתעניין/ת?",
                "en": "What types of events are you interested in?"
            },
            required=False,
            options=[
                {"value": "play", "text": {"he": "פלי", "en": "Play"}},
                {"value": "cuddle", "text": {"he": "כירבולייה", "en": "Cuddle"}},
                {"value": "social", "text": {"he": "חברתי", "en": "Social"}}
            ]
        ),
        "would_you_like_to_register": FormField(
            name="would_you_like_to_register",
            step_id="temp",
            type="choice",
            label={
                "he": "האם תרצה/י להירשם לאירוע זה?",
                "en": "Would you like to register for this event?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        
        # Personal Information
        "full_name": FormField(
            name="full_name",
            step_id="personal_info",
            type="text",
            label={
                "he": "שם מלא",
                "en": "Full Name"
            },
            required=True
        ),
        "last_sti_test": FormField(
            name="last_sti_test",
            step_id="personal_info",
            type="date",
            label={
                "he": "תאריך בדיקת STI אחרונה",
                "en": "Date of last STI test"
            },
            placeholder={
                "he": "DD/MM/YYYY",
                "en": "DD/MM/YYYY"
            },
            required=True,
            validation_rules={"type": "sti_test_date"}
        ),
        "relevant_experience": FormField(
            name="relevant_experience",
            step_id="personal_info",
            type="text",
            label={
                "he": "ניסיון רלוונטי",
                "en": "Relevant experience"
            },
            placeholder={
                "he": "ספר/י לנו על הניסיון שלך באירועים דומים",
                "en": "Tell us about your experience in these events" 
            },
            required=True
        ),
        "partner_or_single": FormField(
            name="partner_or_single",
            step_id="personal_info",
            type="choice",
            label={
                "he": "האם מגיע/ה לבד או עם פרטנר?",
                "en": "Are you coming alone or with a partner?"
            },
            required=True,
            options=[
                {"value": "single", "text": {"he": "לבד", "en": "Alone"}},
                {"value": "partner", "text": {"he": "עם פרטנר", "en": "With Partner"}}
            ]
        ),
        "partner_telegram": FormField(
            name="partner_telegram",
            step_id="personal_info",
            type="text",
            label={
                "he": "שם משתמש הטלגרם של הפרטנר",
                "en": "Partner's Telegram username"
            },
            placeholder={
                "he": "@username או t.me/username",
                "en": "@username or t.me/username"
            },
            required=True,
            validation_rules={"type": "telegram_username"},
            conditional={"field": "partner_or_single", "value": "partner"}
        ),
        "facebook_link": FormField(
            name="facebook_link",
            step_id="personal_info",
            type="text",
            label={
                "he": "קישור לפייסבוק",
                "en": "Facebook link"
            },
            placeholder={
                "he": "https://facebook.com/username",
                "en": "https://facebook.com/username"
            },
            required=True
        ),
        "date_of_birth": FormField(
            name="date_of_birth",
            step_id="personal_info",
            type="date",
            label={
                "he": "תאריך לידה",
                "en": "Date of birth"
            },
            placeholder={
                "he": "DD/MM/YYYY",
                "en": "DD/MM/YYYY"
            },
            required=True
        ),
        "sexual_orientation_and_gender": FormField(
            name="sexual_orientation_and_gender",
            step_id="personal_info",
            type="text",
            label={
                "he": "נטייה מינית ומגדר",
                "en": "Sexual orientation and gender"
            },
            placeholder={
                "he": "ספר/י לנו על עצמך",
                "en": "Tell us about yourself"
            },
            required=True
        ),
        "pronouns": FormField(
            name="pronouns",
            step_id="personal_info",
            type="text",
            label={
                "he": "כינויי גוף מועדפים",
                "en": "Preferred pronouns"
            },
            placeholder={
                "he": "אופציונלי",
                "en": "Optional"
            },
            required=False
        ),
        
        # BDSM Specific Questions
        "bdsm_experience": FormField(
            name="bdsm_experience",
            step_id="bdsm_specific",
            type="choice",
            label={
                "he": "מה הניסיון שלך בבדס״מ?",
                "en": "What is your BDSM experience?"
            },
            required=True,
            options=[
                {"value": "none_not_interested", "text": {"he": "אין לי נסיון וגם לא מתעניין.ת בבדס\"מ", "en": "No experience and not interested in BDSM"}},
                {"value": "none_interested_top", "text": {"he": "אין לי נסיון אבל מעניין אותי לנסות לשלוט", "en": "No experience but interested in trying to top"}},
                {"value": "none_interested_bottom", "text": {"he": "אין לי נסיון אבל מעניין אותי לנסות להישלט", "en": "No experience but interested in trying to bottom"}},
                {"value": "experienced_top", "text": {"he": "יש לי נסיון בתור טופ/שולט.ת", "en": "I have experience as a top/dominant"}},
                {"value": "experienced_bottom", "text": {"he": "יש לי נסיון בתור בוטום/נשלט.ת", "en": "I have experience as a bottom/submissive"}},
                {"value": "other", "text": {"he": "אחר", "en": "Other"}}                
            ]
        ),
        "bdsm_declaration": FormField(
            name="bdsm_declaration",
            step_id="bdsm_specific",
            type="choice",
            label={
                "he": "כל אירועי הליין הינם בדסמ פרנדלי, ויכללו אקטים בדס''מים / מיניים שונים על פי רצון המשתתפים. איני מחוייב.ת להשתתף באף אקט ואסרב בנימוס אם יציעו לי אקט שאיני מעוניין.ת בו",
                "en": "All the lines events are BDSM friendly, and will include various BDSM / sexual acts according to the wishes of the participants. I am not obliged to participate in any act and will politely refuse an offer for an act that I am not interested in."
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "אני מסכים/ה", "en": "I agree"}},
                {"value": "no", "text": {"he": "איני מסכים/ה", "en": "I do not agree"}}
            ]
        ),
        "is_play_with_partner_only": FormField(
            name="is_play_with_partner_only",
            step_id="bdsm_specific",
            type="choice",
            label={
                "he": "האם תשחק/י רק עם הפרטנר?",
                "en": "Will you play only with your partner?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ],
            conditional={"field": "partner_or_single", "value": "partner"}
        ),
        "desired_play_partners": FormField(
            name="desired_play_partners",
            step_id="bdsm_specific",
            type="checkbox",
            label={
                "he": "עם מי ארצה לשחק?",
                "en": "With whom would I like to play?"
            },
            options=[
                {"value": "all_genders", "text": {"he": "יש לי עניין עם כל המגדרים", "en": "I am interested in all genders"}},
                {"value": "women_only", "text": {"he": "יש לי עניין עם נשים* בלבד", "en": "I am interested in women* only"}},
                {"value": "men_only", "text": {"he": "יש לי עניין עם גברים* בלבד", "en": "I am interested in men* only"}},
                {"value": "couples", "text": {"he": "יש לי עניין עם זוג", "en": "I am interested in couples"}},
                {"value": "partner_dependent", "text": {"he": "יש לי עניין אך זה תלוי בהסכמות של בן/בת הזוג", "en": "I am interested but it depends on my partner's consent"}}
            ],
            conditional={"field": "is_play_with_partner_only", "value": "no", "or_field": "partner_or_single", "or_value": "single"}
        ),
        "contact_type": FormField(
            name="contact_type",
            step_id="bdsm_specific",
            type="choice",
            label={
                "he": "סוג מגע רצוי",
                "en": "Desired type of contact"
            },
            required=True,
            options=[
                {"value": "bdsm_only", "text": {"he": "בדס״מ בלבד", "en": "BDSM only"}},
                {"value": "bdsm_and_sexual", "text": {"he": "בדס״מ ומיניות", "en": "BDSM and sexual"}},
                {"value": "other", "text": {"he": "אחר", "en": "Other"}}
            ],
            conditional={"field": "is_play_with_partner_only", "value": "no", "or_field": "partner_or_single", "or_value": "single"}
        ),
        "contact_type_other": FormField(
            name="contact_type_other",
            step_id="bdsm_specific",
            type="text",
            label={
                "he": "אנא פרט/י את סוג מגע הרצוי",
                "en": "Please specify your desired contact type"
            },
            placeholder={
                "he": "סוג מגע רצוי",
                "en": "Desired contact type"
            },
            conditional={"field": "contact_type", "value": "other"}
        ),
        "share_bdsm_interests": FormField(
            name="share_bdsm_interests",
            step_id="bdsm_specific",
            type="choice",
            label={
                "he": "האם תרצה/י לשתף את תחומי העניין שלך בבדס״מ?",
                "en": "Would you like to share your BDSM interests?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "limits_preferences_matrix": FormField(
            name="limits_preferences_matrix",
            step_id="bdsm_specific",
            type="choice",
            label={
                "he": "האם תרצה/י למלא מטריצת גבולות והעדפות?",
                "en": "Would you like to fill out a boundaries and preferences matrix?"
            },
            required=False,
            options=[
                {"value": "yes", "text": {"he": "כן, אשמח/ה", "en": "Yes, I'd be happy to"}},
                {"value": "no", "text": {"he": "לא, תודה", "en": "No, thank you"}}
            ],
            conditional={"field": "share_bdsm_interests", "value": "yes"}
        ),
        "boundaries_text": FormField(
            name="boundaries_text",
            step_id="bdsm_specific",
            type="text",
            label={
                "he": "גבולות - מה לא ארצה/י?",
                "en": "Boundaries - what don't you want?"
            },
            placeholder={
                "he": "ספר/י לנו על הגבולות שלך",
                "en": "Tell us about your boundaries"
            },
            required=True,
            conditional={"field": "share_bdsm_interests", "value": "yes"}
        ),
        "preferences_text": FormField(
            name="preferences_text",
            step_id="bdsm_specific",
            type="text",
            label={
                "he": "העדפות - מה כן ארצה/י?",
                "en": "Preferences - what do you want?"
            },
            placeholder={
                "he": "ספר/י לנו על ההעדפות שלך (אופציונלי)",
                "en": "Tell us about your preferences (optional)"
            },
            required=False,
            conditional={"field": "share_bdsm_interests", "value": "yes"}
        ),
        "bdsm_comments": FormField(
            name="bdsm_comments",
            step_id="bdsm_specific",
            type="text",
            label={
                "he": "הערות נוספות",
                "en": "Additional comments"
            },
            placeholder={
                "he": "כל דבר נוסף שתרצה/י לשתף",
                "en": "Anything else you'd like to share"
            },
            required=False
        ),
        
        # Food and Alcohol
        "food_restrictions": FormField(
            name="food_restrictions",
            step_id="food_alcohol",
            type="checkbox",
            label={
                "he": "מגבלות אוכל",
                "en": "Food restrictions"
            },
            options=[
                {"value": "none", "text": {"he": "אין מגבלות", "en": "No restrictions"}},
                {"value": "vegetarian", "text": {"he": "צמחוני/ת", "en": "Vegetarian"}},
                {"value": "vegan", "text": {"he": "טבעוני/ת", "en": "Vegan"}},
                {"value": "kosher", "text": {"he": "כשרות", "en": "Kosher"}},
                {"value": "gluten_free", "text": {"he": "ללא גלוטן", "en": "Gluten-free"}},
                {"value": "dairy_free", "text": {"he": "ללא מוצרי חלב", "en": "Dairy-free"}},
                {"value": "allergies", "text": {"he": "אלרגיות", "en": "Allergies"}}
            ]
        ),
        "food_comments": FormField(
            name="food_comments",
            step_id="food_alcohol",
            type="text",
            label={
                "he": "הערות לגבי אוכל",
                "en": "Food comments"
            },
            placeholder={
                "he": "אופציונלי",
                "en": "Optional"
            },
            required=False
        ),
        "alcohol_in_event": FormField(
            name="alcohol_in_event",
            step_id="food_alcohol",
            type="choice",
            label={
                "he": "האם תרצה/י אלכוהול באירוע? (בתוספת תשלום)",
                "en": "Would you like alcohol at the event? (with additional payment)"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "alcohol_preference": FormField(
            name="alcohol_preference",
            step_id="food_alcohol",
            type="text",
            label={
                "he": "העדפת אלכוהול",
                "en": "Alcohol preference"
            },
            required=False
        ),
        
        # Commitments and Rules
        "agree_participant_commitment": FormField(
            name="agree_participant_commitment",
            step_id="commitments",
            type="choice",
            label={
                "he": "האם אתה/את מסכים/ה להתחייבות המשתתף?",
                "en": "Do you agree to the participant commitment?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "enthusiastic_verbal_consent_commitment": FormField(
            name="enthusiastic_verbal_consent_commitment",
            step_id="commitments",
            type="choice",
            label={
                "he": "האם אתה/את מתחייב/ת להסכמה מילולית נלהבת?",
                "en": "Do you commit to enthusiastic verbal consent?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "agree_line_rules": FormField(
            name="agree_line_rules",
            step_id="commitments",
            type="choice",
            label={
                "he": "האם אתה/את מסכים/ה לחוקי הליין?",
                "en": "Do you agree to the line rules?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        
        # Helpers and DM
        "wants_to_helper": FormField(
            name="wants_to_helper",
            step_id="helpers_dm",
            type="choice",
            label={
                "he": "האם תרצה/י להיות הלפר?",
                "en": "Would you like to be a helper?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "maybe", "text": {"he": "אולי", "en": "Maybe"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "helper_shifts": FormField(
            name="helper_shifts",
            step_id="helpers_dm",
            type="checkbox",
            label={
                "he": "איזה משמרות תרצה/י?",
                "en": "Which shifts would you like?"
            },
            options=[
                {"value": "opening", "text": {"he": "פתיחה (לפני האירוע)", "en": "Opening (before event)"}},
                {"value": "closing", "text": {"he": "סגירה (אחרי האירוע)", "en": "Closing (after event)"}}
            ],
            conditional={"field": "wants_to_helper", "value": ["yes", "maybe"]}
        ),
        "is_surtified_DM": FormField(
            name="is_surtified_DM",
            step_id="helpers_dm",
            type="choice",
            label={
                "he": "האם את/ה DM מוסמך/ת?",
                "en": "Are you a certified DM?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "wants_to_DM": FormField(
            name="wants_to_DM",
            step_id="helpers_dm",
            type="choice",
            label={
                "he": "האם תרצה/י להיות DM?",
                "en": "Would you like to be a DM?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "maybe", "text": {"he": "אולי", "en": "Maybe"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ],
            conditional={"field": "is_surtified_DM", "value": "yes"}
        ),
        "DM_shifts": FormField(
            name="DM_shifts",
            step_id="helpers_dm",
            type="checkbox",
            label={
                "he": "איזה משמרות DM תרצה/י?",
                "en": "Which DM shifts would you like?"
            },
            options=[
                {"value": "opening", "text": {"he": "פתיחה (לפני האירוע)", "en": "Opening (before event)"}},
                {"value": "closing", "text": {"he": "סגירה (אחרי האירוע)", "en": "Closing (after event)"}}
            ],
            conditional={"field": "wants_to_DM", "value": ["yes", "maybe"]}
        ),
        
        # Returning User Specific Fields
        "update_bdsm": FormField(
            name="update_bdsm",
            step_id="temp",
            type="choice",
            label={
                "he": "האם תרצה/י לעדכן את המידע הבדס״מ שלך?",
                "en": "Would you like to update your BDSM information?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "update_food": FormField(
            name="update_food",
            step_id="temp",
            type="choice",
            label={
                "he": "האם תרצה/י לעדכן את המידע על האוכל שלך?",
                "en": "Would you like to update your food information?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        ),
        "update_alcohol": FormField(
            name="update_alcohol",
            step_id="temp",
            type="choice",
            label={
                "he": "האם תרצה/י לעדכן את העדפת האלכוהול שלך?",
                "en": "Would you like to update your alcohol preference?"
            },
            required=True,
            options=[
                {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                {"value": "no", "text": {"he": "לא", "en": "No"}}
            ]
        )
    }
    
    def __init__(self, event_type: EventType, language: Language = Language.HEBREW):
        self.event_type = event_type
        self.language = language
        self.steps = self._build_steps()
    
    def _build_steps(self) -> List[FormStep]:
        """Build form steps based on event type."""
        steps = []
        
        # Step 0: Language Selection (if not already set)
        if not self.language:
            steps.append(self._create_language_step())
        
        # Step 1: Event Details
        steps.append(self._create_event_details_step())
        
        # Step 2: Personal Information
        steps.append(self._create_personal_info_step())
        
        # Step 3: Event-Specific Questions (conditional)
        specific_step = self._create_specific_event_step()
        if specific_step:
            steps.append(specific_step)

        # Step 4: Food and Alcohol
        steps.append(self._create_food_alcohol_step())
        
        # Step 5: Rules and Agreements
        steps.append(self._create_rules_agreement_step())
        
        # Step 6: Helpers and DM
        steps.append(self._create_helpers_dm_step())
        
        # Step 7: Theme (optional)
        steps.append(self._create_theme_step())
        
        return steps
    
    def _create_language_step(self) -> FormStep:
        """Create language selection step."""
        return 
    def _create_event_details_step(self) -> FormStep:
        """Create event details step."""
        return FormStep(
            id="event_details",
            title={
                "he": "פרטי האירוע",
                "en": "Event Details"
            },
            fields=[ ]
        )
    
    def _create_personal_info_step(self) -> FormStep:
        """Create personal information step."""
        return FormStep(
            id="personal_info",
            title={
                "he": "פרטים אישיים",
                "en": "Personal Information"
            },
            fields=[
            ]
        )
    
    def _create_specific_event_step(self) -> FormStep:
        """Create specific event questions step."""
        pass
    
    def _create_food_alcohol_step(self) -> FormStep:
        """Create food and alcohol preferences step."""
        return FormStep(
            id="food_alcohol",
            title={
                "he": "אוכל ואלכוהול",
                "en": "Food and Alcohol"
            },
            fields=[
                FormField(
                    name="food_restrictions",
                    type="checkbox",
                    label={
                        "he": "מגבלות אוכל",
                        "en": "Food restrictions"
                    },
                    options=[
                        {"value": "vegetarian", "text": {"he": "צמחוני/ת", "en": "Vegetarian"}},
                        {"value": "vegan", "text": {"he": "טבעוני/ת", "en": "Vegan"}},
                        {"value": "gluten_free", "text": {"he": "ללא גלוטן", "en": "Gluten-free"}},
                        {"value": "dairy_free", "text": {"he": "ללא מוצרי חלב", "en": "Dairy-free"}},
                        {"value": "none", "text": {"he": "אין מגבלות", "en": "No restrictions"}}
                    ]
                ),
                FormField(
                    name="alcohol_preference",
                    type="choice",
                    label={
                        "he": "האם תרצה/י אלכוהול?",
                        "en": "Would you like alcohol?"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                        {"value": "maybe", "text": {"he": "אולי", "en": "Maybe"}},
                        {"value": "no", "text": {"he": "לא", "en": "No"}}
                    ]
                ),
                FormField(
                    name="favorite_alcohol",
                    type="text",
                    label={
                        "he": "מה האלכוהול האהוב עליך?",
                        "en": "What's your favorite alcohol?"
                    },
                    placeholder={
                        "he": "אופציונלי",
                        "en": "Optional"
                    },
                    conditional={"field": "alcohol_preference", "value": ["yes", "maybe"]}
                )
            ]
        )
    
    def _create_rules_agreement_step(self) -> FormStep:
        """Create rules and agreements step."""
        return FormStep(
            id="rules_agreement",
            title={
                "he": "חוקים והסכמות",
                "en": "Rules and Agreements"
            },
            fields=[
                FormField(
                    name="rules_read",
                    type="choice",
                    label={
                        "he": "האם קראת את חוקי המרחב?",
                        "en": "Have you read the space rules?"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                        {"value": "no", "text": {"he": "לא", "en": "No"}}
                    ]
                ),
                FormField(
                    name="rules_agreed",
                    type="choice",
                    label={
                        "he": "האם אתה/את מסכים/ה לחוקי המרחב?",
                        "en": "Do you agree to the space rules?"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                        {"value": "no", "text": {"he": "לא", "en": "No"}}
                    ]
                ),
                FormField(
                    name="ginger_confirmation",
                    type="text",
                    label={
                        "he": "כתוב 'זנגביל' לאישור",
                        "en": "Type 'ginger' to confirm"
                    },
                    required=True,
                    validation_rules={"type": "exact_match", "value": "זנגביל"}
                )
            ]
        )
    
    def _create_helpers_dm_step(self) -> FormStep:
        """Create helpers and DM step."""
        return FormStep(
            id="helpers_dm",
            title={
                "he": "הלפרים ואחראי מרחב",
                "en": "Helpers and Space Manager"
            },
            fields=[
                FormField(
                    name="wants_to_help",
                    type="choice",
                    label={
                        "he": "האם תרצה/י לעזור בהכנות לפני / אחרי האירוע?",
                        "en": "Would you like to help as a helper?"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                        {"value": "maybe", "text": {"he": "אולי", "en": "Maybe"}},
                        {"value": "no", "text": {"he": "לא", "en": "No"}}
                    ]
                ),
                FormField(
                    name="helper_shifts",
                    type="checkbox",
                    label={
                        "he": "איזה משמרות תרצה/י?",
                        "en": "Which shifts would you like?"
                    },
                    options=[
                        {"value": "opening", "text": {"he": "פתיחה (לפני האירוע)", "en": "Opening (before event)"}},
                        {"value": "closing", "text": {"he": "סגירה (אחרי האירוע)", "en": "Closing (after event)"}}
                    ],
                    conditional={"field": "wants_to_help", "value": ["yes", "maybe"]}
                ),
                FormField(
                    name="wants_to_dm",
                    type="choice",
                    label={
                        "he": "האם תרצה/י להיות DM/אחראי מרחב?",
                        "en": "Would you like to be a DM/Space Manager?"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "כן", "en": "Yes"}},
                        {"value": "maybe", "text": {"he": "אולי", "en": "Maybe"}},
                        {"value": "no", "text": {"he": "לא", "en": "No"}}
                    ]
                )
            ]
        )
    
    def _create_theme_step(self) -> FormStep:
        """Create theme step (optional)."""
        return FormStep(
            id="theme",
            title={
                "he": "תמה ואווירה",
                "en": "Theme and Atmosphere"
            },
            fields=[
                FormField(
                    name="theme_preferences",
                    type="text",
                    label={
                        "he": "האם יש לך העדפות לתמה או אווירה?",
                        "en": "Do you have any theme or atmosphere preferences?"
                    },
                    placeholder={
                        "he": "אופציונלי - ספר/י לנו על העדפותיך",
                        "en": "Optional - tell us about your preferences"
                    },
                    required=False
                )
            ]
        )
    
    def get_step(self, step_id: str) -> Optional[FormStep]:
        """Get a specific step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_next_step(self, current_step_id: str, answers: Dict[str, Any]) -> Optional[FormStep]:
        """Get the next step based on current step and answers."""
        current_index = -1
        for i, step in enumerate(self.steps):
            if step.id == current_step_id:
                current_index = i
                break
        
        if current_index == -1:
            return None
        
        # Check if current step should be skipped based on answers
        if self._should_skip_step(self.steps[current_index], answers):
            return self.get_next_step(self.steps[current_index + 1].id, answers)
        
        # Return next step if available
        if current_index + 1 < len(self.steps):
            return self.steps[current_index + 1]
        
        return None
    
    def _should_skip_step(self, step: FormStep, answers: Dict[str, Any]) -> bool:
        """Check if a step should be skipped based on answers."""
        if not step.conditional:
            return False
        
        field_name = step.conditional["field"]
        expected_value = step.conditional["value"]
        
        if field_name not in answers:
            return True
        
        actual_value = answers[field_name]
        
        if isinstance(expected_value, list):
            return actual_value not in expected_value
        else:
            return actual_value != expected_value
    
    def validate_step(self, step_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Validate answers for a specific step."""
        step = self.get_step(step_id)
        if not step:
            return {"valid": False, "errors": ["Step not found"]}
        
        errors = []
        
        for field in step.fields:
            # Check if field should be shown based on conditions
            if field.conditional and not self._should_show_field(field, answers):
                continue  # Skip validation for hidden fields
            
            if field.required and field.name not in answers:
                errors.append(f"Field {field.name} is required")
                continue
            
            if field.name in answers:
                field_errors = self._validate_field(field, answers[field.name])
                errors.extend(field_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _should_show_field(self, field: FormField, answers: Dict[str, Any]) -> bool:
        """Check if a field should be shown based on its conditions."""
        if not field.conditional:
            return True
        
        # Check primary condition
        field_name = field.conditional["field"]
        expected_value = field.conditional["value"]
        
        primary_condition = False
        if field_name in answers:
            actual_value = answers[field_name]
            if isinstance(expected_value, list):
                primary_condition = actual_value in expected_value
            else:
                primary_condition = actual_value == expected_value
        
        # Check OR condition if exists
        if "or_field" in field.conditional and "or_value" in field.conditional:
            or_field_name = field.conditional["or_field"]
            or_expected_value = field.conditional["or_value"]
            
            or_condition = False
            if or_field_name in answers:
                or_actual_value = answers[or_field_name]
                if isinstance(or_expected_value, list):
                    or_condition = or_actual_value in or_expected_value
                else:
                    or_condition = or_actual_value == or_expected_value
            
            return primary_condition or or_condition
        
        return primary_condition
    
    def _validate_field(self, field: FormField, value: Any) -> List[str]:
        """Validate a single field."""
        errors = []
        
        if field.validation_rules:
            rule_type = field.validation_rules.get("type")
            
            if rule_type == "telegram_username":
                if not self._is_valid_telegram_username(value):
                    errors.append("Invalid Telegram username format")
            
            elif rule_type == "exact_match":
                expected = field.validation_rules.get("value")
                if value != expected:
                    errors.append(f"Value must be exactly '{expected}'")
            
            elif rule_type == "sti_test_date":
                if not self._is_valid_sti_test_date(value):
                    errors.append("STI test date must be within the last 3 months")
        
        return errors
    
    def _is_valid_telegram_username(self, username: str) -> bool:
        """Validate Telegram username format."""
        import re
        # Accept @username or t.me/username format
        pattern = r'^(@[a-zA-Z0-9_]{5,32}|t\.me/[a-zA-Z0-9_]{5,32})$'
        return bool(re.match(pattern, username))
    
    def _is_valid_sti_test_date(self, date_str: str) -> bool:
        """Validate STI test date (within last 3 months)."""
        from datetime import datetime, timedelta
        
        try:
            test_date = datetime.strptime(date_str, "%d/%m/%Y")
            # three_months_ago = datetime.now() - timedelta(days=90)
            return True # test_date >= three_months_ago
        except ValueError:
            return False 