import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.form_flow_service import FormFlowService
from telegram_bot.models.form_flow import QuestionDefinition, QuestionType, QuestionOption, Text
from telegram_bot.models.registration import RegistrationStatus


class TestFormFlowScenarios:
    """Test suite for form flow scenarios with different event types and user types"""
    
    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock SheetsService"""
        sheets_service = Mock()
        sheets_service.headers = {
            "Users": {
                "telegram_user_id": 0,
                "telegram": 1,
                "full_name": 2,
                "language": 3,
                "relevant_experience": 4,
                "is_returning_participant": 5
            },
            "Registrations": {
                "registration_id": 0,
                "user_id": 1,
                "event_id": 2,
                "status": 3,
                "form_complete": 34,
                "get_to_know_complete": 35
            },
            "Events": {
                "id": 0,
                "name": 1,
                "event_type": 4,
                "status": 9
            }
        }
        # Configure side_effect to return different data for different sheet calls
        def get_data_side_effect(sheet_name):
            if sheet_name == "Events":
                return {
                    'headers': ['id', 'name', 'event_type', 'status', 'date', 'created_at'],
                    'rows': [
                        ['bdsm1', 'BDSM Safety Workshop', 'bdsm_workshop', 'active', '2024-01-01', '2024-01-01']
                    ]
                }
            elif sheet_name == "Users":
                return {
                    'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
                    'rows': []
                }
            else:
                return {
                    'headers': ['registration_id', 'user_id', 'event_id', 'status', 'form_complete', 'get_to_know_complete'],
                    'rows': []
                }
        
        sheets_service.get_data_from_sheet.side_effect = get_data_side_effect
        return sheets_service
    
    @pytest.fixture
    def form_flow_service(self, mock_sheets_service):
        """Create a FormFlowService instance"""
        # Mock the parse_upcoming_events method to avoid initialization issues
        with patch.object(FormFlowService, 'parse_upcoming_events', return_value=[]):
            return FormFlowService(mock_sheets_service)
    
    @pytest.fixture
    def mock_telegram_bot(self):
        """Create a mock Telegram bot"""
        bot = Mock()
        bot.send_message = AsyncMock()
        bot.send_poll = AsyncMock()
        return bot
    
    def setup_form_flow_service(self, form_flow_service, mock_telegram_bot):
        """Setup form flow service with mock bot"""
        form_flow_service.set_telegram_bot(mock_telegram_bot)
        return form_flow_service
    
    # ===== NEW USER SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_new_user_bdsm_workshop_form_flow(self, form_flow_service, mock_telegram_bot):
        """Test form flow for new user registering for BDSM workshop"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - new user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data - BDSM workshop
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['bdsm1', 'BDSM Safety Workshop', 'bdsm_workshop', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions for BDSM workshop
        bdsm_questions = [
            QuestionDefinition(
                question_id="bdsm_experience",
                title=Text(en="What is your BDSM experience level?", he="מה רמת הניסיון שלך ב-BDSM?"),
                question_type=QuestionType.SELECT,
                required=True,
                save_to="registration_data",
                options=[
                    QuestionOption(value="beginner", text=Text(en="Beginner", he="מתחיל")),
                    QuestionOption(value="intermediate", text=Text(en="Intermediate", he="בינוני")),
                    QuestionOption(value="experienced", text=Text(en="Experienced", he="מנוסה"))
                ]
            ),
            QuestionDefinition(
                question_id="bdsm_declaration",
                title=Text(en="Do you understand BDSM safety principles?", he="האם אתה מבין עקרונות בטיחות BDSM?"),
                question_type=QuestionType.BOOLEAN,
                required=True,
                save_to="registration_data"
            )
        ]
        
        # Mock the form flow to return BDSM-specific questions
        form_flow_service.get_form_questions = Mock(return_value=bdsm_questions)
        
        # Start form flow
        first_question = await form_flow_service.start_form("newuser123", language="en")
        
        assert first_question is not None
        assert first_question.question_id == "language"
        assert "language" in first_question.title.en.lower()
    
    @pytest.mark.asyncio
    async def test_new_user_cuddle_party_form_flow(self, form_flow_service, mock_telegram_bot):
        """Test form flow for new user registering for cuddle party"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - new user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data - cuddle party
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['cuddle1', 'Cozy Cuddle Party', 'cuddle_party', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions for cuddle party
        cuddle_questions = [
            QuestionDefinition(
                question_id="cuddle_comfort",
                title=Text(en="How comfortable are you with physical touch?", he="כמה נוח לך עם מגע פיזי?"),
                question_type=QuestionType.SELECT,
                required=True,
                save_to="registration_data",
                options=[
                    QuestionOption(value="very_comfortable", text=Text(en="Very comfortable", he="נוח מאוד")),
                    QuestionOption(value="somewhat_comfortable", text=Text(en="Somewhat comfortable", he="נוח במידה מסוימת")),
                    QuestionOption(value="nervous", text=Text(en="Nervous but willing", he="עצבני אבל מוכן"))
                ]
            ),
            QuestionDefinition(
                question_id="boundaries",
                title=Text(en="Do you understand the importance of respecting boundaries?", he="האם אתה מבין את חשיבות כיבוד הגבולות?"),
                question_type=QuestionType.BOOLEAN,
                required=True,
                save_to="registration_data"
            )
        ]
        
        # Mock the form flow to return cuddle-specific questions
        form_flow_service.get_form_questions = Mock(return_value=cuddle_questions)
        
        # Start form flow
        first_question = await form_flow_service.start_form("newuser123", language="en")
        
        assert first_question is not None
        assert first_question.question_id == "language"
        assert "language" in first_question.title.en.lower()
    
    @pytest.mark.asyncio
    async def test_new_user_sexual_party_form_flow(self, form_flow_service, mock_telegram_bot):
        """Test form flow for new user registering for sexual party"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - new user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data - sexual party
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['sexual1', 'Intimate Play Party', 'sexual_party', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions for sexual party
        sexual_questions = [
            QuestionDefinition(
                question_id="sti_test",
                title=Text(en="When was your last STI test?", he="מתי הבדיקה האחרונה שלך למחלות מין?"),
                question_type=QuestionType.DATE,
                required=True,
                save_to="registration_data"
            ),
            QuestionDefinition(
                question_id="consent_understanding",
                title=Text(en="Do you understand enthusiastic consent?", he="האם אתה מבין הסכמה נלהבת?"),
                question_type=QuestionType.BOOLEAN,
                required=True,
                save_to="registration_data"
            ),
            QuestionDefinition(
                question_id="safe_sex_practices",
                title=Text(en="Are you familiar with safe sex practices?", he="האם אתה מכיר פרקטיקות סקס בטוח?"),
                question_type=QuestionType.BOOLEAN,
                required=True,
                save_to="registration_data"
            )
        ]
        
        # Mock the form flow to return sexual-specific questions
        form_flow_service.get_form_questions = Mock(return_value=sexual_questions)
        
        # Start form flow
        first_question = await form_flow_service.start_form("newuser123", language="en")
        
        assert first_question is not None
        assert first_question.question_id == "language"
        assert "language" in first_question.title.en.lower()
    
    # ===== RETURNING USER SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_returning_user_bdsm_workshop_form_flow(self, form_flow_service, mock_telegram_bot):
        """Test form flow for returning user registering for BDSM workshop"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - returning user with BDSM experience
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['returning123', '@returninguser', 'Returning User', 'en', '{"bdsm_workshop": "experienced"}', 'true']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data - BDSM workshop
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['bdsm1', 'Advanced BDSM Workshop', 'bdsm_workshop', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions for returning BDSM user
        returning_bdsm_questions = [
            QuestionDefinition(
                question_id="advanced_techniques",
                title=Text(en="Which advanced BDSM techniques interest you?", he="אילו טכניקות BDSM מתקדמות מעניינות אותך?"),
                question_type=QuestionType.MULTI_SELECT,
                required=False,
                save_to="registration_data",
                options=[
                    QuestionOption(value="rope_bondage", text=Text(en="Rope Bondage", he="קשירת חבלים")),
                    QuestionOption(value="impact_play", text=Text(en="Impact Play", he="משחק מכות")),
                    QuestionOption(value="sensory_deprivation", text=Text(en="Sensory Deprivation", he="מניעת חושים"))
                ]
            ),
            QuestionDefinition(
                question_id="teaching_assistance",
                title=Text(en="Would you be willing to assist in teaching beginners?", he="האם תהיה מוכן לעזור בהוראת מתחילים?"),
                question_type=QuestionType.BOOLEAN,
                required=False,
                save_to="registration_data"
            )
        ]
        
        # Mock the form flow to return returning user questions
        form_flow_service.get_form_questions = Mock(return_value=returning_bdsm_questions)
        
        # Start form flow
        first_question = await form_flow_service.start_form("returning123", language="en")
        
        assert first_question is not None
        assert first_question.question_id == "language"
        assert "language" in first_question.title.en.lower()
    
    @pytest.mark.asyncio
    async def test_returning_user_different_event_type_form_flow(self, form_flow_service, mock_telegram_bot):
        """Test form flow for returning user registering for different event type"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - returning user with BDSM experience but no cuddle experience
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['returning123', '@returninguser', 'Returning User', 'en', '{"bdsm_workshop": "experienced"}', 'true']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data - cuddle party (different from their experience)
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['cuddle1', 'Cozy Cuddle Party', 'cuddle_party', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions for returning user trying new event type
        new_event_questions = [
            QuestionDefinition(
                question_id="new_event_comfort",
                title=Text(en="How do you feel about trying a new type of event?", he="איך אתה מרגיש לגבי ניסיון סוג אירוע חדש?"),
                question_type=QuestionType.SELECT,
                required=True,
                save_to="registration_data",
                options=[
                    QuestionOption(value="excited", text=Text(en="Excited", he="נרגש")),
                    QuestionOption(value="nervous", text=Text(en="Nervous", he="עצבני")),
                    QuestionOption(value="curious", text=Text(en="Curious", he="סקרן"))
                ]
            ),
            QuestionDefinition(
                question_id="experience_transfer",
                title=Text(en="Do you think your BDSM experience will help with cuddling?", he="האם אתה חושב שניסיון ה-BDSM שלך יעזור עם חיבוקים?"),
                question_type=QuestionType.BOOLEAN,
                required=False,
                save_to="registration_data"
            )
        ]
        
        # Mock the form flow to return new event type questions
        form_flow_service.get_form_questions = Mock(return_value=new_event_questions)
        
        # Start form flow
        first_question = await form_flow_service.start_form("returning123", language="en")
        
        assert first_question is not None
        assert first_question.question_id == "language"
        assert "language" in first_question.title.en.lower()
    
    # ===== FORM COMPLETION SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_new_user_form_completion_flow(self, form_flow_service, mock_telegram_bot):
        """Test complete form flow for new user"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - new user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event1', 'Test Event', 'bdsm_workshop', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions
        questions = [
            QuestionDefinition(
                question_id="name",
                title=Text(en="What is your name?", he="מה השם שלך?"),
                question_type=QuestionType.TEXT,
                required=True,
                save_to="registration_data"
            ),
            QuestionDefinition(
                question_id="experience",
                title=Text(en="What is your experience level?", he="מה רמת הניסיון שלך?"),
                question_type=QuestionType.SELECT,
                required=True,
                save_to="registration_data",
                options=[
                    QuestionOption(value="beginner", text=Text(en="Beginner", he="מתחיל")),
                    QuestionOption(value="intermediate", text=Text(en="Intermediate", he="בינוני")),
                    QuestionOption(value="experienced", text=Text(en="Experienced", he="מנוסה"))
                ]
            )
        ]
        
        form_flow_service.get_form_questions = Mock(return_value=questions)
        form_flow_service.save_answer = AsyncMock(return_value=True)
        form_flow_service.update_registration_status = AsyncMock(return_value=True)
        
        # Start form
        first_question = await form_flow_service.start_form("newuser123", language="en")
        assert first_question.question_id == "language"
        
        # Test that form flow service has the necessary methods
        assert hasattr(form_flow_service, 'handle_poll_answer'), "Should have handle_poll_answer method"
        assert hasattr(form_flow_service, 'question_definitions'), "Should have question definitions"
        
        # Test that the form flow service is properly initialized
        assert form_flow_service.question_definitions is not None, "Should have question definitions"
    
    @pytest.mark.asyncio
    async def test_returning_user_form_completion_flow(self, form_flow_service, mock_telegram_bot):
        """Test complete form flow for returning user"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data - returning user
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['returning123', '@returninguser', 'Returning User', 'en', '{"bdsm_workshop": "experienced"}', 'true']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event1', 'Advanced BDSM Workshop', 'bdsm_workshop', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions for returning user
        questions = [
            QuestionDefinition(
                question_id="advanced_interest",
                title=Text(en="What advanced topics interest you?", he="אילו נושאים מתקדמים מעניינים אותך?"),
                question_type=QuestionType.MULTI_SELECT,
                required=True,
                save_to="registration_data",
                options=[
                    QuestionOption(value="rope", text=Text(en="Rope Work", he="עבודת חבלים")),
                    QuestionOption(value="impact", text=Text(en="Impact Play", he="משחק מכות")),
                    QuestionOption(value="sensory", text=Text(en="Sensory Play", he="משחק חושים"))
                ]
            )
        ]
        
        form_flow_service.get_form_questions = Mock(return_value=questions)
        form_flow_service.save_answer = AsyncMock(return_value=True)
        form_flow_service.update_registration_status = AsyncMock(return_value=True)
        
        # Start form
        first_question = await form_flow_service.start_form("returning123", language="en")
        assert first_question.question_id == "language"
        
        # Test that form flow service has the necessary methods
        assert hasattr(form_flow_service, 'handle_poll_answer'), "Should have handle_poll_answer method"
        assert hasattr(form_flow_service, 'question_definitions'), "Should have question definitions"
        
        # Test that the form flow service is properly initialized
        assert form_flow_service.question_definitions is not None, "Should have question definitions"
    
    # ===== LANGUAGE SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_hebrew_language_form_flow(self, form_flow_service, mock_telegram_bot):
        """Test form flow in Hebrew language"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event1', 'סדנת BDSM', 'bdsm_workshop', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions with Hebrew
        questions = [
            QuestionDefinition(
                question_id="experience",
                title=Text(en="What is your experience level?", he="מה רמת הניסיון שלך?"),
                question_type=QuestionType.SELECT,
                required=True,
                save_to="registration_data",
                options=[
                    QuestionOption(value="beginner", text=Text(en="Beginner", he="מתחיל")),
                    QuestionOption(value="experienced", text=Text(en="Experienced", he="מנוסה"))
                ]
            )
        ]
        
        form_flow_service.get_form_questions = Mock(return_value=questions)
        
        # Start form in Hebrew
        first_question = await form_flow_service.start_form("user123", language="he")
        
        assert first_question is not None
        assert "שפה" in first_question.title.he
        assert first_question.options[0].text.he == "עברית"
        assert first_question.options[1].text.he == "English"
    
    # ===== ERROR SCENARIOS =====
    
    @pytest.mark.asyncio
    async def test_form_flow_user_not_found(self, form_flow_service, mock_telegram_bot):
        """Test form flow when user is not found"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock no user data
        form_flow_service.sheets_service.get_data_from_sheet.return_value = None
        
        # Try to start form
        result = await form_flow_service.start_form("nonexistent123", language="en")
        
        # Should still return language question (form always starts with language)
        assert result is not None
        assert result.question_id == "language"
    
    @pytest.mark.asyncio
    async def test_form_flow_event_not_found(self, form_flow_service, mock_telegram_bot):
        """Test form flow when event is not found"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data but no event data
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': [
                ['user123', '@user', 'Test User', 'en', '{}', 'false']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, None]
        
        # Try to start form
        result = await form_flow_service.start_form("user123", language="en")
        
        # Should still return language question (form always starts with language)
        assert result is not None
        assert result.question_id == "language"
    
    @pytest.mark.asyncio
    async def test_form_flow_invalid_language(self, form_flow_service, mock_telegram_bot):
        """Test form flow with invalid language (should fallback to English)"""
        form_flow_service = self.setup_form_flow_service(form_flow_service, mock_telegram_bot)
        
        # Mock user data
        user_data = {
            'headers': ['telegram_user_id', 'telegram', 'full_name', 'language', 'relevant_experience', 'is_returning_participant'],
            'rows': []
        }
        form_flow_service.sheets_service.get_data_from_sheet.return_value = user_data
        
        # Mock event data
        event_data = {
            'headers': ['id', 'name', 'event_type', 'status'],
            'rows': [
                ['event1', 'Test Event', 'bdsm_workshop', 'active']
            ]
        }
        form_flow_service.sheets_service.get_data_from_sheet.side_effect = [user_data, event_data]
        
        # Mock form questions
        questions = [
            QuestionDefinition(
                question_id="test",
                title=Text(en="Test question", he="שאלה לבדיקה"),
                question_type=QuestionType.TEXT,
                required=True,
                save_to="registration_data"
            )
        ]
        
        form_flow_service.get_form_questions = Mock(return_value=questions)
        
        # Start form with invalid language
        first_question = await form_flow_service.start_form("user123", language="invalid")
        
        assert first_question is not None
        # Should fallback to English
        assert "language" in first_question.title.en.lower() 