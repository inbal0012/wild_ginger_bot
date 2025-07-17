#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for the get-to-know flow functionality
Testing the interactive get-to-know conversation flow
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot_polling import (
    get_to_know_command,
    handle_get_to_know_response,
    complete_get_to_know_flow,
    store_get_to_know_response,
    is_boring_answer,
    GET_TO_KNOW_QUESTIONS,
    BORING_PATTERNS,
    user_conversation_states,
    user_submissions
)

class TestGetToKnowFlow:
    """Test the complete get-to-know flow functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear conversation states
        user_conversation_states.clear()
        user_submissions.clear()
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update object"""
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.first_name = "John"
        update.effective_user.language_code = "he"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        update.message.text = "Test response"
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context object"""
        context = Mock()
        context.args = []
        return context
    
    @pytest.fixture
    def mock_status_data(self):
        """Create mock status data"""
        return {
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'language': 'he',
            'form': True,
            'partner': True,
            'get_to_know': False,
            'approved': False,
            'paid': False,
            'group_open': False,
            'is_returning_participant': False,
            'telegram_user_id': '123456789'
        }
    
    @pytest.mark.asyncio
    async def test_get_to_know_command_start_flow(self, mock_update, mock_context, mock_status_data):
        """Test starting the get-to-know flow with /get_to_know command"""
        user_id = str(mock_update.effective_user.id)
        user_submissions[user_id] = 'SUBM_12345'
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data):
            await get_to_know_command(mock_update, mock_context)
            
            # Verify message was sent
            mock_update.message.reply_text.assert_called_once()
            sent_message = mock_update.message.reply_text.call_args[0][0]
            
            # Check that Hebrew question was asked
            assert "אשמח לשמוע עליך קצת" in sent_message
            assert "😃" in sent_message
            
            # Verify conversation state was set
            assert user_id in user_conversation_states
            state = user_conversation_states[user_id]
            assert state['flow'] == 'get_to_know'
            assert state['step'] == 'first_question'
            assert state['language'] == 'he'
            assert state['submission_id'] == 'SUBM_12345'
    
    @pytest.mark.asyncio
    async def test_get_to_know_command_already_completed(self, mock_update, mock_context, mock_status_data):
        """Test command when get-to-know is already completed"""
        user_id = str(mock_update.effective_user.id)
        user_submissions[user_id] = 'SUBM_12345'
        mock_status_data['get_to_know'] = True
        
        with patch('telegram_bot_polling.get_status_data', return_value=mock_status_data):
            await get_to_know_command(mock_update, mock_context)
            
            # Verify already completed message
            mock_update.message.reply_text.assert_called_once()
            sent_message = mock_update.message.reply_text.call_args[0][0]
            assert "כבר השלמת את חלק ההיכרות" in sent_message
    
    @pytest.mark.asyncio
    async def test_get_to_know_command_no_submission(self, mock_update, mock_context):
        """Test command when no submission is linked"""
        with patch('telegram_bot_polling.get_status_data', return_value=None):
            await get_to_know_command(mock_update, mock_context)
            
            # Verify error message
            mock_update.message.reply_text.assert_called_once()
            sent_message = mock_update.message.reply_text.call_args[0][0]
            assert "אנא קשר את ההרשמה שלך קודם" in sent_message
    
    @pytest.mark.asyncio
    async def test_handle_good_first_response(self, mock_update, mock_context):
        """Test handling a good first response (should complete flow)"""
        user_id = str(mock_update.effective_user.id)
        user_conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'first_question',
            'language': 'he',
            'submission_id': 'SUBM_12345',
            'responses': {}
        }
        
        # Mock a good response
        mock_update.message.text = "אני מפתח תוכנה, יש לי ניסיון באירועים קהילתיים, ואני אוהב לבשל"
        
        with patch('telegram_bot_polling.complete_get_to_know_flow') as mock_complete:
            await handle_get_to_know_response(mock_update, mock_context)
            
            # Verify response was stored
            assert 'first_answer' in user_conversation_states[user_id]['responses']
            
            # Verify flow completion was called
            mock_complete.assert_called_once_with(mock_update, user_id)
    
    @pytest.mark.asyncio
    async def test_handle_boring_first_response(self, mock_update, mock_context):
        """Test handling a boring first response (should ask follow-up)"""
        user_id = str(mock_update.effective_user.id)
        user_conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'first_question',
            'language': 'he',
            'submission_id': 'SUBM_12345',
            'responses': {}
        }
        
        # Mock a boring response
        mock_update.message.text = "לא יודע"
        
        await handle_get_to_know_response(mock_update, mock_context)
        
        # Verify response was stored
        assert 'first_answer' in user_conversation_states[user_id]['responses']
        
        # Verify step was advanced to follow-up
        assert user_conversation_states[user_id]['step'] == 'followup_question'
        
        # Verify follow-up question was asked
        mock_update.message.reply_text.assert_called_once()
        sent_message = mock_update.message.reply_text.call_args[0][0]
        assert "אשמח לשמוע משהו מגניב ומעניין" in sent_message
    
    @pytest.mark.asyncio
    async def test_handle_followup_response(self, mock_update, mock_context):
        """Test handling follow-up response (should complete flow)"""
        user_id = str(mock_update.effective_user.id)
        user_conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'followup_question',
            'language': 'he',
            'submission_id': 'SUBM_12345',
            'responses': {'first_answer': 'לא יודע'}
        }
        
        # Mock a better response
        mock_update.message.text = "אני יודע לנגן בגיטרה ואוהב לאפות עוגות"
        
        with patch('telegram_bot_polling.complete_get_to_know_flow') as mock_complete:
            await handle_get_to_know_response(mock_update, mock_context)
            
            # Verify response was stored
            assert 'followup_answer' in user_conversation_states[user_id]['responses']
            
            # Verify flow completion was called
            mock_complete.assert_called_once_with(mock_update, user_id)
    
    @pytest.mark.asyncio
    async def test_complete_get_to_know_flow_success(self, mock_update, mock_context):
        """Test successful completion of get-to-know flow"""
        user_id = str(mock_update.effective_user.id)
        user_conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'followup_question',
            'language': 'he',
            'submission_id': 'SUBM_12345',
            'responses': {
                'first_answer': 'לא יודע',
                'followup_answer': 'אני יודע לנגן בגיטרה ואוהב לאפות עוגות'
            }
        }
        
        mock_status_data = {
            'submission_id': 'SUBM_12345',
            'get_to_know': True,
            'language': 'he'
        }
        
        with patch('telegram_bot_polling.store_get_to_know_response', return_value=True), \
             patch('telegram_bot_polling.update_get_to_know_complete', return_value=True), \
             patch('telegram_bot_polling.get_status_data', return_value=mock_status_data), \
             patch('telegram_bot_polling.continue_conversation') as mock_continue:
            
            await complete_get_to_know_flow(mock_update, user_id)
            
            # Verify completion message was sent
            mock_update.message.reply_text.assert_called()
            sent_message = mock_update.message.reply_text.call_args[0][0]
            assert "תודה על השיתוף" in sent_message
            
            # Verify continue conversation was called
            mock_continue.assert_called_once()
            
            # Verify conversation state was cleaned up
            assert user_id not in user_conversation_states
    
    @pytest.mark.asyncio
    async def test_complete_get_to_know_flow_storage_error(self, mock_update, mock_context):
        """Test completion with storage error"""
        user_id = str(mock_update.effective_user.id)
        user_conversation_states[user_id] = {
            'flow': 'get_to_know',
            'step': 'first_question',
            'language': 'he',
            'submission_id': 'SUBM_12345',
            'responses': {'first_answer': 'Good response'}
        }
        
        with patch('telegram_bot_polling.store_get_to_know_response', return_value=False):
            await complete_get_to_know_flow(mock_update, user_id)
            
            # Verify error message was sent
            mock_update.message.reply_text.assert_called_once()
            sent_message = mock_update.message.reply_text.call_args[0][0]
            assert "שגיאה בשמירת התשובות" in sent_message
    
    def test_not_in_conversation_flow(self, mock_update, mock_context):
        """Test message handler when user is not in get-to-know flow"""
        user_id = str(mock_update.effective_user.id)
        # No conversation state set
        
        # This should be an async test but returns immediately
        result = asyncio.run(handle_get_to_know_response(mock_update, mock_context))
        
        # Should not call reply_text since user is not in flow
        mock_update.message.reply_text.assert_not_called()

class TestBoringAnswerDetection:
    """Test the boring answer detection functionality"""
    
    def test_is_boring_answer_hebrew_patterns(self):
        """Test detection of boring Hebrew patterns"""
        boring_answers = [
            "לא יודע",
            "לא יודעת", 
            "רגיל",
            "כלום",
            "אמממ",
            "לא"
        ]
        
        for answer in boring_answers:
            assert is_boring_answer(answer) == True, f"Should detect '{answer}' as boring"
    
    def test_is_boring_answer_english_patterns(self):
        """Test detection of boring English patterns"""
        boring_answers = [
            "idk",
            "i don't know",
            "regular",
            "normal",
            "nothing",
            "dunno"
        ]
        
        for answer in boring_answers:
            assert is_boring_answer(answer) == True, f"Should detect '{answer}' as boring"
    
    def test_is_boring_answer_short_answers(self):
        """Test detection of short answers"""
        short_answers = [
            "ok",
            "yes",
            "no",
            "כן",
            "לא",
            "a",
            "בסדר"
        ]
        
        for answer in short_answers:
            assert is_boring_answer(answer) == True, f"Should detect '{answer}' as boring (too short)"
    
    def test_is_boring_answer_good_answers(self):
        """Test that good answers are not detected as boring"""
        good_answers = [
            "אני מפתח תוכנה ויש לי ניסיון רב באירועים קהילתיים. אני אוהב לבשל ולנגן בגיטרה בזמני הפנוי.",
            "I'm a software developer with experience in community events. I love cooking and playing guitar in my free time.",
            "יש לי ניסיון באירועים קהילתיים ואני נגן גיטרה. אני אוהב לפגוש אנשים חדשים ולחלוק חוויות.",
            "I have experience with community events and I play guitar. I love meeting new people and sharing experiences.",
            "אני אוהב לרקוד ויש לי חתול חמוד. אני עובד בתחום החינוך ונהנה מאתגרים חדשים.",
            "I love dancing and I have a cute cat. I work in education and enjoy new challenges in creative environments."
        ]
        
        for answer in good_answers:
            assert is_boring_answer(answer) == False, f"Should not detect '{answer}' as boring"
    
    def test_is_boring_answer_empty_or_none(self):
        """Test detection of empty or None answers"""
        assert is_boring_answer("") == True
        assert is_boring_answer("   ") == True
        assert is_boring_answer(None) == True

class TestGetToKnowQuestions:
    """Test the get-to-know questions data structure"""
    
    def test_hebrew_questions_exist(self):
        """Test that Hebrew questions are properly defined"""
        assert 'he' in GET_TO_KNOW_QUESTIONS
        he_questions = GET_TO_KNOW_QUESTIONS['he']
        
        assert 'first_question' in he_questions
        assert 'followup_question' in he_questions
        assert 'completion_message' in he_questions
        assert 'already_completed' in he_questions
        assert 'no_registration' in he_questions
    
    def test_english_questions_exist(self):
        """Test that English questions are properly defined"""
        assert 'en' in GET_TO_KNOW_QUESTIONS
        en_questions = GET_TO_KNOW_QUESTIONS['en']
        
        assert 'first_question' in en_questions
        assert 'followup_question' in en_questions
        assert 'completion_message' in en_questions
        assert 'already_completed' in en_questions
        assert 'no_registration' in en_questions
    
    def test_questions_content(self):
        """Test that questions contain expected content"""
        he_questions = GET_TO_KNOW_QUESTIONS['he']
        
        assert "אשמח לשמוע עליך קצת" in he_questions['first_question']
        assert "😃" in he_questions['first_question']
        assert "אשמח לשמוע משהו מגניב ומעניין" in he_questions['followup_question']
        assert "לא חובה" in he_questions['followup_question']
        assert "תודה על השיתוף" in he_questions['completion_message']

class TestGoogleSheetsIntegration:
    """Test Google Sheets integration for get-to-know responses"""
    
    def test_store_get_to_know_response_no_sheets_service(self):
        """Test storage when Google Sheets service is not available"""
        with patch('telegram_bot_polling.sheets_service', None):
            result = store_get_to_know_response('SUBM_12345', 'Test response')
            assert result == False
    
    def test_store_get_to_know_response_success(self):
        """Test successful storage of get-to-know response"""
        mock_sheet_data = {
            'headers': ['Submission ID', 'Get To Know Response'],
            'rows': [['SUBM_12345', '']]
        }
        
        mock_sheets_service = Mock()
        mock_sheets_service.spreadsheets().values().update().execute.return_value = {}
        
        with patch('telegram_bot_polling.sheets_service', mock_sheets_service), \
             patch('telegram_bot_polling.get_sheet_data', return_value=mock_sheet_data), \
             patch('telegram_bot_polling.get_column_indices') as mock_get_indices, \
             patch('telegram_bot_polling.column_index_to_letter', return_value='B'):
            
            mock_get_indices.return_value = {'submission_id': 0}
            
            result = store_get_to_know_response('SUBM_12345', 'Test response')
            assert result == True

class TestEnglishFlow:
    """Test get-to-know flow with English language"""
    
    def test_english_user_flow(self):
        """Test complete flow for English user"""
        # Mock English user status
        status_data = {
            'submission_id': 'SUBM_12345',
            'language': 'en',
            'get_to_know': False
        }
        
        # Test first question in English
        first_question = GET_TO_KNOW_QUESTIONS['en']['first_question']
        assert 'I\'d love to hear about you' in first_question
        assert 'experience with these types of events' in first_question
        
        # Test followup question in English
        followup_question = GET_TO_KNOW_QUESTIONS['en']['followup_question']
        assert 'something cool and interesting' in followup_question
        assert 'alternative world' in followup_question


class TestRealExamplesValidation:
    """Test the improved boring answer detection against real examples from get-to-know examples.txt"""
    
    def test_bad_answers_detected_correctly(self):
        """Test that real bad answers are correctly identified as boring"""
        # Real bad answers from the examples file
        bad_answers = [
            "אמממ אני בת 22 מכפר סבא, סטודנטית , הניסיון שלי הוא לא גדול אבל הייתי בכמה פליים , יצא לי גם להשתתף בחלקם , והאמת שאין לי מושג למשהו מגניב חחח",
            "מעצב תאורה בהופעות ומסיבות \nההיתי בכמה פליי לא יותר מידי \nמידי פעם יוצא לדאנגן ולוציפר וכאלה",
            "היי ענבל, כיף להכיר! \nאז טלי, בת 39 (תיכף 40 🥴)\nאני רווקה, בדסמית (סוויץ), ביסית, אנרכי-פולי במערכות יחסים משניות, ברנרית וחברת קאמפ בפרילאב, ככה שיודעת להחזיק מרחב בכללי והעברתי כמה סדנאות הסכמה",
            "היי.\nאני אייל.\nנראה לי שהכרנו פעם בטירה.\nנסיון מועט, יצא לי להיות בכמה כרבוליות יחסית קטנות אצל רעות אמסטרדמסקי.\nמשהו מגניב: {תמונה של כלב}",
            "אני נועם, טרנסית ביסית פוליאמורית בת 32 (בייבי בהכל ☺️)\n\nאין לי ניסיון באירועי כרבוליות, יש לי ניסיון בסרטים של מונטי פייתון (:"
        ]
        
        for bad_answer in bad_answers:
            assert is_boring_answer(bad_answer), f"Failed to detect boring answer: {bad_answer[:50]}..."
    
    def test_good_answers_not_detected_as_boring(self):
        """Test that real good answers are correctly identified as not boring"""
        # Real good answers from the examples file
        good_answers = [
            "אני מבלה לי באזעקות פעם-פעמיים בשבוע\nבסצינה on and off כמה שנים\nבשותפות מסוימת עם גל ב. שהייתה אצלך בשישי 😊\nמנגן גיטרה, קלידים, שר\nבן 41, גר ברמת גן, רווק\nהטרו-גמיש עם יצר מין חזק מאוד ואנרגיות מטורפות. עובד בהייטק, ידידותי וחייכן ושובב.\nיש לי פנטזיות מפה ועד הודעה חדשה, וגם את האומץ לממש אותן, אני מקווה :-p",
            "הי ענבל נעים מאוד😊\nקצת על עצמי.... בת 47 אוהבת תנועה מגע ולרקוד, מתה על כירבולים ונעימים,\nלטייל בטבע ולצחוק משטויות.\n\n יצא לי להיות בכל מיני אירועים מהסוג הזה בפסטיבלים ובמפגשים קטנים.\n\nמגניב על עצמי \nאני מאמנת טאקוונדו( לא יודעת אם מגניב אבל לא שיגרתי....)",
            "קצת עלי.. בת 34 מחיפה, מחפשת עבודה בתחום חינוך או שיקום, והתחלתי השנה ללמוד פסיכותרפיה.\nמבחינת הגדרות, אני ג'נדרקוויר (לשון פנייה מעורבת), פאנסקסואל.ית בדסמית (סוויצ'ית). לאחרונה התחלתי גם ללמוד לקשור שיבארי ונכנסתי לזה בכל הכח 😊\nהייתי במלא פסטיבלים וסדנאות מכל הסוגים, כמשתתף וכהלפר, וגם בסיבות כרבולים, וגם אני לעיתים מנחה מסיבות כרבולים. בהכשרה שלי בין היתר אני גם מנחת קבוצות למיניות בריאה\nמשהו מגניב עלי.. אני מאוד אוהב שפות. ברמה זו או אחרת יש לי הכרות עם 7 שפות, ולמדתי בלשנות. עוד טייטל שיש לי זה שאני מתורגמנית לשפת הסימנים הישראלית\nעוד שאלות? :)",
            "היי ענבל, נעים מאוד אני אורן :), בן 48, אוהב בירות ושאכטות, נשוי + זוגיות משנית, אוהב לטייל. בא במקור מהעולם של אושו עם נסיון בכל מיני מסיבות כרבולים למינהן, קורסים סדנאות וכו'. והאמת קצת מוזר לי לדבר על עצמי\nבתור משהו מגניב אני מניח שהייתי מציין את האהבה שלי לחופש ולטבע. אני מבקר באזור מסויים בים המלח על בסיס קבוע, שם יש לי נביעה כמעט פרטית ובה אני אוהב לטבול, להתהלך בעירום, לפעמים להכיר אנשים ובעיקר להיות עם עצמי או עם מי שמצטרף אלי\nאהה, ועוד משהו, מאוד אוהב את מונטי פייטון (אם כי לא כל כך הבנתי את הקשר של מונטי פייטון לאירוע)"
        ]
        
        for good_answer in good_answers:
            assert not is_boring_answer(good_answer), f"Incorrectly detected good answer as boring: {good_answer[:50]}..."
    
    def test_good_followup_responses(self):
        """Test that good followup responses are not detected as boring"""
        # Real good followup responses from the examples file
        good_followups = [
            "אמממ אני מאוד אוהבת אקסטרים 😅 עשיתי צניחה חופשית כמה פעמים וכאלה",
            "כן אני אוהב קוקטיילים ויודע להכין כמה מושלמים\nבקטע של להכין תרכיזים וכאלה\nמאפס",
            "אני אגרונומית \nאהה פגשתי את לאונרד כהן!\nטיפסתי את הקילימנג'רו",
            "אני מאוד עצלן.\nכל כך עצלן שבניתי שלט ששולט על כל הסלון (טלוויזיה, מזגן, תאורה...) והוא מתוכנן כך שאוכל לתפעל אותו מהספה בלי לקום, אפילו עם הרגליים.",
            "יצאתי בעיקר לפולי-פיקניקים, ופעם אחת לאמונו באורוות בפרדס חנה.\nלא יצא לי לצאת לאירועי bdsm (או פליי פארטיז), אבל יום אחרי הכרבוליה אני מתכננת לצאת לערב טעימות שיבארי (:"
        ]
        
        for good_followup in good_followups:
            assert not is_boring_answer(good_followup), f"Incorrectly detected good followup as boring: {good_followup[:50]}..."
    
    def test_edge_cases_from_examples(self):
        """Test edge cases and boundary conditions from real examples"""
        # Very short answers that should be boring
        short_boring = [
            "בת 22",
            "סטודנטית",
            "אמממ",
            "לא יודע"
        ]
        
        for short_answer in short_boring:
            assert is_boring_answer(short_answer), f"Failed to detect short boring answer: {short_answer}"
        
        # Answers with demographic info but no personality (should be boring)
        demographic_only = [
            "בת 22 מכפר סבא",
            "בן 30 גר בתל אביב",
            "רווקה סטודנטית"
        ]
        
        for demo_answer in demographic_only:
            assert is_boring_answer(demo_answer), f"Failed to detect demographic-only answer as boring: {demo_answer}"

    def test_partner_completion_detection(self):
        """Test that partner completion is automatically detected and updated"""
        # Mock data for a user with partner
        row = [
            'SUBM_12345',  # submission_id
            'דני לוי',     # full_name
            'באיזון',      # coming_alone_or_balance
            'אלעד ויסברוד',  # partner_name
            'TRUE',        # form_complete
            'FALSE',       # partner_complete (starts as FALSE)
            'FALSE',       # get_to_know_complete
            'FALSE',       # admin_approved
            'FALSE',       # payment_complete
            'FALSE',       # group_access
            '123456789',   # telegram_user_id
        ]
        
        column_indices = {
            'submission_id': 0,
            'full_name': 1,
            'coming_alone_or_balance': 2,
            'partner_name': 3,
            'form_complete': 4,
            'partner_complete': 5,
            'get_to_know_complete': 6,
            'admin_approved': 7,
            'payment_complete': 8,
            'group_access': 9,
            'telegram_user_id': 10,
        }
        
        # Mock the partner status check to return that all partners are registered
        mock_partner_status = {
            'all_registered': True,
            'registered_partners': ['אלעד ויסברוד'],
            'missing_partners': []
        }
        
        with patch('telegram_bot_polling.parse_multiple_partners', return_value=['אלעד ויסברוד']), \
             patch('telegram_bot_polling.check_partner_registration_status', return_value=mock_partner_status), \
             patch('telegram_bot_polling.update_partner_complete', return_value=True) as mock_update:
            
            from telegram_bot_polling import parse_submission_row
            
            result = parse_submission_row(row, column_indices)
            
            # Verify that update_partner_complete was called
            mock_update.assert_called_once_with('SUBM_12345', True)
            
            # Verify that the local partner status was updated
            assert result['partner'] == True
            assert result['partner_status']['all_registered'] == True
            assert result['partner_status']['missing_partners'] == []
            
    def test_no_partner_update_when_already_complete(self):
        """Test that partner status is not checked when already complete"""
        # Mock data for a user with partner already complete
        row = [
            'SUBM_12345',  # submission_id
            'דני לוי',     # full_name
            'באיזון',      # coming_alone_or_balance
            'אלעד ויסברוד',  # partner_name
            'TRUE',        # form_complete
            'TRUE',        # partner_complete (already TRUE)
            'FALSE',       # get_to_know_complete
            'FALSE',       # admin_approved
            'FALSE',       # payment_complete
            'FALSE',       # group_access
            '123456789',   # telegram_user_id
        ]
        
        column_indices = {
            'submission_id': 0,
            'full_name': 1,
            'coming_alone_or_balance': 2,
            'partner_name': 3,
            'form_complete': 4,
            'partner_complete': 5,
            'get_to_know_complete': 6,
            'admin_approved': 7,
            'payment_complete': 8,
            'group_access': 9,
            'telegram_user_id': 10,
        }
        
        with patch('telegram_bot_polling.parse_multiple_partners') as mock_parse, \
             patch('telegram_bot_polling.check_partner_registration_status') as mock_check, \
             patch('telegram_bot_polling.update_partner_complete') as mock_update:
            
            from telegram_bot_polling import parse_submission_row
            
            result = parse_submission_row(row, column_indices)
            
            # Verify that expensive operations were not called
            mock_parse.assert_not_called()
            mock_check.assert_not_called()
            mock_update.assert_not_called()
            
            # Verify that partner status is already marked as complete
            assert result['partner'] == True
            assert result['partner_names'] == ['אלעד ויסברוד']  # Just the raw name


if __name__ == '__main__':
    print("🧪 Running get-to-know flow tests...")
    
    # Run tests manually for debugging
    async def run_manual_tests():
        """Run some tests manually for debugging"""
        print("\n📋 Testing boring answer detection...")
        
        # Test boring answer detection
        boring_detector = TestBoringAnswerDetection()
        boring_detector.test_is_boring_answer_hebrew_patterns()
        boring_detector.test_is_boring_answer_english_patterns()
        boring_detector.test_is_boring_answer_short_answers()
        boring_detector.test_is_boring_answer_good_answers()
        boring_detector.test_is_boring_answer_empty_or_none()
        print("✅ Boring answer detection tests passed")
        
        print("\n📋 Testing questions structure...")
        questions_test = TestGetToKnowQuestions()
        questions_test.test_hebrew_questions_exist()
        questions_test.test_english_questions_exist()
        questions_test.test_questions_content()
        print("✅ Questions structure tests passed")
        
        print("\n📋 Testing flow initialization...")
        flow_test = TestGetToKnowFlow()
        flow_test.setup_method()
        
        # Mock objects
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        
        context = Mock()
        status_data = {
            'submission_id': 'SUBM_12345',
            'alias': 'John Doe',
            'language': 'he',
            'get_to_know': False,
            'is_returning_participant': False,
            'telegram_user_id': '123456789'
        }
        
        user_submissions['123456789'] = 'SUBM_12345'
        
        with patch('telegram_bot_polling.get_status_data', return_value=status_data):
            await flow_test.test_get_to_know_command_start_flow(update, context, status_data)
        
        print("✅ Flow initialization test passed")
        
        print("\n🎉 All manual tests passed!")
    
    # Run the manual tests
    asyncio.run(run_manual_tests()) 