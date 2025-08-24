from typing import Dict, List, Optional, Any
from enum import Enum
import logging

from ..config.settings import settings
from ..services.sheets_service import SheetsService
from ..services.message_service import MessageService
from ..exceptions import RegistrationNotFoundException, ServiceException, ConversationStateException

logger = logging.getLogger(__name__)

class GetToKnowState(Enum):
    IDLE = "idle"
    GET_TO_KNOW_ACTIVE = "get_to_know_active"
    GET_TO_KNOW_FOLLOWUP = "get_to_know_followup"

class GetToKnowService:
    """Service for handling get-to-know flow"""
    
    def __init__(self, sheets_service: SheetsService = None, message_service: MessageService = None):
        self.sheets_service = sheets_service or SheetsService()
        self.message_service = message_service or MessageService()
        
        # Store conversation states (in production, this would be in Redis or database)
        self.user_conversation_states: Dict[str, Dict[str, Any]] = {}
        
        # Get-to-know questions from configuration
        self.get_to_know_questions = {
            'he': {
                'first_question': "אשמח לשמוע עליך קצת.\nקצת מי אתה, קצת על הניסיון שלך עם אירועים מהסוג הזה, קצת משהו מגניב עליך 😃",
                'followup_question': "אשמח לשמוע משהו מגניב ומעניין עליך. לא חובה (ואף רצוי) לא מתוך העולם האלטרנטיבי.",
                'completion_message': "🎉 תודה על השיתוף! זה עוזר לנו ליצור סביבה בטוחה ונוחה לכולם.",
                'already_completed': "✅ כבר השלמת את חלק ההיכרות!",
                'no_registration': "אנא קשר את ההרשמה שלך קודם עם /start",
                'error_saving': "❌ שגיאה בשמירת התשובות. אנא נסה שוב."
            },
            'en': {
                'first_question': "I'd love to hear about you a bit.\nA bit about who you are, your experience with these types of events, something cool about you 😃",
                'followup_question': "I'd love to hear something cool and interesting about you. Not required (and preferably not) from the alternative world.",
                'completion_message': "🎉 Thanks for sharing! This helps us create a safe and comfortable environment for everyone.",
                'already_completed': "✅ You've already completed the get-to-know section!",
                'no_registration': "Please link your registration first with /start",
                'error_saving': "❌ Error saving responses. Please try again."
            }
        }
        
        # Boring answer detection patterns
        self._setup_answer_analysis()
    
    def _setup_answer_analysis(self):
        """Set up patterns for analyzing answer quality"""
        # Boring patterns (in Hebrew and English)
        self.boring_patterns = [
            'אמממ', 'אממ', 'המממ', 'נו', 'אמ', 'היי', 'שלום',
            'umm', 'hmm', 'ummm', 'hmmm', 'uhh', 'errr', 'well',
            'idk', "i don't know", 'regular', 'normal', 'nothing', 'boring', 'dunno',
            'not sure', 'whatever', 'meh', 'dunno what to write', 'dont know'
        ]
        
        # Strong boring indicators (immediate red flags)
        self.strong_boring_indicators = [
            'אמממ', 'האמת שאין לי מושג', 'אין לי מושג', 'לא יודע מה לכתוב'
        ]
        
        # Good answer indicators
        self.good_answer_indicators = [
            # Hebrew
            'אוהב', 'אוהבת', 'מעניין', 'מעניינת', 'תחביב', 'עובד', 'עובדת',
            'לומד', 'לומדת', 'מנגן', 'שר', 'אנרגיות', 'ידידותי', 'חייכן',
            'מוזיקה', 'ספורט', 'אמנות', 'טבע', 'נסיעות', 'קריאה',
            # English  
            'love', 'enjoy', 'work', 'study', 'music', 'sports', 'art', 'travel',
            'reading', 'dancing', 'guitar', 'interesting', 'hobby'
        ]
        
        # Negative contexts that negate good indicators
        self.negative_contexts = [
            'אין לי מושג למשהו מגניב', 'לא יודע משהו מגניב',
            'אין לי ניסיון', 'לא יודע מה', 'נסיון מועט'
        ]
    
    async def start_get_to_know_flow(self, telegram_user_id: str) -> Dict[str, Any]:
        """Start the get-to-know conversation flow"""
        try:
            # Find user's registration
            registration = await self.sheets_service.find_submission_by_telegram_id(telegram_user_id)
            if not registration:
                return {
                    'success': False,
                    'message': self.get_to_know_questions['en']['no_registration'],
                    'reason': 'no_registration'
                }
            
            submission_id = registration.get('submission_id')
            language = registration.get('language', 'he')
            
            # Check if already completed
            if registration.get('get_to_know', False):
                return {
                    'success': False,
                    'message': self.get_to_know_questions[language]['already_completed'],
                    'reason': 'already_completed'
                }
            
            # Set up conversation state
            self.user_conversation_states[telegram_user_id] = {
                'flow': 'get_to_know',
                'step': 'first_question',
                'language': language,
                'submission_id': submission_id,
                'responses': {}
            }
            
            return {
                'success': True,
                'message': self.get_to_know_questions[language]['first_question'],
                'state': 'awaiting_first_response'
            }
            
        except Exception as e:
            logger.error(f"Error starting get-to-know flow: {e}")
            raise ServiceException(f"Failed to start get-to-know flow: {e}")
    
    async def handle_get_to_know_response(self, telegram_user_id: str, response: str) -> Dict[str, Any]:
        """Handle user responses in the get-to-know flow"""
        try:
            state = self.user_conversation_states.get(telegram_user_id)
            
            if not state or state.get('flow') != 'get_to_know':
                # Not in conversation flow
                return {'success': False, 'in_conversation': False}
            
            current_step = state['step']
            language = state['language']
            response = response.strip()
            
            if current_step == 'first_question':
                return await self._handle_first_response(telegram_user_id, response, state)
            elif current_step == 'followup_question':
                return await self._handle_followup_response(telegram_user_id, response, state)
            else:
                # Unknown step
                return {'success': False, 'error': 'unknown_conversation_step'}
                
        except Exception as e:
            logger.error(f"Error handling get-to-know response: {e}")
            raise ServiceException(f"Failed to handle response: {e}")
    
    async def _handle_first_response(self, telegram_user_id: str, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the first response in get-to-know flow"""
        language = state['language']
        
        # Store the first response
        state['responses']['first_answer'] = response
        
        # Check if response is boring
        if self.is_boring_answer(response):
            # Ask follow-up question
            state['step'] = 'followup_question'
            return {
                'success': True,
                'message': self.get_to_know_questions[language]['followup_question'],
                'state': 'awaiting_followup_response',
                'needs_followup': True
            }
        else:
            # Good answer, complete the flow
            return await self._complete_get_to_know_flow(telegram_user_id, state)
    
    async def _handle_followup_response(self, telegram_user_id: str, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the follow-up response in get-to-know flow"""
        # Store the follow-up response
        state['responses']['followup_answer'] = response
        
        # Complete the flow regardless of answer quality
        return await self._complete_get_to_know_flow(telegram_user_id, state)
    
    async def _complete_get_to_know_flow(self, telegram_user_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the get-to-know flow and store responses"""
        try:
            submission_id = state['submission_id']
            responses = state['responses']
            language = state['language']
            
            # Combine responses for storage
            combined_response = ""
            if 'first_answer' in responses:
                combined_response += responses['first_answer']
            if 'followup_answer' in responses:
                if combined_response:
                    combined_response += "\n\n[Follow-up]: "
                combined_response += responses['followup_answer']
            
            # Store response in Google Sheets
            success = await self.sheets_service.store_get_to_know_response(
                submission_id, combined_response
            )
            
            if success:
                # Mark as complete
                await self.sheets_service.update_step_status(
                    submission_id, 'get_to_know', True
                )
                
                # Clean up conversation state
                if telegram_user_id in self.user_conversation_states:
                    del self.user_conversation_states[telegram_user_id]
                
                return {
                    'success': True,
                    'message': self.get_to_know_questions[language]['completion_message'],
                    'completed': True,
                    'should_continue_conversation': True
                }
            else:
                return {
                    'success': False,
                    'message': self.get_to_know_questions[language]['error_saving'],
                    'error': 'storage_failed'
                }
                
        except Exception as e:
            logger.error(f"Error completing get-to-know flow: {e}")
            return {
                'success': False,
                'message': self.get_to_know_questions[state['language']]['error_saving'],
                'error': str(e)
            }
    
    def get_conversation_state(self, telegram_user_id: str) -> ConversationState:
        """Get current conversation state for a user"""
        state = self.user_conversation_states.get(telegram_user_id)
        if not state:
            return ConversationState.IDLE
        
        flow = state.get('flow')
        step = state.get('step')
        
        if flow == 'get_to_know':
            if step == 'followup_question':
                return ConversationState.GET_TO_KNOW_FOLLOWUP
            else:
                return ConversationState.GET_TO_KNOW_ACTIVE
        
        return ConversationState.IDLE
    
    def is_in_conversation(self, telegram_user_id: str) -> bool:
        """Check if user is currently in a conversation flow"""
        return telegram_user_id in self.user_conversation_states
    
    def clear_conversation_state(self, telegram_user_id: str):
        """Clear conversation state for a user"""
        if telegram_user_id in self.user_conversation_states:
            del self.user_conversation_states[telegram_user_id]
    
    def is_boring_answer(self, answer: str) -> bool:
        """
        Improved boring answer detection based on real examples
        
        Criteria for boring answers:
        1. Very short answers
        2. Strong boring indicators (immediate red flags)
        3. Many filler words without substance
        4. Lacks specific details or personality
        """
        if not answer or len(answer.strip()) < 3:
            return True
        
        answer_lower = answer.lower().strip()
        
        # Hebrew detection (contains Hebrew characters)
        has_hebrew = any('\u0590' <= char <= '\u05FF' for char in answer)
        
        # 1. Too short for meaningful content
        min_length = 30 if has_hebrew else 20
        if len(answer_lower) < min_length:
            return True
        
        # 2. Check for strong boring indicators (immediate red flags)
        strong_boring_count = 0
        for strong_indicator in self.strong_boring_indicators:
            if strong_indicator in answer_lower:
                strong_boring_count += 1
        
        # 3. Count regular filler words/phrases
        filler_count = 0
        for pattern in self.boring_patterns:
            if pattern in answer_lower:
                filler_count += 1
        
        # 4. Count good indicators
        good_indicators = 0
        for indicator in self.good_answer_indicators:
            if indicator in answer_lower:
                good_indicators += 1
        
        # Check for negative contexts that negate good indicators
        negative_context_count = 0
        for negative_context in self.negative_contexts:
            if negative_context in answer_lower:
                negative_context_count += 1
        
        # Reduce good indicators if there are negative contexts
        if negative_context_count > 0:
            good_indicators = max(0, good_indicators - negative_context_count)
        
        # 5. Calculate word count
        words = answer_lower.split()
        word_count = len(words)
        
        # Decision logic:
        
        # If strong boring indicators, check if there's enough substance to override
        if strong_boring_count > 0:
            if good_indicators >= 2 and len(answer_lower) > 50:
                return False
            else:
                return True
        
        # If good indicators present and reasonable length, probably not boring
        if good_indicators >= 2 and word_count >= 15:
            return False
        
        # If multiple filler words and no good indicators = boring
        if filler_count >= 2 and good_indicators == 0:
            return True
        
        # If short answer with filler words and no substance = boring
        if filler_count >= 1 and word_count < 25 and good_indicators == 0:
            return True
        
        # If very short and no good indicators = boring
        if word_count < 20 and good_indicators == 0:
            return True
        
        return False 