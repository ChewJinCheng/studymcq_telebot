from telegram import Update
from telegram.ext import ContextTypes
from database.queries import DatabaseQueries
from services.document_processor import DocumentProcessor
from services.mcq_generator import MCQGenerator
from services.quiz_manager import QuizManager
from utils.text_chunking import chunk_text
from messages import BotMessages
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)

class MessageHandlers:
    """Handle text and document messages"""
    
    def __init__(self, db_queries: DatabaseQueries, 
                 document_processor: DocumentProcessor,
                 mcq_generator: MCQGenerator,
                 quiz_manager: QuizManager,
                 command_handlers=None):
        self.db = db_queries
        self.doc_processor = document_processor
        self.mcq_generator = mcq_generator
        self.quiz_manager = quiz_manager
        self.command_handlers = command_handlers
    
    def set_command_handlers(self, command_handlers):
        """Set command handlers reference (to avoid circular dependency)"""
        self.command_handlers = command_handlers
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        user_id = update.effective_user.id
        
        # Check if user is in upload mode
        if not context.user_data.get('upload_mode'):
            await update.message.reply_text(
                "📄 To upload documents, please use the /upload command first.\n\n"
                "Type /upload to enable document upload mode."
            )
            return
        
        document = update.message.document
        
        await update.message.reply_text(BotMessages.PROCESSING_DOCUMENT)
        
        try:
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Extract text and save to knowledge base
            if document.file_name.endswith('.pdf'):
                # Get full text for knowledge base
                text = self.doc_processor.extract_text_from_pdf(bytes(file_bytes))
                self.db.save_knowledge(user_id, text, document.file_name)
                
                await update.message.reply_text(BotMessages.DOCUMENT_SAVED)
                
                # Generate questions using word-based chunking (same as DOCX/TXT)
                total_q = await self.process_and_generate_questions(
                    user_id, text, document.file_name, update
                )
                
            elif document.file_name.endswith('.docx'):
                text = self.doc_processor.extract_text_from_docx(bytes(file_bytes))
                self.db.save_knowledge(user_id, text, document.file_name)
                
                await update.message.reply_text(BotMessages.DOCUMENT_SAVED)
                
                total_q = await self.process_and_generate_questions(
                    user_id, text, document.file_name, update
                )
                
            elif document.file_name.endswith('.txt'):
                text = self.doc_processor.extract_text_from_txt(bytes(file_bytes))
                self.db.save_knowledge(user_id, text, document.file_name)
                
                await update.message.reply_text(BotMessages.TEXT_SAVED)
                
                total_q = await self.process_and_generate_questions(
                    user_id, text, document.file_name, update
                )
                
            else:
                await update.message.reply_text(BotMessages.UNSUPPORTED_FORMAT)
                return
            
            safe_filename = document.file_name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
            await update.message.reply_text(
                BotMessages.GENERATION_COMPLETE.format(
                    count=total_q,
                    source=safe_filename
                ),
                parse_mode='Markdown'
            )
            
            # Clear upload mode after successful upload
            context.user_data.pop('upload_mode', None)
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await update.message.reply_text(BotMessages.PROCESSING_ERROR)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if we're awaiting quiz count input
        if context.user_data.get('awaiting_quiz_count'):
            await self.handle_quiz_count_input(update, context, text, user_id)
            return
        
        # Check if we're awaiting settings input
        awaiting = context.user_data.get('awaiting')
        
        if awaiting == 'questions':
            await self.handle_questions_input(update, context, text, user_id)
            return
        
        if awaiting == 'time':
            await self.handle_time_input(update, context, text, user_id)
            return
        
        # Check if user is in upload mode
        if not context.user_data.get('upload_mode'):
            await update.message.reply_text(
                "💬 To upload text for quiz generation, please use the /upload command first.\n\n"
                "Type /upload to enable upload mode, or use /help to see all available commands."
            )
            return
        
        # Save text to knowledge base
        self.db.save_knowledge(user_id, text, "Text message")
        
        await update.message.reply_text(BotMessages.DOCUMENT_SAVED)
        
        # Generate questions from text
        total_q = await self.process_and_generate_questions(
            user_id, text, "Text message", update
        )
        
        await update.message.reply_text(
            BotMessages.TEXT_QUESTIONS_COMPLETE.format(count=total_q),
            parse_mode='Markdown'
        )
        
        # Clear upload mode after successful upload
        context.user_data.pop('upload_mode', None)
    
    async def handle_quiz_count_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     text: str, user_id: int):
        """Handle quiz question count input"""
        question_count = self.db.get_question_count(user_id)
        
        try:
            num = int(text)
            if 1 <= num <= question_count:
                # Clear the flag
                context.user_data.pop('awaiting_quiz_count', None)
                
                # Start quiz with specified number
                success, mcqs, message = self.quiz_manager.start_quiz(user_id, num, context)
                
                await update.message.reply_text(message)
                
                if success:
                    # Send first question
                    await self.command_handlers.send_question(update, context)
            else:
                await update.message.reply_text(
                    BotMessages.INVALID_QUIZ_COUNT.format(total=question_count)
                )
        except ValueError:
            await update.message.reply_text(
                BotMessages.INVALID_QUIZ_COUNT.format(total=question_count)
            )
    
    async def handle_questions_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    text: str, user_id: int):
        """Handle daily questions count input"""
        try:
            num = int(text)
            if config.MIN_DAILY_QUESTIONS <= num <= config.MAX_DAILY_QUESTIONS:
                self.db.save_user_settings(
                    user_id, 
                    update.effective_user.username, 
                    daily_questions=num
                )
                await update.message.reply_text(
                    BotMessages.QUESTIONS_SET.format(num=num)
                )
                context.user_data.pop('awaiting', None)
            else:
                await update.message.reply_text(BotMessages.INVALID_NUMBER)
        except ValueError:
            await update.message.reply_text(BotMessages.INVALID_NUMBER_FORMAT)
    
    async def handle_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               text: str, user_id: int):
        """Handle quiz time input"""
        if len(text) == 5 and text[2] == ':':
            self.db.save_user_settings(
                user_id, 
                update.effective_user.username, 
                quiz_time=text
            )
            await update.message.reply_text(
                BotMessages.TIME_SET.format(time=text)
            )
            context.user_data.pop('awaiting', None)
        else:
            await update.message.reply_text(BotMessages.INVALID_TIME_FORMAT)
    
    async def process_and_generate_questions(self, user_id: int, content: str, 
                                            source: str, update: Update, 
                                            chunks: list = None):
        """Process content, generate questions, and save to database"""
        
        if chunks is None:
            # Chunk by words for text content
            chunks = [
                (f"Chunk {i+1}", chunk) 
                for i, chunk in enumerate(chunk_text(content, config.CHUNK_SIZE_WORDS))
            ]
        
        total_questions = 0
        
        for chunk_name, chunk_content in chunks:
            # Generate 3-5 questions per chunk
            num_q = min(
                config.MAX_QUESTIONS_PER_CHUNK, 
                max(
                    config.DEFAULT_QUESTIONS_PER_CHUNK, 
                    len(chunk_content.split()) // config.CONTENT_WORDS_PER_QUESTION
                )
            )
            
            
            mcqs = self.mcq_generator.generate_mcqs_from_chunk(chunk_content, num_q)
            
            # Save each question to database
            for mcq in mcqs:
                self.db.save_question(
                    user_id,
                    mcq['question'],
                    mcq['options'],
                    mcq['correct_answer'],
                    mcq['explanation'],
                    f"{source} - {chunk_name}"
                )
                total_questions += 1
        
        return total_questions