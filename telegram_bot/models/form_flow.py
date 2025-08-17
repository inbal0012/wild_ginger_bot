"""
Form Flow Models - Models for the new FormFlowService
Following the form order specification and sequence diagram
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


class QuestionType(Enum):
    """Types of questions supported by the form flow."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    TELEGRAM_LINK = "telegram_link"
    FACEBOOK_LINK = "facebook_link"


class ValidationRuleType(Enum):
    """Types of validation rules."""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    REGEX = "regex"
    URL_FORMAT = "url_format"
    TELEGRAM_LINK = "telegram_link"
    FACEBOOK_LINK = "facebook_link"
    DATE_RANGE = "date_range"
    AGE_RANGE = "age_range"
    STI_TEST_DATE = "sti_test_date"
    UNIQUE = "unique"


class FormState(Enum):
    """Form states for the state machine."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    VALIDATION_ERROR = "validation_error"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Text:
    he: str
    en: str
    
    def get(self, language: str, fallback: str = "en") -> str:
        """Get text for the specified language with fallback."""
        if language == "he":
            return self.he
        elif language == "en":
            return self.en
        else:
            # Fallback to specified language or English
            return getattr(self, fallback, self.en)

@dataclass
class ValidationRule:
    """Validation rule for a question."""
    rule_type: ValidationRuleType
    error_message: Text
    params: Optional[Dict[str, Any]] = None


@dataclass
class SkipConditionItem:
    """Individual condition for skipping a question."""
    type: str  # "field_value" | "user_exists" | "event_type" | "user_type"
    operator: str = "equals"  # "equals" | "not_equals" | "in" | "not_in"
    field: Optional[str] = None
    value: Optional[Any] = None


@dataclass
class SkipCondition:
    """Condition for skipping a question."""
    operator: str  # "AND" | "OR" | "NOT"
    conditions: List[SkipConditionItem]

@dataclass
class QuestionOption:
    """Option for select/multi-select questions."""
    value: str
    text: Text

@dataclass
class QuestionDefinition:
    """Definition of a form question."""
    question_id: str
    question_type: QuestionType
    title: Text
    required: bool
    save_to: str  # "Registrations" for registration, "Users" for users
    validation_rules: List[ValidationRule] = field(default_factory=list)
    order: int = 0
    depends_on: Optional[List[str]] = None
    skip_condition: Optional[SkipCondition] = None
    options: Optional[List[QuestionOption]] = None
    placeholder: Optional[Text] = None


@dataclass
class ValidationResult:
    """Result of validation."""
    isValid: bool
    errors: List[str] = field(default_factory=list)
    nextQuestion: Optional[QuestionDefinition] = None


@dataclass
class FormContext:
    """Context for form processing."""
    user_id: int
    event_id: str
    event_type: str  # "play" | "cuddle"
    answers: Dict[str, Any] = field(default_factory=dict)
    language: str = "he"  # "he" | "en"


@dataclass
class FormStateData:
    """State data for a form session."""
    user_id: int
    event_id: str
    current_state: FormState
    current_question_id: Optional[str] = None
    answers: Dict[str, Any] = field(default_factory=dict)
    validation_errors: Dict[str, List[str]] = field(default_factory=dict)
    language: str = "he"
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class FormProgress:
    """Progress information for a form."""
    user_id: int
    event_id: str
    current_question: Optional[QuestionDefinition] = None
    completed_questions: int = 0
    total_questions: int = 0
    completion_percentage: float = 0.0
    language: str = "he"


@dataclass
class FormData:
    """Complete form data for registration."""
    user_id: int
    event_id: str
    answers: Dict[str, Any]
    language: str
    completed_at: datetime = field(default_factory=datetime.now)


@dataclass
class UpdateableFieldDTO:
    """DTO for fields that can be updated by returning users."""
    field_id: str
    field_name: Text
    current_value: Any
    field_type: str  # "text" | "select" | "multi_select" | "date" | "boolean"
    required: bool
    options: Optional[List[QuestionOption]] = None
    validation_rules: List[ValidationRule] = field(default_factory=list)


@dataclass
class UpdateResult:
    """Result of updating user data."""
    user_id: int
    updated_fields: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    errors: Optional[List[str]] = None 