from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.queries import DatabaseQueries
from services.quiz_manager import QuizManager
from messages import BotMessages
import config

class CallbackHandlers:
    """Handle callback queries from inline keyboards"""
    
    def __init__(self, db_queries: DatabaseQueries, quiz_manager: QuizManager, 
                 command_handlers):
        self.db = db_queries
        self.quiz_manager = quiz_manager
        self.command_handlers = command_handlers
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main callback handler"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Route to appropriate handler
        if data == 'close':
            await query.message.delete()
        
        elif data.startswith('answer_'):
            user_answer = data.split('_')[1]
            await self.handle_answer(update, context, user_answer)
        
        elif data == 'retry':
            await self.command_handlers.send_question(update, context)
        
        elif data == 'show_solution':
            await self.show_solution(update, context)
        
        elif data == 'next_question':
            # Don't call next_question here - already called in handle_answer/show_solution
            await self.command_handlers.send_question(update, context)
        
        elif data == 'set_questions':
            await query.message.reply_text(BotMessages.SET_QUESTIONS_PROMPT)
            context.user_data['awaiting'] = 'questions'
        
        elif data == 'set_time':
            await query.message.reply_text(BotMessages.SET_TIME_PROMPT)
            context.user_data['awaiting'] = 'time'
        
        elif data == 'confirm_clear_knowledge':
            user_id = update.effective_user.id
            self.db.clear_user_knowledge(user_id)
            # Edit the existing message instead of creating a new one
            await query.edit_message_text(BotMessages.KNOWLEDGE_CLEARED)
        
        elif data == 'confirm_clear_questions':
            user_id = update.effective_user.id
            self.db.clear_user_questions(user_id)
            # Edit the existing message instead of creating a new one
            await query.edit_message_text(BotMessages.QUESTIONS_CLEARED)
        
        elif data == 'end_quiz':
            # User wants to end quiz early
            progress = self.quiz_manager.get_quiz_progress(context)
            result_text = BotMessages.QUIZ_ENDED_EARLY.format(**progress)
            
            # Clear quiz state
            self.quiz_manager.end_quiz(context)
            
            await query.message.reply_text(result_text, parse_mode='Markdown')
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          user_answer: str):
        """Handle user's answer to quiz question"""
        user_id = update.effective_user.id
        result = self.quiz_manager.process_answer(user_id, user_answer, context)
        
        if result['is_correct']:
            # Correct answer - move to next question immediately
            self.quiz_manager.next_question(context)
            
            # Check if quiz is complete
            if self.quiz_manager.is_quiz_complete(context):
                # Show explanation then quiz summary
                # Escape special characters for markdown
                safe_explanation = result['explanation'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
                await update.callback_query.message.reply_text(
                    BotMessages.CORRECT_ANSWER.format(explanation=safe_explanation),
                    parse_mode='Markdown'
                )
                
                # Show final quiz results
                summary = self.quiz_manager.get_quiz_summary(context)
                result_text = BotMessages.QUIZ_COMPLETED.format(**summary)
                self.quiz_manager.end_quiz(context)
                
                await update.callback_query.message.reply_text(result_text, parse_mode='Markdown')
            else:
                # More questions remaining - show next question button and end quiz button
                keyboard = [
                    [
                        InlineKeyboardButton("Next Question ➡️", callback_data='next_question'),
                        InlineKeyboardButton("🛑 End Quiz", callback_data='end_quiz')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Escape special characters for markdown
                safe_explanation = result['explanation'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
                await update.callback_query.message.reply_text(
                    BotMessages.CORRECT_ANSWER.format(explanation=safe_explanation), 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        else:
            # Wrong answer
            keyboard = [
                [InlineKeyboardButton("🔄 Retry", callback_data='retry')],
                [InlineKeyboardButton("💡 Show Solution", callback_data='show_solution')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = BotMessages.INCORRECT_ANSWER.format(user_answer=user_answer)
            
            await update.callback_query.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def show_solution(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show solution for current question"""
        mcq = self.quiz_manager.get_current_question(context)
        
        # Escape special characters in explanation for markdown
        safe_explanation = mcq['explanation'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        
        solution_text = BotMessages.SOLUTION.format(
            correct_answer=mcq['correct_answer'],
            explanation=safe_explanation
        )
        
        # Move to next question
        self.quiz_manager.next_question(context)
        
        # Check if quiz is complete
        if self.quiz_manager.is_quiz_complete(context):
            # Show solution then quiz summary
            await update.callback_query.message.reply_text(
                solution_text,
                parse_mode='Markdown'
            )
            
            # Show final quiz results
            summary = self.quiz_manager.get_quiz_summary(context)
            result_text = BotMessages.QUIZ_COMPLETED.format(**summary)
            self.quiz_manager.end_quiz(context)
            
            await update.callback_query.message.reply_text(result_text, parse_mode='Markdown')
        else:
            # More questions remaining - show next question button and end quiz button
            keyboard = [
                [
                    InlineKeyboardButton("Next Question ➡️", callback_data='next_question'),
                    InlineKeyboardButton("🛑 End Quiz", callback_data='end_quiz')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                solution_text, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
