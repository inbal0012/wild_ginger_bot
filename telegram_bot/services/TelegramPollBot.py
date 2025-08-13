import logging
from telegram import Update, Poll, PollOption
from telegram.ext import Application, CommandHandler, PollAnswerHandler, MessageHandler, filters, ContextTypes
import json

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store poll data (in production, use a database)
poll_data = {}

class TelegramPollBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("poll", self.create_poll))
        self.application.add_handler(CommandHandler("quiz", self.create_quiz))
        self.application.add_handler(CommandHandler("results", self.get_poll_results))
        self.application.add_handler(PollAnswerHandler(self.handle_poll_answer))
        self.application.add_handler(MessageHandler(filters.POLL, self.handle_poll_message))
    
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
                is_anonymous=True,
                allows_multiple_answers=False
            )
            
            # Store poll data
            poll_data[message.poll.id] = {
                'question': question,
                'options': options,
                'chat_id': update.effective_chat.id,
                'message_id': message.message_id,
                'creator': update.effective_user.id,
                'type': 'regular',
                'votes': {i: [] for i in range(len(options))}
            }
            
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
            poll_data[message.poll.id] = {
                'question': question,
                'options': options,
                'chat_id': update.effective_chat.id,
                'message_id': message.message_id,
                'creator': update.effective_user.id,
                'type': 'quiz',
                'correct_option_id': correct_option_id,
                'votes': {i: [] for i in range(len(options))}
            }
            
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
        
        if poll_id not in poll_data:
            return
        
        # Update vote tracking
        poll_info = poll_data[poll_id]
        
        # Remove user's previous votes
        for option_id in poll_info['votes']:
            if user_id in poll_info['votes'][option_id]:
                poll_info['votes'][option_id].remove(user_id)
        
        # Add new votes
        for option_id in selected_options:
            if option_id not in poll_info['votes']:
                poll_info['votes'][option_id] = []
            poll_info['votes'][option_id].append(user_id)
        
        logger.info(f"Poll {poll_id}: User {user_id} voted for options {selected_options}")
    
    async def handle_poll_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle poll messages (for tracking purposes)"""
        poll = update.message.poll
        if poll and poll.id not in poll_data:
            # This is a poll we didn't create, still track it
            poll_data[poll.id] = {
                'question': poll.question,
                'options': [option.text for option in poll.options],
                'chat_id': update.effective_chat.id,
                'message_id': update.message.message_id,
                'creator': None,
                'type': 'external',
                'votes': {i: [] for i in range(len(poll.options))}
            }
    
    async def get_poll_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get poll results"""
        chat_id = update.effective_chat.id
        
        # Check if replying to a poll
        if update.message.reply_to_message and update.message.reply_to_message.poll:
            poll_id = update.message.reply_to_message.poll.id
            if poll_id in poll_data:
                await self.send_poll_results(update, poll_id)
            else:
                await update.message.reply_text("❌ No data available for this poll.")
            return
        
        # Find the latest poll in this chat
        latest_poll = None
        for poll_id, poll_info in reversed(poll_data.items()):
            if poll_info['chat_id'] == chat_id:
                latest_poll = poll_id
                break
        
        if latest_poll:
            await self.send_poll_results(update, latest_poll)
        else:
            await update.message.reply_text("❌ No polls found in this chat.")
    
    async def send_poll_results(self, update: Update, poll_id: str):
        """Send formatted poll results"""
        if poll_id not in poll_data:
            await update.message.reply_text("❌ Poll data not found.")
            return
        
        poll_info = poll_data[poll_id]
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
    # Replace with your bot token from @BotFather
    BOT_TOKEN = "7712413209:AAHoJiujVbikMQyPjkk8CDfy2yCKp-cIQZI"
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please replace BOT_TOKEN with your actual bot token from @BotFather")
        print("📝 Steps to get a bot token:")
        print("   1. Message @BotFather on Telegram")
        print("   2. Send /newbot")
        print("   3. Follow the instructions to create your bot")
        print("   4. Copy the token and replace BOT_TOKEN in this script")
    else:
        bot = TelegramPollBot(BOT_TOKEN)
        bot.run()