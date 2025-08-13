import logging
import os
from telegram import Update, Poll, PollOption
from telegram.ext import Application, CommandHandler, PollAnswerHandler, MessageHandler, filters, ContextTypes, PollHandler
import json
from .file_storage_service import FileStorageService

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramPollBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.file_storage = FileStorageService()
        self.poll_data = self.load_poll_data()
        self.setup_handlers()
        print("✅ Telegram Poll Bot initialized")
    
    def load_poll_data(self) -> dict:
        """Load poll data from file storage."""
        try:
            poll_data = self.file_storage.load_data("poll_data", {})
            logger.info(f"Loaded {len(poll_data)} polls from storage")
            return poll_data
        except Exception as e:
            logger.error(f"Error loading poll data: {e}")
            return {}
    
    def save_poll_data(self) -> bool:
        """Save poll data to file storage."""
        try:
            success = self.file_storage.save_data("poll_data", self.poll_data)
            if success:
                logger.info(f"Saved {len(self.poll_data)} polls to storage")
            return success
        except Exception as e:
            logger.error(f"Error saving poll data: {e}")
            return False
    
    def setup_handlers(self):
        """Set up command and message handlers"""
        # Command handlers (these have higher priority)
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("poll", self.create_poll))
        self.application.add_handler(CommandHandler("quiz", self.create_quiz))
        self.application.add_handler(CommandHandler("results", self.get_poll_results))
        
        # Special message handlers
        self.application.add_handler(PollAnswerHandler(self.handle_poll_answer))
        self.application.add_handler(MessageHandler(filters.POLL, self.handle_poll_message))
        self.application.add_handler(PollHandler(self.handle_poll_message))

        
        # Listen to ALL text messages (except commands - they're handled above)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_all_messages))
        
        # Listen to other message types (optional)
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        # self.application.add_handler(MessageHandler(filters.DOCUMENT, self.handle_document))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        # self.application.add_handler(MessageHandler(filters.STICKER, self.handle_sticker))
        
        # Catch-all handler for any other message types (optional)
        self.application.add_handler(MessageHandler(filters.ALL, self.handle_any_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        await update.message.reply_text(
            "🗳️ Welcome to Poll Bot!\n\n"
            "I can help you create polls and track results.\n"
            "Use /help to see available commands."
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
🗳️ **Poll Bot Commands:**

📊 **Create Polls:**
• `/poll question | option1 | option2 | option3` - Create a regular poll
• `/quiz question | correct_answer | wrong1 | wrong2` - Create a quiz

📈 **View Results:**
• `/results` - Get results for the latest poll in this chat
• Reply to a poll with `/results` - Get results for that specific poll

**Examples:**
• `/poll What's your favorite color? | Red | Blue | Green | Yellow`
• `/quiz What is 2+2? | 4 | 3 | 5 | 6`

**Features:**
• Anonymous voting
• Real-time results tracking
• Multiple choice support
• Quiz mode with correct answers
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def create_poll(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a regular poll"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide poll question and options!\n"
                "Format: `/poll question | option1 | option2 | option3`\n\n"
                "Example: `/poll What's your favorite programming language? | Python | JavaScript | Java`"
            )
            return
        
        try:
            # Parse the poll data
            poll_text = " ".join(context.args)
            parts = [part.strip() for part in poll_text.split("|")]
            
            if len(parts) < 3:
                await update.message.reply_text("❌ Please provide at least a question and 2 options!")
                return
            
            if len(parts) > 11:  # Telegram limit: 1 question + max 10 options
                await update.message.reply_text("❌ Maximum 10 options allowed!")
                return
            
            question = parts[0]
            options = parts[1:]
            
            # Create the poll
            message = await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=question,
                options=options,
                is_anonymous=False,
                allows_multiple_answers=True
            )
            
            # Store poll data
            self.poll_data[message.poll.id] = {
                'question': question,
                'options': options,
                'chat_id': update.effective_chat.id,
                'message_id': message.message_id,
                'creator': update.effective_user.id,
                'type': 'regular',
                'votes': {i: [] for i in range(len(options))}
            }
            
            # Save to storage
            self.save_poll_data()
            
            await update.message.reply_text("✅ Poll created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}")
            await update.message.reply_text("❌ Error creating poll. Please check your format.")
    
    async def create_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a quiz poll"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide quiz question and options!\n"
                "Format: `/quiz question | correct_answer | wrong1 | wrong2`\n\n"
                "Example: `/quiz What is the capital of France? | Paris | London | Berlin`"
            )
            return
        
        try:
            # Parse the quiz data
            quiz_text = " ".join(context.args)
            parts = [part.strip() for part in quiz_text.split("|")]
            
            if len(parts) < 3:
                await update.message.reply_text("❌ Please provide at least a question and 2 options!")
                return
            
            question = parts[0]
            options = parts[1:]
            correct_option_id = 0  # First option is always correct
            
            # Create the quiz
            message = await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=question,
                options=options,
                type=Poll.QUIZ,
                correct_option_id=correct_option_id,
                is_anonymous=True
            )
            
            # Store quiz data
            self.poll_data[message.poll.id] = {
                'question': question,
                'options': options,
                'chat_id': update.effective_chat.id,
                'message_id': message.message_id,
                'creator': update.effective_user.id,
                'type': 'quiz',
                'correct_option_id': correct_option_id,
                'votes': {i: [] for i in range(len(options))}
            }
            
            # Save to storage
            self.save_poll_data()
            
            print(f"Quiz created successfully! {self.poll_data[message.poll.id]}")
            
            await update.message.reply_text("✅ Quiz created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating quiz: {e}")
            await update.message.reply_text("❌ Error creating quiz. Please check your format.")
    
    async def handle_poll_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle poll answer updates"""
        poll_answer = update.poll_answer
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id
        selected_options = poll_answer.option_ids
        
        if poll_id not in self.poll_data:
            return
        
        # Update vote tracking
        poll_info = self.poll_data[poll_id]
        print(f"Poll info: {poll_info}")
        
        # Remove user's previous votes
        for option_id in poll_info['votes']:
            if user_id in poll_info['votes'][option_id]:
                poll_info['votes'][option_id].remove(user_id)
        
        # Add new votes
        for option_id in selected_options:
            if option_id not in poll_info['votes']:
                poll_info['votes'][option_id] = []
            poll_info['votes'][option_id].append(user_id)
        
        # Save to storage after vote update
        self.save_poll_data()
        
        print(f"Poll {poll_id}: User {user_id} voted for options {selected_options}")
    
    async def handle_poll_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle poll messages (for tracking purposes)"""
        poll = update.poll
        if poll and poll.id not in self.poll_data:
            # This is a poll we didn't create, still track it
            self.poll_data[poll.id] = {
                'question': poll.question,
                'options': [option.text for option in poll.options],
                'chat_id': update.effective_chat.id,
                'message_id': update.message.message_id,
                'creator': None,
                'type': 'external',
                'votes': {i: [] for i in range(len(poll.options))}
            }
            
            # Save to storage
            self.save_poll_data()
    
    async def handle_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages that aren't commands"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Log the message
        logger.info(f"Message from {user.first_name} ({user.id}) in chat {chat.id}: {message.text}")
        
        # Get message info
        message_text = message.text.lower()
        user_name = user.first_name or user.username or "Unknown"
        
        # Smart responses based on message content
        if any(word in message_text for word in ['hello', 'hi', 'hey', 'start']):
            await message.reply_text(f"Hello {user_name}! 👋\nUse /help to see what I can do!")
        
        elif any(word in message_text for word in ['poll', 'vote', 'survey']):
            await message.reply_text(
                "🗳️ Want to create a poll?\n"
                "Use: `/poll question | option1 | option2 | option3`\n"
                "Or: `/quiz question | correct | wrong1 | wrong2`"
            )
        
        elif any(word in message_text for word in ['help', 'commands', 'what can you do']):
            await self.help_command(update, context)
        
        elif any(word in message_text for word in ['results', 'stats', 'votes']):
            await message.reply_text("📊 Use /results to see poll results!")
        
        else:
            # Echo the message with some processing info
            response = f"📝 I received: \"{message.text}\"\n\n"
            response += f"👤 From: {user_name}\n"
            response += f"💬 Chat: {chat.title if chat.title else 'Private'}\n"
            response += f"📅 Time: {message.date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            response += "💡 Try /help to see what I can do!"
            
            await message.reply_text(response)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages"""
        user = update.effective_user
        photo = update.message.photo[-1]  # Get the highest resolution
        
        logger.info(f"Photo received from {user.first_name} ({user.id})")
        
        await update.message.reply_text(
            f"📸 Nice photo, {user.first_name}!\n"
            f"🔍 File ID: {photo.file_id}\n"
            f"📏 Size: {photo.width}x{photo.height}\n\n"
            "💡 I can create polls about your photos too! Try:\n"
            "`/poll Rate this photo | Amazing | Good | Okay | Meh`"
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages"""
        user = update.effective_user
        document = update.message.document
        
        logger.info(f"Document received from {user.first_name} ({user.id}): {document.file_name}")
        
        await update.message.reply_text(
            f"📄 Thanks for the document, {user.first_name}!\n"
            f"📝 File: {document.file_name}\n"
            f"💾 Size: {document.file_size} bytes\n\n"
            "🗳️ Want to create a poll about this document?"
        )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages"""
        user = update.effective_user
        voice = update.message.voice
        
        logger.info(f"Voice message received from {user.first_name} ({user.id})")
        
        await update.message.reply_text(
            f"🎤 Voice message received, {user.first_name}!\n"
            f"⏱️ Duration: {voice.duration} seconds\n\n"
            "🗳️ How about a poll about voice messages?\n"
            "`/poll Do you like voice messages? | Love them | They're okay | Prefer text`"
        )
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        user = update.effective_user
        video = update.message.video
        
        logger.info(f"Video received from {user.first_name} ({user.id})")
        
        await update.message.reply_text(
            f"🎥 Cool video, {user.first_name}!\n"
            f"⏱️ Duration: {video.duration} seconds\n"
            f"📏 Size: {video.width}x{video.height}\n\n"
            "🎬 Want to create a poll about videos?"
        )
    
    async def handle_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle sticker messages"""
        user = update.effective_user
        sticker = update.message.sticker
        
        logger.info(f"Sticker received from {user.first_name} ({user.id}): {sticker.emoji}")
        
        await update.message.reply_text(
            f"🔥 Nice sticker, {user.first_name}! {sticker.emoji}\n\n"
            "😄 How about a poll about stickers?\n"
            "`/poll What's your favorite sticker emotion? | Happy 😊 | Sad 😢 | Angry 😠 | Love 😍`"
        )
    
    async def handle_any_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Catch-all handler for any message type not handled above"""
        user = update.effective_user
        message = update.message
        
        # Log all message types
        message_types = []
        if message.text: message_types.append("text")
        if message.photo: message_types.append("photo")
        if message.video: message_types.append("video")
        if message.voice: message_types.append("voice")
        if message.document: message_types.append("document")
        if message.sticker: message_types.append("sticker")
        if message.animation: message_types.append("gif")
        if message.location: message_types.append("location")
        if message.contact: message_types.append("contact")
        if message.poll: message_types.append("poll")
        
        logger.info(f"Message from {user.first_name} ({user.id}): {', '.join(message_types)}")
        
        await message.reply_text(
            f"📨 I received a message from {user.first_name}!\n"
            f"🔍 Type: {', '.join(message_types) if message_types else 'unknown'}\n\n"
            "🤖 I can handle various message types and create polls about anything!"
        )
    
    async def get_poll_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get poll results"""
        chat_id = update.effective_chat.id
        
        # Check if replying to a poll
        if update.message.reply_to_message and update.message.reply_to_message.poll:
            poll_id = update.message.reply_to_message.poll.id
            if poll_id in self.poll_data:
                await self.send_poll_results(update, poll_id)
            else:
                await update.message.reply_text("❌ No data available for this poll.")
            return
        
        # Find the latest poll in this chat
        latest_poll = None
        for poll_id, poll_info in reversed(self.poll_data.items()):
            if poll_info['chat_id'] == chat_id:
                latest_poll = poll_id
                break
        
        if latest_poll:
            await self.send_poll_results(update, latest_poll)
        else:
            await update.message.reply_text("❌ No polls found in this chat.")
    
    async def send_poll_results(self, update: Update, poll_id: str):
        """Send formatted poll results"""
        if poll_id not in self.poll_data:
            await update.message.reply_text("❌ Poll data not found.")
            return
        
        poll_info = self.poll_data[poll_id]
        question = poll_info['question']
        options = poll_info['options']
        votes = poll_info['votes']
        poll_type = poll_info['type']
        
        # Calculate total votes
        total_votes = sum(len(user_list) for user_list in votes.values())
        
        # Build results message
        results_text = f"📊 **Poll Results**\n\n"
        results_text += f"❓ **Question:** {question}\n\n"
        
        if poll_type == 'quiz' and 'correct_option_id' in poll_info:
            results_text += f"✅ **Correct Answer:** {options[poll_info['correct_option_id']]}\n\n"
        
        results_text += f"🗳️ **Total Votes:** {total_votes}\n\n"
        
        # Add option results
        for i, option in enumerate(options):
            vote_count = len(votes.get(i, []))
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            # Add emoji for correct answer in quiz
            emoji = "✅ " if poll_type == 'quiz' and i == poll_info.get('correct_option_id', -1) else "• "
            
            results_text += f"{emoji}**{option}:** {vote_count} votes ({percentage:.1f}%)\n"
            
            # Add progress bar
            bar_length = 10
            filled_length = int(bar_length * percentage / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            results_text += f"  {bar}\n\n"
        
        await update.message.reply_text(results_text, parse_mode='Markdown')
    
    def run(self):
        """Start the bot"""
        print("🤖 Starting Telegram Poll Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# Main execution
if __name__ == "__main__":
    # Try to get token from environment variable first, then fallback to hardcoded
    BOT_TOKEN = "7712413209:AAHoJiujVbikMQyPjkk8CDfy2yCKp-cIQZI"
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN.strip():
        print("❌ Bot token not found!")
        print("\n📝 Option 1 - Set environment variable (recommended):")
        print("   Windows: set TELEGRAM_BOT_TOKEN=your_token_here")
        print("   Linux/Mac: export TELEGRAM_BOT_TOKEN=your_token_here")
        print("\n📝 Option 2 - Replace BOT_TOKEN in code:")
        print("   Change 'YOUR_BOT_TOKEN_HERE' to your actual token")
        print("\n🤖 Steps to get a bot token:")
        print("   1. Message @BotFather on Telegram")
        print("   2. Send /newbot")
        print("   3. Follow the instructions to create your bot")
        print("   4. Copy the token (format: 123456789:ABCdefGHIjklMNOpqrSTUvwxyz)")
        exit(1)
    
    # Validate token format
    if ':' not in BOT_TOKEN or len(BOT_TOKEN) < 35:
        print("❌ Invalid token format!")
        print("🔍 Token should look like: 123456789:ABCdefGHIjklMNOpqrSTUvwxyz")
        exit(1)
    
    try:
        print("🤖 Starting Telegram Poll Bot...")
        print(f"🔑 Using token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
        bot = TelegramPollBot(BOT_TOKEN)
        bot.run()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("🔍 Please check:")
        print("   - Your bot token is correct")
        print("   - You have internet connection")
        print("   - The bot wasn't revoked by @BotFather")