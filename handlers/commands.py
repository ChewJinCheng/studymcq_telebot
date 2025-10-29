from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from database.queries import DatabaseQueries
from services.quiz_manager import QuizManager
from messages import BotMessages
from utils.logger import setup_logger
import html

logger = setup_logger(__name__)

class CommandHandlers:
    """All command handlers"""
    
    def __init__(self, db_queries: DatabaseQueries, quiz_manager: QuizManager):
        self.db = db_queries
        self.quiz_manager = quiz_manager
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        self.db.save_user_settings(user_id, username)
        
        await update.message.reply_text(BotMessages.WELCOME_MESSAGE, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
    
    async def upload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /upload command - enables upload mode"""
        context.user_data['upload_mode'] = True
        await update.message.reply_text(
            BotMessages.UPLOAD_INSTRUCTIONS,
            parse_mode='Markdown'
        )
    
    async def bank_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bank command"""
        user_id = update.effective_user.id
        count = self.db.get_question_count(user_id)
        
        if count == 0:
            await update.message.reply_text(BotMessages.EMPTY_QUESTION_BANK)
            return
        
        stats = self.db.get_question_bank_stats(user_id)
        
        bank_text = BotMessages.QUESTION_BANK_STATS.format(
            count=count,
            sources=stats['sources'],
            avg_asked=stats['avg_asked'],
            accuracy=stats['accuracy']
        )
        
        await update.message.reply_text(bank_text, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        settings = self.db.get_user_settings(user_id)
        
        keyboard = [
            [InlineKeyboardButton("Set Daily Questions", callback_data='set_questions')],
            [InlineKeyboardButton("Set Quiz Time", callback_data='set_time')],
            [InlineKeyboardButton("Close", callback_data='close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = BotMessages.CURRENT_SETTINGS.format(
            daily_questions=settings['daily_questions'],
            quiz_time=settings['quiz_time']
        )
        
        await update.message.reply_text(
            settings_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
    
    async def quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz command"""
        user_id = update.effective_user.id
        
        # Check if user has questions in bank
        question_count = self.db.get_question_count(user_id)
        
        if question_count == 0:
            await update.message.reply_text(BotMessages.EMPTY_BANK_ERROR)
            return
        
        # Ask user how many questions they want
        await update.message.reply_text(
            BotMessages.ASK_QUIZ_COUNT.format(total=question_count),
            parse_mode='Markdown'
        )
        
        # Set flag to await quiz count input
        context.user_data['awaiting_quiz_count'] = True
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        stats = self.db.get_user_stats(user_id)
        
        if stats['total'] == 0:
            await update.message.reply_text(BotMessages.NO_QUIZ_HISTORY)
            return
        
        accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        stats_text = BotMessages.STATS_DISPLAY.format(
            total=stats['total'],
            correct=stats['correct'],
            accuracy=accuracy
        )
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def clear_knowledge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear_knowledge command"""
        keyboard = [
            [InlineKeyboardButton("✅ Yes, clear knowledge base", 
                                callback_data='confirm_clear_knowledge')],
            [InlineKeyboardButton("❌ Cancel", callback_data='close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            BotMessages.CONFIRM_CLEAR_KNOWLEDGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def clear_questions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear_questions command"""
        keyboard = [
            [InlineKeyboardButton("✅ Yes, clear question bank", 
                                callback_data='confirm_clear_questions')],
            [InlineKeyboardButton("❌ Cancel", callback_data='close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            BotMessages.CONFIRM_CLEAR_QUESTIONS,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def send_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send current question to user"""
        if self.quiz_manager.is_quiz_complete(context):
            summary = self.quiz_manager.get_quiz_summary(context)
            result_text = BotMessages.QUIZ_COMPLETED.format(**summary)
            
            # Clear quiz state
            self.quiz_manager.end_quiz(context)
            
            if update.callback_query:
                await update.callback_query.message.reply_text(result_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(result_text, parse_mode='Markdown')
            return
        
        mcq = self.quiz_manager.get_current_question(context)
        quiz = context.user_data.get('current_quiz', [])
        question_num = context.user_data.get('current_question', 0)
        
        # Create inline keyboard with options
        keyboard = []
        for option in mcq['options']:
            callback_data = f"answer_{option[0]}"  # Get A, B, C, or D
            keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Build plain text message (no HTML/Markdown to avoid parsing issues)
        question_text = (
            f"📝 Question {question_num + 1}/{len(quiz)}\n\n"
            f"{str(mcq['question'])}\n\n"
            f"Source: {str(mcq['source'])}"
        )
        
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    question_text, 
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    question_text, 
                    reply_markup=reply_markup
                )
        except BadRequest as e:
            logger.error(f"Error sending question: {e}")
            # Try to skip to next question
            error_msg = f"⚠️ Error displaying question {question_num + 1}. Skipping..."
            if update.callback_query:
                await update.callback_query.message.reply_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            # Move to next question
            self.quiz_manager.next_question(context)
            await self.send_question(update, context)
        except Exception as e:
            logger.error(f"Unexpected error sending question: {e}")
            error_msg = "❌ An error occurred. Please try /quiz again."
            if update.callback_query:
                await update.callback_query.message.reply_text(error_msg)
            else:
                await update.message.reply_text(error_msg)