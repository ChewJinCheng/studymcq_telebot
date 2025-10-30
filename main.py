from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters, 
    ContextTypes
)
from datetime import time

# Import all modules
import config
from database.models import Database
from database.queries import DatabaseQueries
from services.document_processor import DocumentProcessor
from services.mcq_generator import MCQGenerator
from services.quiz_manager import QuizManager
from handlers.commands import CommandHandlers
from handlers.callbacks import CallbackHandlers
from handlers.messages import MessageHandlers
from utils.logger import setup_logger
from messages import BotMessages

logger = setup_logger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        "❌ Unknown command. Here's what I can do:",
        parse_mode='Markdown'
    )
    await update.message.reply_text(BotMessages.WELCOME_MESSAGE, parse_mode='Markdown')

async def send_daily_quiz(context: ContextTypes.DEFAULT_TYPE, db_queries: DatabaseQueries):
    """Send daily quiz to users at their scheduled time"""
    conn = db_queries._get_connection()
    c = conn.cursor()
    
    # Get all users (in real implementation, filter by current time and timezone)
    c.execute('SELECT user_id, daily_questions FROM users')
    users = c.fetchall()
    conn.close()
    
    for user_id, num_questions in users:
        try:
            question_count = db_queries.get_question_count(user_id)
            
            if question_count == 0:
                continue
            
            # Send notification
            await context.bot.send_message(
                chat_id=user_id,
                text=BotMessages.DAILY_QUIZ_NOTIFICATION
            )
        except Exception as e:
            logger.error(f"Error sending daily quiz to {user_id}: {e}")


def main():
    """Main entry point"""
    # Initialize database
    db = Database(config.DB_NAME)
    db.init_db()
    
    # Initialize services
    db_queries = DatabaseQueries(config.DB_NAME)
    doc_processor = DocumentProcessor()
    mcq_generator = MCQGenerator(config.GROQ_API_KEY)
    quiz_manager = QuizManager(db_queries)
    
    # Initialize handlers
    command_handlers = CommandHandlers(db_queries, quiz_manager)
    callback_handlers = CallbackHandlers(db_queries, quiz_manager, command_handlers)
    message_handlers = MessageHandlers(db_queries, doc_processor, mcq_generator, quiz_manager)
    
    # Set command_handlers reference in message_handlers (for quiz flow)
    message_handlers.set_command_handlers(command_handlers)
    message_handlers.set_callback_handlers(callback_handlers)

    # Create application
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # Register command handlers (order matters - specific before general)
    app.add_handler(CommandHandler('start', command_handlers.start_command))
    app.add_handler(CommandHandler('help', command_handlers.help_command))
    app.add_handler(CommandHandler('upload', command_handlers.upload_command))
    app.add_handler(CommandHandler('quiz', command_handlers.quiz_command))
    app.add_handler(CommandHandler('settings', command_handlers.settings_command))
    app.add_handler(CommandHandler('stats', command_handlers.stats_command))
    app.add_handler(CommandHandler('bank', command_handlers.bank_command))
    app.add_handler(CommandHandler('clear_knowledge', command_handlers.clear_knowledge_command))
    app.add_handler(CommandHandler('clear_questions', command_handlers.clear_questions_command))
    
    # Register message handlers (only when in upload mode or awaiting input)
    app.add_handler(MessageHandler(filters.Document.ALL, message_handlers.handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text))
    
    # Register callback handler
    app.add_handler(CallbackQueryHandler(callback_handlers.button_callback))
    
    # Handle unknown commands (must be last)
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Register error handler
    app.add_error_handler(error_handler)
    
    # Add daily quiz job (example: runs every day at a specific time)
    # Note: This is a simplified example. Real implementation would check user timezones
    # job_queue = app.job_queue
    # job_queue.run_daily(
    #     lambda ctx: send_daily_quiz(ctx, db_queries), 
    #     time=time(hour=9, minute=0)
    # )
    
    # Start bot
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()