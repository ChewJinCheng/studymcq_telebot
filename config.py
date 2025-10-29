from typing import Final
from dotenv import load_dotenv 
import os
# Load environment variables from .env file 
load_dotenv() 
# # Access them 
BOT_TOKEN: Final = os.getenv("BOT_TOKEN") 
BOT_USERNAME: Final = os.getenv("BOT_USERNAME") 
GROQ_API_KEY: Final = os.getenv("GROQ_API_KEY")

# Database Configuration
DB_NAME: Final = 'mcq_bot.db'

# MCQ Generation Settings
DEFAULT_QUESTIONS_PER_CHUNK: Final = 3  # Default minimum questions per chunk
MAX_QUESTIONS_PER_CHUNK: Final = 5      # Default maximum questions per chunk
CHUNK_SIZE_WORDS: Final = 1000          # Fixed size of content chunks for processing

# User Settings Defaults
DEFAULT_DAILY_QUESTIONS: Final = 5
DEFAULT_QUIZ_TIME: Final = '09:00'
DEFAULT_TIMEZONE: Final = 'UTC'

# Limits
MIN_DAILY_QUESTIONS: Final = 1
MAX_DAILY_QUESTIONS: Final = 20

# Groq API Settings
GROQ_MODEL: Final = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE: Final = 0.7
GROQ_MAX_TOKENS: Final = 4096
GROQ_TOP_P: Final = 1

# Content Limits
MAX_CONTENT_LENGTH: Final = 10000  # Characters to send to Groq