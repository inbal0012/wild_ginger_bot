"""
Play Form Implementation - Handles registration forms specifically for play events.
Extends the generic form with play-specific questions and validation.
"""

from typing import Any, Dict, List, Optional
from .generic_form import GenericForm, EventType, Language, FormStep, FormField


class PlayForm(GenericForm):
    """
    Play-specific form implementation.
    Extends the generic form with BDSM-specific questions and validation.
    """
    
    def __init__(self, language: Language = Language.HEBREW):
        super().__init__(EventType.PLAY, language)
    
    def _create_specific_event_step(self) -> FormStep:
        """Create enhanced play-specific questions step."""
        return FormStep(
            id="play_specific",
            title={
                "he": "שאלות ספציפיות לפליי",
                "en": "Play-Specific Questions"
            },
            fields=[
                # BDSM Experience
                FormField(
                    name="bdsm_experience",
                    type="choice",
                    label={
                        "he": "מה הניסיון שלך בבדס״מ?",
                        "en": "What is your BDSM experience?"
                    },
                    required=True,
                    options=[
                        {"value": "none", "text": {"he": "אין ניסיון", "en": "No experience"}},
                        {"value": "beginner", "text": {"he": "מתחיל/ה", "en": "Beginner"}},
                        {"value": "intermediate", "text": {"he": "בינוני/ת", "en": "Intermediate"}},
                        {"value": "advanced", "text": {"he": "מתקדם/ת", "en": "Advanced"}}
                    ]
                ),
                
                # STI Test Date (Required for play events)
                FormField(
                    name="last_sti_test",
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
                    validation_rules={"type": "sti_test_date", "max_days_ago": 90}
                ),
                
                # BDSM Interests
                FormField(
                    name="bdsm_interests",
                    type="checkbox",
                    label={
                        "he": "תחומי עניין בבדס״מ",
                        "en": "BDSM interests"
                    },
                    options=[
                        {"value": "bondage", "text": {"he": "קשירות", "en": "Bondage"}},
                        {"value": "impact", "text": {"he": "מכות", "en": "Impact Play"}},
                        {"value": "sensation", "text": {"he": "תחושות", "en": "Sensation Play"}},
                        {"value": "roleplay", "text": {"he": "משחק תפקידים", "en": "Roleplay"}},
                        {"value": "wax", "text": {"he": "שעווה", "en": "Wax Play"}},
                        {"value": "ice", "text": {"he": "קרח", "en": "Ice Play"}},
                        {"value": "electro", "text": {"he": "אלקטרו", "en": "Electro Play"}},
                        {"value": "other", "text": {"he": "אחר", "en": "Other"}}
                    ]
                ),
                
                # BDSM Declaration
                FormField(
                    name="bdsm_declaration",
                    type="choice",
                    label={
                        "he": "הצהרה: הליין בדס״מ/מיני; איני מחויב/ת להשתתף",
                        "en": "Declaration: The line is BDSM/sexual; I am not obligated to participate"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "אני מסכים/ה", "en": "I agree"}},
                        {"value": "no", "text": {"he": "איני מסכים/ה", "en": "I do not agree"}}
                    ]
                ),
                
                # Play with Partner Only (conditional)
                FormField(
                    name="play_with_partner_only",
                    type="choice",
                    label={
                        "he": "האם תשחק/י רק עם הפרטנר או גם עם אחרים?",
                        "en": "Will you play only with your partner or also with others?"
                    },
                    required=True,
                    options=[
                        {"value": "partner_only", "text": {"he": "רק עם הפרטנר", "en": "Partner only"}},
                        {"value": "others_too", "text": {"he": "גם עם אחרים", "en": "With others too"}}
                    ],
                    conditional={"field": "balance_status", "value": "partner"}
                ),
                
                # Desired Play Partners
                FormField(
                    name="desired_play_partners",
                    type="checkbox",
                    label={
                        "he": "עם מי ארצה לשחק?",
                        "en": "With whom would I like to play?"
                    },
                    options=[
                        {"value": "men", "text": {"he": "גברים", "en": "Men"}},
                        {"value": "women", "text": {"he": "נשים", "en": "Women"}},
                        {"value": "non_binary", "text": {"he": "לא בינארי/ת", "en": "Non-binary"}},
                        {"value": "everyone", "text": {"he": "כולם/ן", "en": "Everyone"}}
                    ],
                    conditional={"field": "play_with_partner_only", "value": "others_too", "or_field": "balance_status", "or_value": "single"}
                ),
                
                # Type of Contact Desired
                FormField(
                    name="contact_type",
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
                    ]
                ),
                
                # contact type Other Text (conditional)
                FormField(
                    name="contact_type_other",
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
                
                # Boundaries Matrix (Optional but recommended)
                FormField(
                    name="boundaries_matrix",
                    type="choice",
                    label={
                        "he": "האם תרצה/י למלא מטריצת גבולות והעדפות?",
                        "en": "Would you like to fill out a boundaries and preferences matrix?"
                    },
                    required=True,
                    options=[
                        {"value": "yes", "text": {"he": "כן, אשמח/ה", "en": "Yes, I'd be happy to"}},
                        {"value": "no", "text": {"he": "לא, תודה", "en": "No, thank you"}}
                    ]
                ),
                
                # Boundaries Text (Required if matrix is yes)
                FormField(
                    name="boundaries_text",
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
                    conditional={"field": "boundaries_matrix", "value": "yes"}
                ),
                
                # Preferences Text (Optional)
                FormField(
                    name="preferences_text",
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
                    conditional={"field": "boundaries_matrix", "value": "yes"}
                ),
                
                # Additional Comments
                FormField(
                    name="play_comments",
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
                )
            ]
        )
    
    def _validate_play_specific_fields(self, answers: Dict[str, Any]) -> List[str]:
        """Validate play-specific fields."""
        errors = []
        
        # Check BDSM declaration
        if answers.get("bdsm_declaration") != "yes":
            errors.append("BDSM declaration must be agreed to")
        
        # Check STI test date
        sti_date = answers.get("last_sti_test")
        if sti_date and not self._is_valid_sti_test_date(sti_date):
            errors.append("STI test date must be within the last 3 months")
        
        # Check boundaries text if matrix is yes
        if answers.get("boundaries_matrix") == "yes" and not answers.get("boundaries_text"):
            errors.append("Boundaries text is required when matrix is selected")
        
        return errors
    
    def validate_step(self, step_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Override to add play-specific validation."""
        # Get base validation
        base_validation = super().validate_step(step_id, answers)
        
        # Add play-specific validation for play_specific step
        if step_id == "play_specific":
            play_errors = self._validate_play_specific_fields(answers)
            base_validation["errors"].extend(play_errors)
            base_validation["valid"] = len(base_validation["errors"]) == 0
        
        return base_validation
    
    def get_play_specific_data(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract play-specific data from form answers."""
        return {
            "bdsm_experience": answers.get("bdsm_experience"),
            "last_sti_test": answers.get("last_sti_test"),
            "bdsm_interests": answers.get("bdsm_interests", []),
            "bdsm_declaration": answers.get("bdsm_declaration") == "yes",
            "play_with_partner_only": answers.get("play_with_partner_only"),
            "desired_play_partners": answers.get("desired_play_partners", []),
            "contact_type": answers.get("contact_type"),
            "boundaries_matrix": answers.get("boundaries_matrix") == "yes",
            "boundaries_text": answers.get("boundaries_text"),
            "preferences_text": answers.get("preferences_text"),
            "play_comments": answers.get("play_comments")
        } 