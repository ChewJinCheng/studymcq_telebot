import sqlite3
from typing import Optional, Tuple, List
import config

class Database:
    """Database connection and initialization"""
    
    def __init__(self, db_name: str = config.DB_NAME):
        self.db_name = db_name
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Users table
        # Create base table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY,
                      username TEXT,
                      daily_questions INTEGER DEFAULT 5,
                      quiz_time TEXT DEFAULT '09:00',
                      timezone TEXT DEFAULT 'UTC')''')
        
        # Add new columns if they don't exist
        # SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we need to check
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'min_questions_per_chunk' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN min_questions_per_chunk INTEGER DEFAULT 3')
        
        if 'max_questions_per_chunk' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN max_questions_per_chunk INTEGER DEFAULT 5')
        
        # Knowledge base table (stores raw content)
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      content TEXT,
                      source TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id))''')
        
        # Question bank table (stores pre-generated MCQs)
        c.execute('''CREATE TABLE IF NOT EXISTS question_bank
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      question TEXT,
                      options TEXT,
                      correct_answer TEXT,
                      explanation TEXT,
                      source TEXT,
                      times_asked INTEGER DEFAULT 0,
                      times_correct INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id))''')
        
        # Quiz history table
        c.execute('''CREATE TABLE IF NOT EXISTS quiz_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      question_id INTEGER,
                      user_answer TEXT,
                      is_correct BOOLEAN,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id),
                      FOREIGN KEY (question_id) REFERENCES question_bank(id))''')
        
        conn.commit()
        conn.close()


def chunk_pdf_by_pages(file_bytes: bytes) -> List[Tuple[str, str]] :
    """Extract text from PDF and return list of (page_number, text) tuples"""
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    chunks = []
    
    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            chunks.append((f"Page {page_num}", text))
    
    return chunks