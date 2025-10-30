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
        
    def get_quiz_buttons(self) -> InlineKeyboardMarkup:
        """Get standard quiz navigation buttons"""
        keyboard = [
            [
                InlineKeyboardButton("Next Question ➡️", callback_data='next_question'),
                InlineKeyboardButton("✏️ Edit", callback_data='edit_question'),
                InlineKeyboardButton("🛑 End Quiz", callback_data='end_quiz')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_final_buttons(self) -> InlineKeyboardMarkup:
        """Get buttons for final-question state (allow edit or finish)"""
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit", callback_data='edit_question'),
                InlineKeyboardButton("🛑 End Quiz", callback_data='end_quiz')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
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
            
        elif data == 'edit_question':
            await self.start_question_edit(update, context)
            
        # Edit flow callbacks: includes both `edit_...` and the answer selection `set_answer_X`
        elif data.startswith('edit_') or data.startswith('set_answer_'):
            await self.handle_edit_response(update, context)
            
        elif data == 'set_questions':
            await query.message.reply_text(BotMessages.SET_QUESTIONS_PROMPT)
            context.user_data['awaiting'] = 'questions'
        
        elif data == 'set_time':
            await query.message.reply_text(BotMessages.SET_TIME_PROMPT)
            context.user_data['awaiting'] = 'time'
            
        elif data == 'set_questions_per_chunk':
            await query.message.reply_text(BotMessages.SET_MIN_QUESTIONS_PROMPT)
            context.user_data['awaiting'] = 'min_questions'
            # Clear any previous temporary settings
            context.user_data.pop('temp_min_questions', None)
        
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
        
        elif data.startswith('custom_answer_'):
            # Handle custom question answer selection
            answer = data.split('_')[2]
            custom_qn = context.user_data.get('custom_qn_data', {})
            custom_qn['correct_answer'] = answer
            context.user_data['custom_qn_data'] = custom_qn
            
            await query.message.reply_text(
                f"✅ Correct answer set to: *{answer}*\n\n"
                "Finally, please provide an explanation for the correct answer:",
                parse_mode='Markdown'
            )
            context.user_data['custom_question_step'] = 'explanation'
                
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
            # Save reference to current question before moving to next
            current_mcq = self.quiz_manager.get_current_question(context)
            context.user_data['current_mcq'] = current_mcq
            self.quiz_manager.next_question(context)
            
            # Check if quiz is complete
            if self.quiz_manager.is_quiz_complete(context):
                # Show explanation then quiz summary
                # Escape special characters for markdown
                safe_explanation = result['explanation'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
                # Show explanation and allow editing or finishing the quiz
                await update.callback_query.message.reply_text(
                    BotMessages.CORRECT_ANSWER.format(explanation=safe_explanation),
                    reply_markup=self.get_final_buttons(),
                    parse_mode='Markdown'
                )
            else:
                # More questions remaining
                
                # Escape special characters for markdown
                safe_explanation = result['explanation'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
                await update.callback_query.message.reply_text(
                    BotMessages.CORRECT_ANSWER.format(explanation=safe_explanation), 
                    reply_markup=self.get_quiz_buttons(),
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
        # Save snapshot of this question so edits refer to the question the user just saw
        context.user_data['current_mcq'] = mcq
        
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
            # Show final quiz results
            await update.callback_query.message.reply_text(solution_text, parse_mode='Markdown')

            summary = self.quiz_manager.get_quiz_summary(context)
            result_text = BotMessages.QUIZ_COMPLETED.format(**summary)
            self.quiz_manager.end_quiz(context)

            await update.callback_query.message.reply_text(result_text, parse_mode='Markdown')
        else:
            # More questions remaining - show buttons
            await update.callback_query.message.reply_text(
                solution_text,
                reply_markup=self.get_quiz_buttons(),
                parse_mode='Markdown'
            )
    
    async def start_question_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the question editing process"""
        # Prefer the saved snapshot of the question the user just answered
        orig_mcq = context.user_data.get('current_mcq')
        if not orig_mcq:
            # Fallback to current question if no saved reference
            orig_mcq = self.quiz_manager.get_current_question(context)

        # Store a shallow copy/snapshot so we don't mutate the in-memory quiz list
        mcq = {
            'id': orig_mcq['id'],
            'question': orig_mcq['question'],
            'options': list(orig_mcq.get('options', [])),
            'correct_answer': orig_mcq.get('correct_answer'),
            'explanation': orig_mcq.get('explanation'),
            'source': orig_mcq.get('source')
        }
        context.user_data['editing_question'] = mcq
        context.user_data['editing_question_id'] = mcq['id']
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit", callback_data='edit_question_yes'),
                InlineKeyboardButton("🗑️ Delete", callback_data='edit_delete'),
                InlineKeyboardButton("❌ Cancel", callback_data='edit_question_no')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(
            BotMessages.EDIT_QUESTION_START.format(question=mcq['question']),
            reply_markup=reply_markup
        )
        
    async def handle_edit_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle responses during the question editing process"""
        query = update.callback_query
        data = query.data
        mcq = context.user_data.get('editing_question')
        
        if not mcq:
            await query.message.reply_text("Edit session expired. Please try again.")
            return
            
        if data == 'edit_question_yes':
            await query.message.reply_text(BotMessages.ENTER_NEW_QUESTION)
            context.user_data['awaiting_edit'] = 'question'
            
        elif data == 'edit_question_no':
            # Move to options edit
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='edit_options_yes'),
                    InlineKeyboardButton("No", callback_data='edit_options_no')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            options_text = "\n".join(mcq['options'])
            await query.message.reply_text(
                BotMessages.EDIT_OPTIONS_START.format(options=options_text),
                reply_markup=reply_markup
            )
        
        elif data == 'edit_delete':
            # Confirm deletion
            keyboard = [
                [
                    InlineKeyboardButton("✅ Delete", callback_data='edit_delete_confirm'),
                    InlineKeyboardButton("❌ Cancel", callback_data='edit_delete_cancel')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(BotMessages.CONFIRM_DELETE_QUESTION, reply_markup=reply_markup, parse_mode='Markdown')

        elif data == 'edit_delete_cancel':
            await query.message.reply_text(BotMessages.SKIP_EDIT)

        elif data == 'edit_delete_confirm':
            # Perform deletion
            user_id = update.effective_user.id
            question_id = mcq.get('id')
            success = self.db.delete_question(question_id, user_id)
            if success:
                # Remove from in-memory quiz list if present
                quiz = context.user_data.get('current_quiz', [])
                curr_idx = context.user_data.get('current_question', 0)
                removed_index = None
                for i, q in enumerate(quiz):
                    if q.get('id') == question_id:
                        removed_index = i
                        quiz.pop(i)
                        break
                # Adjust current_question index if necessary
                if removed_index is not None and removed_index <= curr_idx and curr_idx > 0:
                    context.user_data['current_question'] = curr_idx - 1

                await query.message.reply_text(BotMessages.QUESTION_DELETED)
            else:
                await query.message.reply_text("Failed to delete question. You may not own this question.")
            # Clear editing state
            context.user_data.pop('editing_question', None)
            context.user_data.pop('awaiting_edit', None)
            context.user_data.pop('editing_question_id', None)

            # After deletion, immediately go to the next question
            if self.command_handlers:
                await self.command_handlers.send_question(update, context)
            
        elif data == 'edit_options_yes':
            await query.message.reply_text(BotMessages.ENTER_NEW_OPTIONS)
            context.user_data['awaiting_edit'] = 'options'
            
        elif data == 'edit_options_no':
            # Move to answer edit
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='edit_answer_yes'),
                    InlineKeyboardButton("No", callback_data='edit_answer_no')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                BotMessages.EDIT_ANSWER_START.format(current_answer=mcq['correct_answer']),
                reply_markup=reply_markup
            )
            
        elif data == 'edit_answer_yes':
            keyboard = [
                [InlineKeyboardButton(opt[0], callback_data=f"set_answer_{opt[0]}") 
                 for opt in mcq['options']]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                BotMessages.SELECT_NEW_ANSWER,
                reply_markup=reply_markup
            )
            
        elif data == 'edit_answer_no':
            # Move to explanation edit
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='edit_explanation_yes'),
                    InlineKeyboardButton("No", callback_data='edit_explanation_no')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                BotMessages.EDIT_EXPLANATION_START.format(explanation=mcq['explanation']),
                reply_markup=reply_markup
            )
            
        elif data == 'edit_explanation_yes':
            await query.message.reply_text(BotMessages.ENTER_NEW_EXPLANATION)
            context.user_data['awaiting_edit'] = 'explanation'
            
        elif data == 'edit_explanation_no':
            # Complete the editing process
            await self.save_question_edits(update, context)
            
        elif data.startswith('set_answer_'):
            new_answer = data.split('_')[2]
            # Store in new_correct_answer, not the original correct_answer
            context.user_data['editing_question']['new_correct_answer'] = new_answer

            # Move to explanation edit
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='edit_explanation_yes'),
                    InlineKeyboardButton("No", callback_data='edit_explanation_no')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                BotMessages.EDIT_EXPLANATION_START.format(explanation=mcq['explanation']),
                reply_markup=reply_markup
            )

    async def save_question_edits(self, update: Update, context: ContextTypes.DEFAULT_TYPE, from_text: bool = False):
        """Save all accumulated question edits

        This updates the DB and then updates the in-memory copy of the quiz
        (context.user_data['current_quiz']) by matching question id so the
        displayed quiz items remain consistent.
        """
        mcq = context.user_data.get('editing_question')
        if mcq:
            user_id = update.effective_user.id
            # Prepare values to update (only include if provided)
            new_q = mcq.get('new_question')
            new_opts = mcq.get('new_options')
            new_correct = mcq.get('new_correct_answer')
            new_expl = mcq.get('new_explanation')

            success = self.db.update_question(
                mcq['id'],
                user_id,
                question=new_q,
                options=new_opts,
                correct_answer=new_correct,
                explanation=new_expl
            )

            if success:
                # Update any in-memory quiz list entries that match this id
                quiz = context.user_data.get('current_quiz', [])
                for i, q in enumerate(quiz):
                    try:
                        if q.get('id') == mcq['id']:
                            # replace only provided fields
                            if new_q is not None:
                                q['question'] = new_q
                            if new_opts is not None:
                                q['options'] = new_opts
                            if new_correct is not None:
                                q['correct_answer'] = new_correct
                            if new_expl is not None:
                                q['explanation'] = new_expl
                            # write back
                            quiz[i] = q
                    except Exception:
                        # be defensive; continue on error
                        continue

                # Reply to user
                if from_text or not update.callback_query:
                    await update.message.reply_text(
                        BotMessages.EDIT_COMPLETE
                    )
                else:
                    await update.callback_query.message.reply_text(
                        BotMessages.EDIT_COMPLETE
                    )

                # After successful edit, immediately send the next question
                if self.command_handlers:
                    await self.command_handlers.send_question(update, context)
            else:
                if from_text or not update.callback_query:
                    await update.message.reply_text("Failed to update question. Please try again.")
                else:
                    await update.callback_query.message.reply_text("Failed to update question. Please try again.")

        # Clear editing state
        context.user_data.pop('editing_question', None)
        context.user_data.pop('awaiting_edit', None)
        context.user_data.pop('editing_question_id', None)