import json
from typing import Dict, List, Optional
import sqlite3
import random
import config

class DatabaseQueries:
    """Database query operations"""
    
    def __init__(self, db_name: str = config.DB_NAME):
        self.db_name = db_name
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_name)
    
    # User Settings
    def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings"""
        conn = self._get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''SELECT daily_questions, quiz_time, 
                        min_questions_per_chunk, max_questions_per_chunk 
                        FROM users WHERE user_id = ?''', (user_id,))
            result = c.fetchone()
            
            if result:
                return {
                    'daily_questions': result[0],
                    'quiz_time': result[1],
                    'min_questions_per_chunk': result[2] if result[2] is not None else config.DEFAULT_QUESTIONS_PER_CHUNK,
                    'max_questions_per_chunk': result[3] if result[3] is not None else config.MAX_QUESTIONS_PER_CHUNK
                }
        except sqlite3.OperationalError:
            c.execute('SELECT daily_questions, quiz_time FROM users WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            
            if result:
                return {
                    'daily_questions': result[0],
                    'quiz_time': result[1],
                    'min_questions_per_chunk': config.DEFAULT_QUESTIONS_PER_CHUNK,
                    'max_questions_per_chunk': config.MAX_QUESTIONS_PER_CHUNK
                }
        
        finally:
            conn.close()
        
        # Default values for new users
        return {
            'daily_questions': config.DEFAULT_DAILY_QUESTIONS,
            'quiz_time': config.DEFAULT_QUIZ_TIME,
            'min_questions_per_chunk': config.DEFAULT_QUESTIONS_PER_CHUNK,
            'max_questions_per_chunk': config.MAX_QUESTIONS_PER_CHUNK
        }
    
    def save_user_settings(self, user_id: int, username: str, 
                          daily_questions: Optional[int] = None, 
                          quiz_time: Optional[str] = None,
                          min_questions: Optional[int] = None,
                          max_questions: Optional[int] = None):
        """Save or update user settings"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                  (user_id, username))
        
        if daily_questions is not None:
            c.execute('UPDATE users SET daily_questions = ? WHERE user_id = ?', 
                      (daily_questions, user_id))
        if quiz_time is not None:
            c.execute('UPDATE users SET quiz_time = ? WHERE user_id = ?', 
                      (quiz_time, user_id))
        if min_questions is not None:
            c.execute('UPDATE users SET min_questions_per_chunk = ? WHERE user_id = ?',
                      (min_questions, user_id))
        if max_questions is not None:
            c.execute('UPDATE users SET max_questions_per_chunk = ? WHERE user_id = ?',
                      (max_questions, user_id))
        
        conn.commit()
        conn.close()
    
    # Knowledge Base
    def save_knowledge(self, user_id: int, content: str, source: str):
        """Save content to knowledge base"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO knowledge_base (user_id, content, source) VALUES (?, ?, ?)', 
                  (user_id, content, source))
        conn.commit()
        conn.close()
    
    def clear_user_knowledge(self, user_id: int):
        """Clear user's knowledge base"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM knowledge_base WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    # Question Bank
    def save_question(self, user_id: int, question: str, options: List[str], 
                     correct_answer: str, explanation: str, source: str):
        """Save a question to the question bank"""
        def clean_text(text):
            """Clean text before storing in database"""
            if not isinstance(text, str):
                text = str(text)
            text = text.replace('\n', ' ')
            text = ' '.join(text.split())
            return text.strip()
        
        # Clean all text fields
        question = clean_text(question)
        options = [clean_text(opt) for opt in options]
        explanation = clean_text(explanation)
        source = clean_text(source)
        
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO question_bank 
                     (user_id, question, options, correct_answer, explanation, source, accuracy) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, question, json.dumps(options), correct_answer, explanation, source, 0.0))
        conn.commit()
        conn.close()
    
    def get_random_questions(self, user_id: int, num_questions: int) -> List[Dict]:
        """Get random questions from question bank with weighted selection based on accuracy
        
        Lower accuracy questions appear more frequently to help user improve weak areas.
        Weight formula:
        - Never attempted (times_asked = 0): weight = 0.6 (neutral)
        - Low accuracy: weight = 1.0 - accuracy + 0.2 (ranges from 0.2 to 1.2)
        - This gives lower accuracy questions higher probability of selection
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        # Get all questions with their accuracy
        c.execute('''SELECT id, question, options, correct_answer, explanation, source, 
                     times_asked, accuracy
                     FROM question_bank WHERE user_id = ?''', 
                  (user_id,))
        all_questions = c.fetchall()
        conn.close()
        
        if not all_questions:
            return []
        
        # Calculate weights for each question
        questions_with_weights = []
        for row in all_questions:
            question_id, question, options, correct_answer, explanation, source, times_asked, accuracy = row
            
            # Calculate weight
            if times_asked == 0:
                # Never attempted - neutral weight
                weight = 0.6
            else:
                # Inverse accuracy weighting: lower accuracy = higher weight
                # Weight ranges from 0.2 (high accuracy) to 1.2 (low accuracy)
                weight = 1.0 - accuracy + 0.2
            
            questions_with_weights.append({
                'id': question_id,
                'question': question,
                'options': json.loads(options),
                'correct_answer': correct_answer,
                'explanation': explanation,
                'source': source,
                'weight': weight
            })
        
        # If have fewer questions than requested, return all
        if len(questions_with_weights) <= num_questions:
            return [q for q in questions_with_weights]
        
        # Weighted random selection without replacement
        weights = [q['weight'] for q in questions_with_weights]
        selected_questions = random.choices(
            questions_with_weights, 
            weights=weights, 
            k=min(num_questions, len(questions_with_weights))
        )
        
        # Remove weight field before returning
        for q in selected_questions:
            q.pop('weight', None)
        
        return selected_questions
    
    def get_question_count(self, user_id: int) -> int:
        """Get total question count for user"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM question_bank WHERE user_id = ?', (user_id,))
        count = c.fetchone()[0]
        conn.close()
        return count
    
    def clear_user_questions(self, user_id: int):
        """Clear user's question bank"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM question_bank WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def update_question_stats(self, question_id: int, is_correct: bool):
        """Update question statistics and recalculate accuracy"""
        conn = self._get_connection()
        c = conn.cursor()
        
        if is_correct:
            c.execute('''UPDATE question_bank 
                         SET times_asked = times_asked + 1, 
                             times_correct = times_correct + 1,
                             accuracy = CAST(times_correct + 1 AS REAL) / (times_asked + 1)
                         WHERE id = ?''', (question_id,))
        else:
            c.execute('''UPDATE question_bank 
                         SET times_asked = times_asked + 1,
                             accuracy = CAST(times_correct AS REAL) / (times_asked + 1)
                         WHERE id = ?''', (question_id,))
        
        conn.commit()
        conn.close()
    
    def get_question_bank_stats(self, user_id: int) -> Dict:
        """Get question bank statistics"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT 
                        COUNT(DISTINCT source),
                        AVG(times_asked),
                        SUM(times_correct) * 1.0 / NULLIF(SUM(times_asked), 0) * 100
                     FROM question_bank WHERE user_id = ?''', (user_id,))
        sources, avg_asked, accuracy = c.fetchone()
        
        conn.close()
        
        return {
            'sources': sources or 0,
            'avg_asked': avg_asked or 0,
            'accuracy': accuracy or 0
        }
    
    # Quiz History
    def save_quiz_result(self, user_id: int, question_id: int, 
                        user_answer: str, is_correct: bool):
        """Save quiz result"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO quiz_history 
                     (user_id, question_id, user_answer, is_correct) 
                     VALUES (?, ?, ?, ?)''',
                  (user_id, question_id, user_answer, is_correct))
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*), SUM(is_correct) FROM quiz_history WHERE user_id = ?', 
                  (user_id,))
        total, correct = c.fetchone()
        
        conn.close()
        
        return {
            'total': total or 0,
            'correct': correct or 0
        }
    
    def update_question(self, question_id: int, user_id: int, 
                   question: str = None, options: List[str] = None,
                   correct_answer: str = None, explanation: str = None) -> bool:
        """Update a question in the question bank and reset accuracy to 0"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # Verify the question belongs to the user
        c.execute('SELECT id FROM question_bank WHERE id = ? AND user_id = ?', 
                (question_id, user_id))
        if not c.fetchone():
            conn.close()
            return False
            
        updates = []
        params = []
        
        if question is not None:
            updates.append('question = ?')
            params.append(question)
        if options is not None:
            updates.append('options = ?')
            params.append(json.dumps(options))
        if correct_answer is not None:
            updates.append('correct_answer = ?')
            params.append(correct_answer)
        if explanation is not None:
            updates.append('explanation = ?')
            params.append(explanation)
        
        # Always reset accuracy when editing
        updates.append('accuracy = ?')
        params.append(0.0)
        updates.append('times_asked = ?')
        params.append(0)
        updates.append('times_correct = ?')
        params.append(0)
            
        if updates:
            query = f'''UPDATE question_bank 
                    SET {', '.join(updates)}
                    WHERE id = ? AND user_id = ?'''
            params.extend([question_id, user_id])
            c.execute(query, params)
            conn.commit()
            
            # Verify the update by reading it back
            c.execute('''SELECT question, options, correct_answer, explanation 
                        FROM question_bank WHERE id = ? AND user_id = ?''',
                    (question_id, user_id))
            result = c.fetchone()
            if result:
                print(f"✓ Question {question_id} updated successfully:")
                print(f"  Question: {result[0][:50]}...")
                print(f"  Answer: {result[2]}")
                print(f"  Accuracy reset to 0.0")
            
        conn.close()
        return True

    def delete_question(self, question_id: int, user_id: int) -> bool:
        """Delete a single question belonging to a user"""
        conn = self._get_connection()
        c = conn.cursor()
        # Verify ownership
        c.execute('SELECT id FROM question_bank WHERE id = ? AND user_id = ?', (question_id, user_id))
        if not c.fetchone():
            conn.close()
            return False

        c.execute('DELETE FROM question_bank WHERE id = ? AND user_id = ?', (question_id, user_id))
        conn.commit()
        conn.close()
        return True