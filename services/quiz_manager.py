from typing import List, Dict
from telegram import Update
from telegram.ext import ContextTypes
from database.queries import DatabaseQueries
from messages import BotMessages

class QuizManager:
    """Manage quiz flow and state"""
    
    def __init__(self, db_queries: DatabaseQueries):
        self.db = db_queries
    
    def start_quiz(self, user_id: int, num_questions: int, context: ContextTypes.DEFAULT_TYPE) -> tuple:
        """
        Start a new quiz for user with specified number of questions
        Returns: (success: bool, mcqs: List[Dict], message: str)
        """
        question_count = self.db.get_question_count(user_id)
        
        if question_count == 0:
            return False, [], BotMessages.EMPTY_BANK_ERROR
        
        if num_questions < 1 or num_questions > question_count:
            return False, [], BotMessages.INVALID_QUIZ_COUNT.format(total=question_count)
        
        # Get random questions from bank
        mcqs = self.db.get_random_questions(user_id, num_questions)
        
        if not mcqs:
            return False, [], BotMessages.QUIZ_LOAD_ERROR
        
        # Initialize quiz state
        context.user_data['current_quiz'] = mcqs
        context.user_data['current_question'] = 0
        context.user_data['score'] = 0
        
        message = BotMessages.QUIZ_START.format(num=len(mcqs))
        return True, mcqs, message
    
    def get_current_question(self, context: ContextTypes.DEFAULT_TYPE) -> Dict:
        """Get current question from quiz state"""
        quiz = context.user_data.get('current_quiz', [])
        question_num = context.user_data.get('current_question', 0)
        
        if question_num < len(quiz):
            return quiz[question_num]
        return None
    
    def is_quiz_complete(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if quiz is completed"""
        quiz = context.user_data.get('current_quiz', [])
        question_num = context.user_data.get('current_question', 0)
        return question_num >= len(quiz)
    
    def process_answer(self, user_id: int, user_answer: str, 
                      context: ContextTypes.DEFAULT_TYPE) -> Dict:
        """
        Process user's answer
        Returns dict with: is_correct, score_updated, explanation
        """
        mcq = self.get_current_question(context)
        if not mcq:
            return None
        
        correct_answer = mcq['correct_answer']
        is_correct = user_answer == correct_answer
        
        # Save result to database
        self.db.save_quiz_result(user_id, mcq['id'], user_answer, is_correct)
        
        # Update question statistics
        self.db.update_question_stats(mcq['id'], is_correct)
        
        # Update score if correct
        if is_correct:
            context.user_data['score'] = context.user_data.get('score', 0) + 1
        
        return {
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': mcq['explanation']
        }
    
    def next_question(self, context: ContextTypes.DEFAULT_TYPE):
        """Move to next question"""
        context.user_data['current_question'] = context.user_data.get('current_question', 0) + 1
    
    def get_quiz_summary(self, context: ContextTypes.DEFAULT_TYPE) -> Dict:
        """Get quiz completion summary"""
        score = context.user_data.get('score', 0)
        quiz = context.user_data.get('current_quiz', [])
        total = len(quiz)
        percentage = (score / total * 100) if total > 0 else 0
        
        return {
            'score': score,
            'total': total,
            'percentage': percentage
        }
    
    def get_quiz_progress(self, context: ContextTypes.DEFAULT_TYPE) -> Dict:
        """Get current quiz progress (for early end)"""
        score = context.user_data.get('score', 0)
        quiz = context.user_data.get('current_quiz', [])
        answered = context.user_data.get('current_question', 0)
        total = len(quiz)
        percentage = (score / answered * 100) if answered > 0 else 0
        
        return {
            'score': score,
            'answered': answered,
            'total': total,
            'percentage': percentage
        }
    
    def end_quiz(self, context: ContextTypes.DEFAULT_TYPE):
        """Clear quiz state"""
        context.user_data.pop('current_quiz', None)
        context.user_data.pop('current_question', None)
        context.user_data.pop('score', None)
        context.user_data.pop('awaiting_quiz_count', None)