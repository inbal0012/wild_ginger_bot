from dataclasses import dataclass
from typing import List, Dict

@dataclass
class TelegramPollFields:
    question: str
    options: List[str]
    is_anonymous: bool
    allows_multiple_answers: bool

@dataclass
class TelegramPollData:
    id: str
    question_field: str
    question: str
    options: List[str]
    chat_id: str
    message_id: int
    creator: str
    type: str
    votes: Dict[int, List[str]]