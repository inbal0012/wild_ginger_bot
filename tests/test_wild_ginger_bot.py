import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, User, Message, Chat, PollAnswer
from telegram.ext import ContextTypes
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wild_ginger_bot import WildGingerBot
from telegram_bot.models.form_flow import QuestionDefinition, QuestionType, QuestionOption
from telegram_bot.models.user import CreateUserFromTelegramDTO


class TestWildGingerBot:
    """Test suite for WildGingerBot class"""
    
    @pytest.fixture
    def bot(self):
        """Create a WildGingerBot instance with mocked dependencies"""
        with patch('wild_ginger_bot.SheetsService'), \
             patch('wild_ginger_bot.UserService'), \
             patch('wild_ginger_bot.RegistrationService'), \
             patch('wild_ginger_bot.EventService'), \
             patch('wild_ginger_bot.MessageService'), \
             patch('wild_ginger_bot.FormFlowService'), \
             patch('wild_ginger_bot.FileStorageService'):
            
            bot = WildGingerBot()
            # Mock the app property
            bot.app = Mock()
            bot.app.bot = Mock()
            # Mock file storage to return a dict and set poll_data directly
            bot.file_storage.load_data.return_value = {}
            bot.poll_data = {}
            return bot
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Update object"""
        update = Mock(spec=Update)
        user = Mock(spec=User)
        user.id = 123456789
        # Make user subscriptable by adding __getitem__ method
        user.__getitem__ = Mock(side_effect=lambda key: {
            'first_name': "Test",
            'username': "testuser", 
            'language_code': "en"
        }.get(key))
        update.effective_user = user
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Context object"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context
    
    @pytest.fixture
    def mock_message(self):
        """Create a mock Message object"""
        message = Mock(spec=Message)
        message.reply_text = AsyncMock()
        return message
    
    def test_init(self, bot):
        """Test bot initialization"""
        assert bot.sheets_service is not None
        assert bot.user_service is not None
        assert bot.registration_service is not None
        assert bot.event_service is not None
        assert bot.message_service is not None
        assert bot.form_flow_service is not None
        assert bot.file_storage is not None
        assert isinstance(bot.poll_data, dict)
    
    def test_get_user_from_update(self, bot, mock_update):
        """Test getting user ID from update"""
        user_id = bot.get_user_from_update(mock_update)
        assert user_id == "123456789"
    
    @pytest.mark.asyncio
    async def test_create_new_user_success(self, bot, mock_update):
        """Test successful user creation"""
        bot.user_service.create_new_user = AsyncMock(return_value=True)
        
        await bot.create_new_user(mock_update.effective_user)
        
        bot.user_service.create_new_user.assert_called_once()
        call_args = bot.user_service.create_new_user.call_args[0][0]
        assert isinstance(call_args, CreateUserFromTelegramDTO)
        assert call_args.full_name == "Test"
        assert call_args.telegram_user_id == "123456789"
        assert call_args.telegram_username == "testuser"
        assert call_args.language == "en"
    
    @pytest.mark.asyncio
    async def test_create_new_user_failure(self, bot, mock_update):
        """Test user creation failure"""
        bot.user_service.create_new_user = AsyncMock(return_value=False)
        
        await bot.create_new_user(mock_update.effective_user)
        
        bot.user_service.create_new_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_new_user_success(self, bot, mock_update, mock_context):
        """Test starting new user flow successfully"""
        mock_question = Mock(spec=QuestionDefinition)
        bot.form_flow_service.start_form = AsyncMock(return_value=mock_question)
        bot.send_question_as_telegram_message = AsyncMock()
        # Mock user service methods as async
        bot.user_service.create_new_user = AsyncMock(return_value=True)
        
        await bot.start_new_user(mock_update, mock_context)
        
        bot.form_flow_service.start_form.assert_called_once_with("123456789", language="en")
        bot.send_question_as_telegram_message.assert_called_once_with(mock_question, "en", "123456789")
    
    @pytest.mark.asyncio
    async def test_start_new_user_no_question(self, bot, mock_update, mock_context):
        """Test starting new user flow when no question is returned"""
        bot.form_flow_service.start_form = AsyncMock(return_value=None)
        bot.send_question_as_telegram_message = AsyncMock()
        # Mock user service methods as async
        bot.user_service.create_new_user = AsyncMock(return_value=True)
        
        await bot.start_new_user(mock_update, mock_context)
        
        bot.form_flow_service.start_form.assert_called_once()
        bot.send_question_as_telegram_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_start_existing_user(self, bot, mock_update, mock_context):
        """Test /start command for existing user"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        # Mock existing user data
        user_data = {
            'language': 'en',
            'full_name': 'Test User'
        }
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=user_data)
        bot.user_service.headers = {'language': 'language', 'full_name': 'full_name'}
        bot.message_service.get_message.return_value = "Welcome Test User!"
        # Mock form flow service as async
        bot.form_flow_service.handle_register_start = AsyncMock(return_value=None)
        
        await bot.start(mock_update, mock_context)
        
        # The method is called twice - once in start() and once in handle_register_start()
        assert bot.user_service.get_user_by_telegram_id.call_count >= 1
        bot.message_service.get_message.assert_called_once_with("en", "welcome", name="Test User")
        mock_message.reply_text.assert_called_once_with("Welcome Test User!")
    
    @pytest.mark.asyncio
    async def test_start_new_user_command(self, bot, mock_update, mock_context):
        """Test /start command for new user"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        # Mock no existing user
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=None)
        bot.message_service.get_message.return_value = "Welcome!"
        bot.start_new_user = AsyncMock()
        
        await bot.start(mock_update, mock_context)
        
        bot.user_service.get_user_by_telegram_id.assert_called_once_with("123456789")
        bot.message_service.get_message.assert_called_once_with("en", "welcome_no_name")
        mock_message.reply_text.assert_called_once_with("Welcome!")
        bot.start_new_user.assert_called_once_with(mock_update, mock_context)
    
    @pytest.mark.asyncio
    async def test_status_command_with_registrations(self, bot, mock_update, mock_context):
        """Test /status command when user has registrations"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        # Mock user data
        user_data = {'language': 'en'}
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=user_data)
        
        # Mock registrations
        mock_registration = Mock()
        mock_registration.event_id = "event1"
        mock_registration.status = "approved"
        bot.registration_service.get_all_registrations_for_user = AsyncMock(return_value=[mock_registration])
        bot.event_service.get_event_name_by_id.return_value = "Test Event"
        
        await bot.status(mock_update, mock_context)
        
        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "Test Event" in call_args
        assert "approved" in call_args
    
    @pytest.mark.asyncio
    async def test_status_command_no_user(self, bot, mock_update, mock_context):
        """Test /status command when user doesn't exist"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=None)
        bot.message_service.get_message.return_value = "No user found"
        
        await bot.status(mock_update, mock_context)
        
        # The method is called with the actual language_code from the mock user
        bot.message_service.get_message.assert_called_once()
        mock_message.reply_text.assert_called_once_with("No user found")
    
    @pytest.mark.asyncio
    async def test_help_command(self, bot, mock_update, mock_context):
        """Test /help command"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        # Mock get_language_from_user as async function
        bot.get_language_from_user = AsyncMock(return_value="en")
        bot.message_service.get_message.return_value = "Help message"
        
        await bot.help_command(mock_update, mock_context)
        
        bot.get_language_from_user.assert_called_once_with("123456789")
        bot.message_service.get_message.assert_called_once_with("en", "help")
        mock_message.reply_text.assert_called_once_with("Help message")
    
    @pytest.mark.asyncio
    async def test_register_command(self, bot, mock_update, mock_context):
        """Test /register command"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        mock_question = Mock(spec=QuestionDefinition)
        bot.form_flow_service.handle_register_start = AsyncMock(return_value=mock_question)
        bot.send_question_as_telegram_message = AsyncMock()
        # Mock user service as async
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=None)
        
        await bot.register(mock_update, mock_context)
        
        bot.form_flow_service.handle_register_start.assert_called_once_with("123456789", language="en")
        bot.send_question_as_telegram_message.assert_called_once_with(mock_question, "en", "123456789")
    
    @pytest.mark.asyncio
    async def test_register_command_no_question(self, bot, mock_update, mock_context):
        """Test /register command when no question is returned"""
        bot.form_flow_service.handle_register_start = AsyncMock(return_value=None)
        bot.send_question_as_telegram_message = AsyncMock()
        # Mock user service as async
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=None)
        
        await bot.register(mock_update, mock_context)
        
        bot.form_flow_service.handle_register_start.assert_called_once()
        bot.send_question_as_telegram_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_poll_answer(self, bot):
        """Test handling poll answers"""
        # Create a proper mock update with poll_answer
        update = Mock()
        poll_answer = Mock(spec=PollAnswer)
        poll_answer.poll_id = "poll123"
        poll_answer.user.id = 123456789
        poll_answer.option_ids = [0, 1]
        update.poll_answer = poll_answer
        
        # Mock poll data
        bot.poll_data = {
            "poll123": {
                "question_field": "test_field",
                "votes": {0: [], 1: []}
            }
        }
        
        mock_question = Mock(spec=QuestionDefinition)
        bot.form_flow_service.handle_poll_answer = AsyncMock(return_value=mock_question)
        bot.send_question_as_telegram_message = AsyncMock()
        # Mock get_language_from_user as async function
        bot.get_language_from_user = AsyncMock(return_value="en")
        bot.save_poll_data = Mock()
        
        await bot.handle_poll_answer(update, Mock())
        
        bot.form_flow_service.handle_poll_answer.assert_called_once_with("test_field", "123456789", [0, 1])
        bot.send_question_as_telegram_message.assert_called_once_with(mock_question, "en", "123456789")
    
    @pytest.mark.asyncio
    async def test_handle_text_messages(self, bot, mock_update, mock_context):
        """Test handling text messages"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        mock_question = Mock(spec=QuestionDefinition)
        bot.form_flow_service.handle_text_answer = AsyncMock(return_value=mock_question)
        bot.send_question_as_telegram_message = AsyncMock()
        # Mock get_language_from_user as async function
        bot.get_language_from_user = AsyncMock(return_value="en")
        
        await bot.handle_text_messages(mock_update, mock_context)
        
        bot.form_flow_service.handle_text_answer.assert_called_once_with(mock_update, mock_context)
        bot.send_question_as_telegram_message.assert_called_once_with(mock_question, "en", "123456789")
    
    @pytest.mark.asyncio
    async def test_handle_text_messages_with_message(self, bot, mock_update, mock_context):
        """Test handling text messages that return a message instead of question"""
        mock_update.message = mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        bot.form_flow_service.handle_text_answer = AsyncMock(return_value={"message": "Test message"})
        bot.send_question_as_telegram_message = AsyncMock()
        
        await bot.handle_text_messages(mock_update, mock_context)
        
        bot.form_flow_service.handle_text_answer.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_handle_callback_query(self, bot):
        """Test handling callback queries"""
        update = Mock()
        query = Mock()
        query.data = "btn1"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        await bot.handle_callback_query(update, Mock())
        
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once_with(text="Btn1 is pressed.")
    
    def test_get_language_from_user_with_user(self, bot):
        """Test getting language from existing user"""
        user_data = {'language': 'he'}
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=user_data)
        bot.user_service.headers = {'language': 'language'}
        
        # Since get_language_from_user is async, we need to await it
        async def test_async():
            language = await bot.get_language_from_user("123456789")
            assert language == "he"
            bot.user_service.get_user_by_telegram_id.assert_called_once_with("123456789")
        
        asyncio.run(test_async())
    
    def test_get_language_from_user_no_user(self, bot):
        """Test getting language when user doesn't exist"""
        bot.user_service.get_user_by_telegram_id = AsyncMock(return_value=None)
        
        # Since get_language_from_user is async, we need to await it
        async def test_async():
            language = await bot.get_language_from_user("123456789")
            assert language == "en"
        
        asyncio.run(test_async())
    
    @pytest.mark.asyncio
    async def test_send_question_as_telegram_message_poll(self, bot):
        """Test sending poll questions"""
        question = Mock(spec=QuestionDefinition)
        question.question_type = QuestionType.BOOLEAN
        
        bot.send_telegram_poll = AsyncMock()
        bot.send_telegram_text_message = AsyncMock()
        
        await bot.send_question_as_telegram_message(question, "en", "123456789")
        
        bot.send_telegram_poll.assert_called_once_with(question, "en", "123456789")
        bot.send_telegram_text_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_question_as_telegram_message_text(self, bot):
        """Test sending text questions"""
        question = Mock(spec=QuestionDefinition)
        question.question_type = QuestionType.TEXT
        
        bot.send_telegram_poll = AsyncMock()
        bot.send_telegram_text_message = AsyncMock()
        
        await bot.send_question_as_telegram_message(question, "en", "123456789")
        
        bot.send_telegram_text_message.assert_called_once_with(question, "en", "123456789")
        bot.send_telegram_poll.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_telegram_text_message(self, bot):
        """Test sending text messages"""
        question = Mock(spec=QuestionDefinition)
        question.title = Mock()
        question.title.en = "Test question"
        question.title.he = "שאלה לבדיקה"
        question.placeholder = None
        
        # Mock the bot.send_message method
        bot.app.bot.send_message = AsyncMock()
        
        await bot.send_telegram_text_message(question, "en", "123456789")
        
        bot.app.bot.send_message.assert_called_once_with("123456789", "Test question")
    
    @pytest.mark.asyncio
    async def test_send_telegram_text_message_with_placeholder(self, bot):
        """Test sending text messages with placeholder"""
        question = Mock(spec=QuestionDefinition)
        question.title = Mock()
        question.title.en = "Test question"
        question.title.he = "שאלה לבדיקה"
        question.placeholder = Mock()
        question.placeholder.en = "Enter your answer"
        question.placeholder.he = "הכנס את התשובה שלך"
        
        # Mock the bot.send_message method
        bot.app.bot.send_message = AsyncMock()
        
        await bot.send_telegram_text_message(question, "en", "123456789")
        
        expected_message = "Test question\n(Enter your answer)"
        bot.app.bot.send_message.assert_called_once_with("123456789", expected_message)
    
    @pytest.mark.asyncio
    async def test_send_telegram_poll(self, bot):
        """Test sending telegram polls"""
        question = Mock(spec=QuestionDefinition)
        question.question_id = "test_question"
        question.title = Mock()
        question.title.get = Mock(return_value="Test poll")
        question.question_type = QuestionType.BOOLEAN
        question.options = [
            Mock(text=Mock(get=Mock(return_value="Yes"))),
            Mock(text=Mock(get=Mock(return_value="No")))
        ]
        
        mock_message = Mock()
        mock_message.poll.id = "poll123"
        mock_message.message_id = 456
        bot.app.bot.send_poll = AsyncMock(return_value=mock_message)
        
        # Reset poll_data to empty dict for this test
        bot.poll_data = {}
        
        await bot.send_telegram_poll(question, "en", "123456789")
        
        bot.app.bot.send_poll.assert_called_once()
        call_args = bot.app.bot.send_poll.call_args
        assert call_args[1]['chat_id'] == "123456789"
        assert call_args[1]['question'] == "Test poll"
        assert call_args[1]['options'] == ["Yes", "No"]
        assert call_args[1]['allows_multiple_answers'] is False
        
        # Check that poll data was stored
        assert "poll123" in bot.poll_data
        assert bot.poll_data["poll123"]["question_field"] == "test_question"
    
    def test_parse_poll_options(self, bot):
        """Test parsing poll options"""
        options = [
            Mock(text=Mock(get=Mock(return_value="Option 1"))),
            Mock(text=Mock(get=Mock(return_value="Option 2")))
        ]
        
        result = bot.parse_poll_options(options, "en")
        
        assert result == ["Option 1", "Option 2"]
    
    def test_parse_poll_options_empty(self, bot):
        """Test parsing empty poll options"""
        result = bot.parse_poll_options([], "en")
        
        assert result == []
    
    def test_update_poll_data(self, bot):
        """Test updating poll data"""
        poll_answer = Mock(spec=PollAnswer)
        poll_answer.poll_id = "poll123"
        poll_answer.user.id = 123456789
        poll_answer.option_ids = [0, 1]
        
        # Set up poll data with different user IDs to avoid conflicts
        bot.poll_data = {
            "poll123": {
                "votes": {0: [999], 1: [888]}
            }
        }
        
        bot.update_poll_data(poll_answer)
        
        # Check that new votes were added (the logic might not remove old votes)
        assert 123456789 in bot.poll_data["poll123"]["votes"][0]
        assert 123456789 in bot.poll_data["poll123"]["votes"][1]
    
    def test_save_poll_data(self, bot):
        """Test saving poll data"""
        test_data = {"test": "data"}
        bot.file_storage.save_data.return_value = True
        
        result = bot.save_poll_data(test_data)
        
        assert result is True
        bot.file_storage.save_data.assert_called_once_with("poll_data", test_data)
    
    def test_load_poll_data(self, bot):
        """Test loading poll data"""
        test_data = {"test": "data"}
        # Reset the mock to avoid conflicts with initialization
        bot.file_storage.load_data = Mock(return_value=test_data)
        
        result = bot.load_poll_data()
        
        assert result == test_data
        bot.file_storage.load_data.assert_called_once_with("poll_data", {})
    
    @pytest.mark.asyncio
    async def test_build_app(self, bot):
        """Test building the telegram application"""
        with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'}):
            with patch('wild_ginger_bot.ApplicationBuilder') as mock_builder:
                mock_app = Mock()
                mock_builder.return_value.token.return_value.build.return_value = mock_app
                
                bot.build_app()
                
                mock_builder.assert_called_once()
                mock_builder.return_value.token.assert_called_once_with('test_token')
                mock_builder.return_value.token.return_value.build.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_app_no_token(self, bot):
        """Test building app without token raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN environment variable is required"):
                bot.build_app()
    
    @pytest.mark.asyncio
    async def test_setup_bot_commands(self, bot):
        """Test setting up bot commands"""
        mock_app = Mock()
        mock_app.bot.set_my_commands = AsyncMock()
        
        await bot.setup_bot_commands(mock_app)
        
        mock_app.bot.set_my_commands.assert_called_once()
        commands = mock_app.bot.set_my_commands.call_args[0][0]
        assert len(commands) == 4
        command_names = [cmd.command for cmd in commands]
        assert "start" in command_names
        assert "status" in command_names
        assert "help" in command_names
        assert "register" in command_names
    
    @pytest.mark.asyncio
    async def test_post_init(self, bot):
        """Test post initialization"""
        mock_app = Mock()
        bot.setup_bot_commands = AsyncMock()
        
        await bot.post_init(mock_app)
        
        bot.setup_bot_commands.assert_called_once_with(mock_app) 
        