from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
                command_handlers=None,
                callback_handlers=None):
        self.db = db_queries
        self.doc_processor = document_processor
        self.mcq_generator = mcq_generator
        self.quiz_manager = quiz_manager
        self.command_handlers = command_handlers
        self.callback_handlers = callback_handlers

    def set_command_handlers(self, command_handlers):
        """Set command handlers reference (to avoid circular dependency)"""
        self.command_handlers = command_handlers

    def set_callback_handlers(self, callback_handlers):
        """Set callback handlers reference (to avoid circular dependency)"""
        self.callback_handlers = callback_handlers
    
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
            
        if awaiting == 'min_questions':
            await self.handle_min_questions_input(update, context, text, user_id)
            return
            
        if awaiting == 'max_questions':
            await self.handle_max_questions_input(update, context, text, user_id)
            return
            
        # Check if we're awaiting question edits
        awaiting_edit = context.user_data.get('awaiting_edit')
        if awaiting_edit:
            await self.handle_question_edit_input(update, context, text, awaiting_edit)
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
            
    async def handle_min_questions_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       text: str, user_id: int):
        """Handle minimum questions per chunk input"""
        try:
            num = int(text)
            if num > 0:  # Only check if positive
                # Store minimum temporarily in user_data
                context.user_data['temp_min_questions'] = num
                # Ask for maximum
                await update.message.reply_text(
                    BotMessages.SET_MAX_QUESTIONS_PROMPT.format(min_q=num)
                )
                context.user_data['awaiting'] = 'max_questions'
            else:
                await update.message.reply_text(BotMessages.INVALID_MIN_QUESTIONS)
        except ValueError:
            await update.message.reply_text(BotMessages.INVALID_NUMBER_FORMAT)
            
    async def handle_max_questions_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       text: str, user_id: int):
        """Handle maximum questions per chunk input"""
        try:
            num = int(text)
            min_q = context.user_data.get('temp_min_questions')  # Get the temp min value
            
            if not min_q:
                # Something went wrong, start over
                await update.message.reply_text(BotMessages.SET_MIN_QUESTIONS_PROMPT)
                context.user_data['awaiting'] = 'min_questions'
                return
            
            if num >= min_q:
                # Save both min and max together
                self.db.save_user_settings(
                    user_id,
                    update.effective_user.username,
                    min_questions=min_q,  # Save the temp min value
                    max_questions=num
                )
                await update.message.reply_text(
                    BotMessages.QUESTIONS_PER_CHUNK_SET.format(min_q=min_q, max_q=num)
                )
                # Clear temporary data and awaiting state
                context.user_data.pop('awaiting', None)
                context.user_data.pop('temp_min_questions', None)
            else:
                await update.message.reply_text(
                    BotMessages.INVALID_MAX_QUESTIONS.format(min_q=min_q)
                )
        except ValueError:
            await update.message.reply_text(BotMessages.INVALID_NUMBER_FORMAT)
            
    async def handle_question_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       text: str, edit_type: str):
        """Handle input for question editing"""
        mcq = context.user_data.get('editing_question')
        if not mcq:
            await update.message.reply_text("Edit session expired. Please try again.")
            return
            
        if edit_type == 'question':
            mcq['new_question'] = text
            # Move to options edit
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='edit_options_yes'),
                    InlineKeyboardButton("No", callback_data='edit_options_no')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            options_text = "\n".join(mcq['options'])
            await update.message.reply_text(
                BotMessages.EDIT_OPTIONS_START.format(options=options_text),
                reply_markup=reply_markup
            )
            
        elif edit_type == 'options':
            # Validate options format
            lines = text.strip().split('\n')
            if len(lines) != 4:
                await update.message.reply_text(BotMessages.INVALID_OPTIONS_FORMAT)
                return
            
            cleaned_options = []
            expected_labels = ['A', 'B', 'C', 'D']
            found_labels = []

            for line in lines:
                line = line.strip()
                if not line:
                    await update.message.reply_text(BotMessages.INVALID_OPTIONS_FORMAT)
                    return
                
                # Find A, B, C, or D (case-insensitive) in the line
                label_found = None
                label_pos = -1
                
                for label in expected_labels:
                    # Search for the label (case-insensitive)
                    pos = line.upper().find(label)
                    if pos != -1:
                        label_found = label
                        label_pos = pos
                        break
                
                if not label_found:
                    await update.message.reply_text(BotMessages.INVALID_OPTIONS_FORMAT)
                    return
                
                # Check for duplicate labels
                if label_found in found_labels:
                    await update.message.reply_text(BotMessages.INVALID_OPTIONS_FORMAT)
                    return
                
                found_labels.append(label_found)
                
                # Extract the text after the label and any separator
                # Start from position after the label
                text_after_label = line[label_pos + 1:].strip()
                
                # Remove common separators at the start if present
                if text_after_label and text_after_label[0] in (')', '-', '.', ':', ']', ','):
                    text_after_label = text_after_label[1:].strip()
                
                if not text_after_label:
                    await update.message.reply_text(BotMessages.INVALID_OPTIONS_FORMAT)
                    return
                
                # Store in standardized A) format with the label
                cleaned_options.append((label_found, f"{label_found}) {text_after_label}"))
            
            # Verify all labels A, B, C, D were found
            if sorted(found_labels) != expected_labels:
                await update.message.reply_text(BotMessages.INVALID_OPTIONS_FORMAT)
                return
            
            # Sort options to ensure A, B, C, D order
            cleaned_options.sort(key=lambda x: x[0])
            cleaned_options = [opt[1] for opt in cleaned_options]
            
            mcq['new_options'] = cleaned_options
            # Move to answer edit
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='edit_answer_yes'),
                    InlineKeyboardButton("No", callback_data='edit_answer_no')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                BotMessages.EDIT_ANSWER_START.format(current_answer=mcq['correct_answer']),
                reply_markup=reply_markup
            )
            
        elif edit_type == 'explanation':
            mcq['new_explanation'] = text
            # Complete the editing process
            # The save logic lives in the callback handlers (edit flow). Call it
            # via the callback_handlers reference so the same save path is used
            # for both callback-driven and text-driven edits.
            if self.callback_handlers:
                await self.callback_handlers.save_question_edits(update, context, from_text=True)
            else:
                # Fallback: try quiz_manager (older code paths), but normally
                # callback_handlers should be present.
                try:
                    await self.quiz_manager.save_question_edits(update, context)
                except Exception:
                    await update.message.reply_text("Failed to save edits: handler not available.")
            
        context.user_data.pop('awaiting_edit', None)
    
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
            # Get user's question generation settings
            settings = self.db.get_user_settings(user_id)
            min_q = settings['min_questions_per_chunk']
            max_q = settings['max_questions_per_chunk']
            
            # Let the LLM decide how many questions to generate within the min-max range
            mcqs = self.mcq_generator.generate_mcqs_from_chunk(
                chunk_content, 
                min_questions=min_q,
                max_questions=max_q
            )
            
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