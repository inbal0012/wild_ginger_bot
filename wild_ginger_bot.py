from telegram import Update, BotCommand, User
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application
import os
from dotenv import load_dotenv
import logging

from telegram_bot.services.sheets_service import SheetsService
from telegram_bot.services.user_service import UserService
from telegram_bot.services.message_service import MessageService
from telegram_bot.models.user import CreateUserFromTelegramDTO
from telegram_bot.services.form_flow_service import FormFlowService
from telegram_bot.services.file_storage_service import FileStorageService

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

class WildGingerBot:
    def __init__(self):
        self.sheets_service = SheetsService()
        self.user_service = UserService(self.sheets_service)
        self.message_service = MessageService()
        self.form_flow_service = FormFlowService(self.sheets_service)
        self.file_storage = FileStorageService()
    
    def get_user_from_update(self, update: Update):
        user = update.effective_user
        return str(user.id)        
    
    async def start_new_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # create new user in the sheet
        await self.create_new_user(user)
        
        # TODO: send welcome message
        # TODO multi language support
        await update.message.reply_text(
            f"Hi {user['first_name']}! nice to meet you!"
        )
        
        # TODO: start the form flow
        result = await self.form_flow_service.start_form(str(user.id), language=user['language_code'])
        
        print(f"👋 Form flow result: {result}")
        
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
            print(f"👋 User {user_id} created successfully")
        else:
            print(f"❌ Error creating user {user_id} in the sheet")
        
    # --- /start command handler ---
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.get_user_from_update(update)
        
        print(f"👋 User {user_id} started the bot")
        
        # search if user is already in the sheet
        user_data = self.user_service.find_user_by_telegram_id(user_id)
        if user_data:
            print(f"👋 User {user_id} is already in the sheet")
            await update.message.reply_text(
                # f"Hi {user['first_name']}! how are you?"
                self.message_service.get_message(user_data[self.user_service.headers['language']], 'welcome', name=user_data[self.user_service.headers['full_name']])
            )
            # TODO

        else:
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
        user_id = str(update.effective_user.id)
        print(f"👋 User {user_id} checked status")
        
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
        print(f"👋 User {user_id} checked help")
        
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
    
    
    def build_app(self):        
        # --- Bot token from environment variable ---
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required. Please set it in your .env file.")

        app = ApplicationBuilder().token(BOT_TOKEN).build()
    
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("help", self.help_command))
        # app.add_handler(CommandHandler("remind_partner", remind_partner))
        # app.add_handler(CommandHandler("cancel", cancel_registration))
        # app.add_handler(CommandHandler("get_to_know", get_to_know_command))
        
        # Admin commands
        # app.add_handler(CommandHandler("admin_dashboard", admin_dashboard))
        # app.add_handler(CommandHandler("admin_approve", admin_approve))
        # app.add_handler(CommandHandler("admin_reject", admin_reject))
        # app.add_handler(CommandHandler("admin_status", admin_status))
        # app.add_handler(CommandHandler("admin_digest", admin_digest))
        
        # Message handlers (must be after command handlers)
        from telegram.ext import MessageHandler, filters
        # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_get_to_know_response))

        # Set the post_init hook
        app.post_init = self.post_init

        print("Bot is running with polling...")

        try:
            app.run_polling(drop_pending_updates=True)
        except Exception as e:
            if "Conflict" in str(e):
                print("❌ Error: Another instance of the bot is already running!")
                print("Solutions:")
                print("1. Stop any other running instances of this bot")
                print("2. Wait a few seconds and try again")
                print("3. If you have a webhook configured, disable it first")
                print("4. Check your task manager for other Python processes")
            else:
                print(f"❌ Error starting bot: {e}")
            exit(1)

    
    async def setup_bot_commands(self, app: Application):
        """Set up bot command autocomplete"""
        commands = [
            BotCommand("start", "Link your registration or get welcome message"),
            BotCommand("status", "Check your registration progress"),
            BotCommand("help", "Show help and available commands"),
            # BotCommand("cancel", "Cancel your registration with reason"),
            # BotCommand("remind_partner", "Send reminder to partner(s)"),
            # BotCommand("get_to_know", "Complete the get-to-know section"),
        ]
        
        try:
            await app.bot.set_my_commands(commands)
            print("✅ Bot command autocomplete set up successfully")
        except Exception as e:
            print(f"❌ Error setting up bot commands: {e}")
    
    # Post-init hook to start background tasks
    async def post_init(self, app: Application):
        """Initialize background tasks after bot starts"""
        # Set up command autocomplete
        await self.setup_bot_commands(app)
            

# --- Main runner ---
if __name__ == '__main__':
    bot = WildGingerBot()
    bot.build_app()
    
