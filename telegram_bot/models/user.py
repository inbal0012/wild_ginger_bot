from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class UserDTO:
    full_name: str
    user_id: str
    telegram_user_id: str
    telegram_username: str
    facebook_profile: str
    birth_date: str
    gender: str
    sexual_orientation_gender: str
    pronouns: str
    sexual_orientation: str
    intro_text: str
    experiences: str
    food_restrictions: str
    alcohol_preference: str
    last_test_date: str
    cool_about_you: str
    intro_opt_in: bool
    intro_last_updated: str
    created_at: str
    updated_at: str
    language: str = "en"

class CreateUserFromTelegramDTO:
    full_name: str
    telegram_user_id: str
    telegram_username: str
    language: str
    
    def __init__(self, full_name: str, telegram_user_id: str, telegram_username: str, language: str):
        self.full_name = full_name
        self.telegram_user_id = telegram_user_id
        self.telegram_username = telegram_username
        self.language = language

    
    def __post_init__(self):
        # Optional validation
        if len(self.language) != 2:
            raise ValueError("language must be a 2-character code")
