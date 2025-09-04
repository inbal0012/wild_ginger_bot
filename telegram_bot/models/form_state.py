"""
FormState model - Represents the state of a form for a specific user.
"""

import asyncio
from typing import Any, Dict, Optional


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