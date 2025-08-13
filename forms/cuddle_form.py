"""
Cuddle Form Implementation - Handles registration forms specifically for cuddle events.
Extends the generic form with cuddle-specific questions and validation.
"""

from typing import Any, Dict, List, Optional
from .generic_form import GenericForm, EventType, Language, FormStep, FormField


class CuddleForm(GenericForm):
    """
    Cuddle-specific form implementation.
    Extends the generic form with cuddle-specific questions and validation.
    """
    
    def __init__(self, language: Language = Language.HEBREW):
        super().__init__(EventType.CUDDLE, language)
    
    def _create_specific_event_step(self) -> FormStep:
        """Create cuddle-specific questions step."""
        return FormStep(
            id="cuddle_specific",
            title={
                "he": "שאלות ספציפיות לכירבולייה",
                "en": "Cuddle-Specific Questions"
            },
            fields=[
                # Cuddle Experience
                FormField(
                    name="cuddle_experience",
                    type="checkbox",
                    label={
                        "he": "האם יש לך נסיון בכירבולייה?",
                        "en": "Do you have cuddle experience?"
                    },
                    required=True,
                    options=[
                        {"value": "no_experience", "text": {"he": "אין לי נסיון", "en": "I have no experience"}},
                        {"value": "some_experience", "text": {"he": "יש לי קצת נסיון", "en": "I have some experience"}},
                        {"value": "experienced", "text": {"he": "יש לי נסיון רב", "en": "I have a lot of experience"}}
                    ]
                ),
                
                # Cuddle Preferences
                FormField(
                    name="cuddle_preferences",
                    type="checkbox",
                    label={
                        "he": "מה העדפות הכירבולייה שלך?",
                        "en": "What are your cuddle preferences?"
                    },
                    options=[
                        {"value": "gentle", "text": {"he": "עדין/ה", "en": "Gentle"}},
                        {"value": "intimate", "text": {"he": "אינטימי/ת", "en": "Intimate"}},
                        {"value": "playful", "text": {"he": "שובב/ה", "en": "Playful"}},
                        {"value": "therapeutic", "text": {"he": "טיפולי", "en": "Therapeutic"}},
                        {"value": "other", "text": {"he": "אחר", "en": "Other"}}
                    ]
                ),
                
                # Cuddle Experience Other Text (conditional)
                FormField(
                    name="cuddle_experience_other",
                    type="text",
                    label={
                        "he": "אנא פרט/י את הניסיון שלך בכירבולייה",
                        "en": "Please specify your cuddle experience"
                    },
                    placeholder={
                        "he": "ספר/י על הניסיון שלך...",
                        "en": "Tell us about your experience..."
                    },
                    conditional={"field": "cuddle_experience", "value": "other"}
                ),
                
                # Comfort Level
                FormField(
                    name="comfort_level",
                    type="choice",
                    label={
                        "he": "מה רמת הנוחות שלך עם מגע פיזי?",
                        "en": "What is your comfort level with physical touch?"
                    },
                    required=True,
                    options=[
                        {"value": "very_comfortable", "text": {"he": "מאוד נוח לי", "en": "Very comfortable"}},
                        {"value": "comfortable", "text": {"he": "נוח לי", "en": "Comfortable"}},
                        {"value": "somewhat_comfortable", "text": {"he": "קצת נוח לי", "en": "Somewhat comfortable"}},
                        {"value": "not_comfortable", "text": {"he": "לא נוח לי", "en": "Not comfortable"}}
                    ]
                )
            ]
        )
    
    def _validate_cuddle_specific_fields(self, answers: Dict[str, Any]) -> List[str]:
        """Validate cuddle-specific fields."""
        errors = []
        
        # Check if comfort level is provided
        if "comfort_level" not in answers:
            errors.append("Comfort level is required")
        
        # Check if cuddle experience is provided
        if "cuddle_experience" not in answers:
            errors.append("Cuddle experience is required")
        
        return errors
    
    def validate_step(self, step_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Override validation for cuddle-specific step."""
        if step_id == "cuddle_specific":
            errors = self._validate_cuddle_specific_fields(answers)
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }
        
        # Use parent validation for other steps
        return super().validate_step(step_id, answers)
    
    def get_cuddle_specific_data(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract cuddle-specific data from answers."""
        return {
            "cuddle_experience": answers.get("cuddle_experience"),
            "cuddle_preferences": answers.get("cuddle_preferences"),
            "cuddle_experience_other": answers.get("cuddle_experience_other"),
            "comfort_level": answers.get("comfort_level")
        } 