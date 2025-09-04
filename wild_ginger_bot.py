from telegram import Update, BotCommand, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application, PollAnswerHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
import os
from dotenv import load_dotenv
import logging
from typing import List

from telegram_bot.models.form_flow import QuestionDefinition, QuestionType, QuestionOption
from telegram_bot.models.TelegramPollFields import TelegramPollFields
from telegram_bot.models.user import CreateUserFromTelegramDTO

from telegram_bot.services.base_service import BaseService
from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.services.user_service import UserService
from telegram_bot.services.message_service import MessageService
from telegram_bot.services.form_flow_service import FormFlowService
from telegram_bot.services.file_storage_service import FileStorageService
from telegram_bot.services.registration_service import RegistrationService
from telegram_bot.services.event_service import EventService
from telegram_bot.services.poll_data_service import PollDataService

# Load environment variables from .env file
load_dotenv()

# Enable logging
logger = logging.getLogger(__name__)

class WildGingerBot(BaseService):
    def __init__(self):
        super().__init__()
        self.sheets_service = SheetsService()
        self.user_service = UserService(self.sheets_service)
        self.registration_service = RegistrationService(self.sheets_service)
        self.event_service = EventService(self.sheets_service)
        self.message_service = MessageService()
        self.form_flow_service = FormFlowService(self.sheets_service)
        self.file_storage = FileStorageService()
        self.poll_data_service = PollDataService(self.sheets_service)
        self.log_info("WildGingerBot initialized successfully")
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        self.log_info("Initializing WildGingerBot...")
        # Any additional initialization can go here
        
    async def shutdown(self) -> None:
        """Clean up resources when shutting down the service."""
        self.log_info("Shutting down WildGingerBot...")
        # Any cleanup can go here
        
    def get_user_from_update(self, update: Update):
        user = update.effective_user
        return str(user.id)        
    
    async def start_new_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # create new user in the sheet
        await self.create_new_user(user)

        # Start the form flow
        question = await self.form_flow_service.start_form(str(user.id), language=user['language_code'])
        if question:
            await self.send_question_as_telegram_message(question, user['language_code'], str(user.id))
        else:
            self.log_error(f"Could not start form for user {user.id}")
        
        self.log_info(f"Form flow result: {question}")
        
    async def create_new_user(self, user: User):
        user_id = str(user.id)                

        # create new user in the sheet
        new_user = CreateUserFromTelegramDTO(
            full_name=user['first_name'],
            telegram_user_id=user_id,
            telegram_username=user['username'],
            language=user['language_code']
        )
        result = await self.user_service.create_new_user(new_user)
        if result:
            self.log_info(f"User {user_id} created successfully")
        else:
            self.log_error(f"Error creating user {user_id} in the sheet")
        
    # --- /start command handler ---
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = str(user.id)
        
        self.log_info(f"User {user_id} started the bot")
        
        # search if user is already in the sheet
        user_data = self.user_service.get_user_by_telegram_id(user_id)
        
        if user_data:
            self.log_info(f"User {user_id} is already in the sheet")
            language = user_data[self.user_service.headers['language']]
            name = user_data[self.user_service.headers['full_name']]
            await update.message.reply_text(
                # f"Hi {user['first_name']}! how are you?"
                self.message_service.get_message(language, 'welcome', name=name)
            )
            await self.handle_register_start(user_id, language)
            # TODO

        else:
            await update.message.reply_text(
                self.message_service.get_message(user['language_code'], 'welcome_no_name')
            )            
            await self.start_new_user(update, context)

        #TODO         
        return
        # Start the form flow
        result = await form_flow_service.start_form(user_id)   

        # Check if a submission ID was provided
        if context.args:
            submission_id = context.args[0]

            # Store the user -> submission_id mapping
            user_submissions[user_id] = submission_id

            # Get status data (from Google Sheets or mock data)
            status_data = await get_status_data(submission_id=submission_id)

            if status_data:
                # Link the Telegram User ID to the submission in Google Sheets
                await sheets_service.update_telegram_user_id(submission_id, user_id)

                # TASK: new registers - automatically mark them as 'Form Complete' TRUE
                # If I have a record, that means they filled out the form
                update_form_complete(submission_id, True)

                # TASK: returning participant - auto mark 'Get To Know Complete' as TRUE
                # If they participated in a previous event, they already know the process
                if status_data.get('is_returning_participant'):
                    update_get_to_know_complete(submission_id, True)

                # NEW TASK 1: if the "paid" col (J) isn't empty mark "Payment Complete"
                # Check if there's payment data in the paid column and auto-update payment_complete
                if sheets_service:
                    try:
                        sheet_data = sheets_service.get_sheet_data()  
                        if sheet_data:
                            headers = sheet_data['headers']
                            rows = sheet_data['rows']
                            column_indices = sheets_service.get_column_indices(headers) 

                            submission_id_col = column_indices.get('submission_id')
                            paid_col = column_indices.get('paid')

                            if submission_id_col is not None and paid_col is not None:
                                # Find the current user's row
                                for row in rows:
                                    if (len(row) > submission_id_col and 
                                        row[submission_id_col] == submission_id and
                                        len(row) > paid_col):

                                        paid_col_value = row[paid_col].strip() if row[paid_col] else ''

                                        if paid_col_value and not status_data.get('paid', False):
                                            print(f"✅ Found payment data in paid column for {status_data['alias']}: '{paid_col_value}' - auto-updating payment_complete to TRUE")
                                            update_payment_complete(submission_id, True)
                                            break
                    except Exception as e:
                        print(f"❌ Error checking paid column: {e}")

                # Send welcome message
                await update.message.reply_text(
                    get_message(status_data['language'], 'welcome', name=status_data['alias'])
                )

                # TASK: chat continues - keep the conversation going after /start
                # Guide user to their next step instead of letting conversation fade
                await continue_conversation(update, context, status_data)

                # Check if user is now ready for review and notify admins
                await check_and_notify_ready_for_review(status_data)
            else:
                # Default to English if no submission found
                await update.message.reply_text(
                    get_message('en', 'submission_not_found', submission_id=submission_id)
                )
        else:
            # No submission ID provided
            # Use Telegram user's language if available, otherwise default to English
            user_language = 'he' if user.language_code == 'he' else 'en'
            await update.message.reply_text(
                get_message(user_language, 'welcome_no_name')
            )

    # --- /status command handler ---
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        teleg_user = update.effective_user
        user_id = str(teleg_user.id)
        self.log_info(f"User {user_id} checked status")
        
        user = self.user_service.get_user_by_telegram_id(user_id)
        if user:
            registrations = await self.registration_service.get_all_registrations_for_user(user_id)
            if registrations:
                status_message = f"you're registered for {len(registrations)} events:\n"
                for registration in registrations:
                    event_name = self.event_service.get_event_name_by_id(registration.event_id)
                    status_message += f"{event_name}: {registration.status}\n"
            await update.message.reply_text(
                status_message
            )
        else:
            await update.message.reply_text(self.message_service.get_message(teleg_user.language_code, 'status_no_name'))
        
        
        # button1 = InlineKeyboardButton(text="Button1", callback_data="btn1")
        # button2 = InlineKeyboardButton(text="Button2", callback_data="btn2")
        # inline_keyboard = InlineKeyboardMarkup([[button1]])
        # await update.message.reply_text(
        #     "Welcome to the Bot!",
        #     reply_markup=inline_keyboard
        # )
        
        # TODO
        return
        # Get the submission ID for this user (from local storage)
        submission_id = user_submissions.get(user_id)

        # Get status data from Google Sheets - try submission ID first, then Telegram User ID
        status_data = None
        if submission_id:
            status_data = await get_status_data(submission_id=submission_id)

        if not status_data:
            # Try to find by Telegram User ID in the sheet
            status_data = await get_status_data(telegram_user_id=user_id)

        if not status_data:
            # Use Telegram user's language if available, otherwise default to English
            user_language = 'he' if update.effective_user.language_code == 'he' else 'en'
            await update.message.reply_text(
                get_message(user_language, 'no_submission_linked')
            )
            return

        # Build the status message
        message = get_status_message(status_data)

        await update.message.reply_text(message)

    # --- /help command handler ---
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.get_user_from_update(update)
        self.log_info(f"User {user_id} checked help")
        
        await update.message.reply_text(
            self.message_service.get_message(await self.get_language_from_user(user_id), 'help')
        )

        # TODO
        return
        # Try to get user's language from their submission data first
        submission_id = user_submissions.get(user_id)
        status_data = None

        if submission_id:
            status_data = await get_status_data(submission_id=submission_id)

        if not status_data:
            # Try to find by Telegram User ID in the sheet
            status_data = await get_status_data(telegram_user_id=user_id)

        # Determine language
        if status_data and 'language' in status_data:
            language = status_data['language']
        else:
            # Fallback to Telegram user's language
            language = 'he' if user.language_code == 'he' else 'en'

        await update.message.reply_text(
            get_message(language, 'help')
        )

        # Set up command autocomplete for better user experience
    
    # --- /register command handler ---
    async def register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        user_id = self.get_user_from_update(update)
        self.log_info(f"User {user_id} checked register")
        
        # TODO: search if user is already in the sheet
        # TODO: if user is already in the sheet, start the form flow skip language selection
        # TODO: if user is not in the sheet, create a new user and start the form flow
        # user_data = self.user_service.get_user_by_telegram_id(user_id)
                
        # Start the form flow
        await self.handle_register_start(user.id, user['language_code'])
        return
    
    async def handle_register_start(self, user_id: str, language: str):
        user = self.user_service.get_user_by_telegram_id(user_id)
        if user:
            language = user[self.user_service.headers["language"]]
        else:
            self.log_error(f"No user found for user {user_id}")

        question = await self.form_flow_service.handle_register_start(str(user_id), language=language)
        if question:
            await self.send_question_as_telegram_message(question, language, str(user_id))
        else:
            self.log_error(f"Could not start form for user {user_id}")
        
        self.log_info(f"Form flow result: {question}")
        return
    
    async def handle_poll_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle poll answer updates"""
        poll_answer = update.poll_answer
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id
        selected_options = poll_answer.option_ids
        
        poll_info = self.poll_data_service.get_poll_by_id(poll_id)
        if not poll_info:
            self.log_error(f"Poll {poll_id} not found")
            return
        
        self.log_info(f"Poll info: {poll_info}")
        
        # update poll data
        success = await self.poll_data_service.update_poll(poll_answer)
        if not success:
            self.log_error(f"Failed to save updated poll {poll_id}")
            return
        else:
            self.log_info(f"Poll {poll_id} updated successfully")
        
        # Handle the poll answer in the form flow service
        next_question = await self.form_flow_service.handle_poll_answer(poll_info['question_field'], str(user_id), selected_options)
        if next_question:
            if isinstance(next_question, QuestionDefinition):
                await self.send_question_as_telegram_message(next_question, await self.get_language_from_user(user_id), str(user_id))        
            else:
                # await update.message.reply_text(next_question['message'])
                await self.app.bot.send_message(user_id, next_question['message'], parse_mode=ParseMode.MARKDOWN)
    
    async def handle_text_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages"""
        user_id = self.get_user_from_update(update)
        self.log_info(f"User {user_id} sent a text message")
        
        # TODO: handle the text message
        # get the current question from the active forms
        # Handle the poll answer in the form flow service
        next_question = await self.form_flow_service.handle_text_answer(update, context)
        if next_question:
            if isinstance(next_question, QuestionDefinition):
                await self.send_question_as_telegram_message(next_question, await self.get_language_from_user(user_id), str(user_id))        
            else:
                await update.message.reply_text(next_question['message'], parse_mode=ParseMode.MARKDOWN)
        
        return

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == "btn1":
            await query.edit_message_text(text="Btn1 is pressed.")
        elif query.data == "btn2":
            await query.edit_message_text(text="Btn2 is pressed.")

    async def get_language_from_user(self, user_id: str):
        user_data = self.user_service.get_user_by_telegram_id(user_id)
        if user_data:
            return user_data[self.user_service.headers['language']]
        else:
            return 'en'
    
    async def send_question_as_telegram_message(self, question: QuestionDefinition, language: str, user_id: str):
        if question.question_type  in (QuestionType.BOOLEAN, QuestionType.SELECT, QuestionType.MULTI_SELECT):
            # TODO: create a telegram message with the question
            return await self.send_telegram_poll(question, language, user_id)
        else: # if question.question_type == QuestionType.TEXT or question.question_type == QuestionType.DATE:
            # TODO: create a telegram message with the question
            return await self.send_telegram_text_message(question, language, user_id)
        
    async def send_telegram_text_message(self, question: QuestionDefinition, language: str, user_id: str):
        # Create a text message with the question
        question_text = question.title.he if language == "he" else question.title.en
        
        # Add placeholder if available
        if question.placeholder:
            placeholder_text = question.placeholder.he if language == "he" else question.placeholder.en
            message = f"{question_text}\n({placeholder_text})"
        else:
            message = question_text
            
        await self.app.bot.send_message(user_id, message)
    
    async def send_telegram_poll(self, question_field: QuestionDefinition, language: str, user_id: str):
        # TODO: create a telegram poll with the question
        try:
            poll_fields = TelegramPollFields(
                # id=question_field.question_id,
                question=question_field.title.get(language),
                options=self.parse_poll_options(question_field.options, language),
                is_anonymous=False,
                allows_multiple_answers=question_field.question_type == QuestionType.MULTI_SELECT
            )

            message = await self.app.bot.send_poll(
                chat_id=user_id,
                question=poll_fields.question,
                options=poll_fields.options,
                is_anonymous=poll_fields.is_anonymous,
                allows_multiple_answers=poll_fields.allows_multiple_answers
            )

            # Store poll data
            poll_info = {
                    "id": message.poll.id,
                    "question_field": question_field.question_id,
                    "question": poll_fields.question,
                    "options": poll_fields.options,
                    "chat_id": user_id,
                    "message_id": message.message_id,
                    "creator": user_id,
                    "type": "regular",
                    "votes": {i: [] for i in range(len(poll_fields.options))}
            }

            # Save to storage using PollDataService
            success = await self.poll_data_service.save_single_poll(message.poll.id, poll_info)
            if not success:
                self.log_error(f"Failed to save poll {message.poll.id}")
        except Exception as e:
            logger.error(f"Error sending poll: {e}")
    
    def parse_poll_options(self, options: List[QuestionOption], language: str):
        """Parse poll options to get text in the specified language."""
        if not options:
            return []
        return [option.text.get(language) for option in options]
    
    def build_app(self):        
        self.log_info("Building Telegram application...")
        # --- Bot token from environment variable ---
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        if not BOT_TOKEN:
            self.log_error("TELEGRAM_BOT_TOKEN environment variable is required")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required. Please set it in your .env file.")
        
        self.log_info("Bot token found, creating application...")

        app = ApplicationBuilder().token(BOT_TOKEN).build()
    
        self.log_info("Adding command handlers...")
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("register", self.register))
        # app.add_handler(CommandHandler("update", self.update))
        # app.add_handler(CommandHandler("remind_partner", remind_partner))
        # app.add_handler(CommandHandler("cancel", cancel_registration))
        # app.add_handler(CommandHandler("get_to_know", get_to_know_command))
        
        # Poll handlers
        app.add_handler(PollAnswerHandler(self.handle_poll_answer))
        
        app.add_handler(CallbackQueryHandler(self.handle_callback_query))
        # Admin commands
        # app.add_handler(CommandHandler("admin_dashboard", admin_dashboard))
        # app.add_handler(CommandHandler("admin_approve", admin_approve))
        # app.add_handler(CommandHandler("admin_reject", admin_reject))
        # app.add_handler(CommandHandler("admin_status", admin_status))
        # app.add_handler(CommandHandler("admin_digest", admin_digest))
        
        # Message handlers (must be after command handlers)
        # Listen to ALL text messages (except commands - they're handled above)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_messages))
        
        # Set the post_init hook
        app.post_init = self.post_init

        self.app = app
        self.form_flow_service.set_telegram_bot(app.bot)
        self.log_info("Application built successfully")
        self.log_info("Bot is running with polling...")

        try:
            app.run_polling(drop_pending_updates=False)
        except Exception as e:
            if "Conflict" in str(e):
                self.log_error("Another instance of the bot is already running!")
                self.log_error("Solutions:")
                self.log_error("1. Stop any other running instances of this bot")
                self.log_error("2. Wait a few seconds and try again")
                self.log_error("3. If you have a webhook configured, disable it first")
                self.log_error("4. Check your task manager for other Python processes")
            else:
                self.log_error(f"Error starting bot: {e}")
            exit(1)

    
    async def setup_bot_commands(self, app: Application):
        """Set up bot command autocomplete"""
        commands = [
            BotCommand("start", "Link your registration or get welcome message"),
            BotCommand("status", "Check your registration progress"),
            BotCommand("help", "Show help and available commands"),
            BotCommand("register", "Register for an event"),
            # BotCommand("cancel", "Cancel your registration with reason"),
            # BotCommand("remind_partner", "Send reminder to partner(s)"),
            # BotCommand("get_to_know", "Complete the get-to-know section"),
        ]
        
        try:
            await app.bot.set_my_commands(commands)
            self.log_info("Bot command autocomplete set up successfully")
        except Exception as e:
            self.log_error(f"Error setting up bot commands: {e}")
    
    # Post-init hook to start background tasks
    async def post_init(self, app: Application):
        """Initialize background tasks after bot starts"""
        # Set up command autocomplete
        await self.setup_bot_commands(app)
            

# --- Main runner ---
if __name__ == '__main__':
    bot = WildGingerBot()
    bot.log_info("Starting Wild Ginger Bot...")
    bot.build_app()
    
