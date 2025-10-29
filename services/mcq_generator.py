# ============================================================================
# services/mcq_generator.py - MCQ Generation Using Groq
# ============================================================================

import json
from typing import List, Dict
from groq import Groq
from utils.logger import setup_logger
from messages import MCQPrompts
import config

logger = setup_logger(__name__)

import json
import re
from groq import Groq
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MCQGenerator:
    """Generate MCQs using Groq API"""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
    
    def generate_mcqs_from_chunk(self, content: str, min_questions: int = 3, max_questions: int = 5) -> list:
        """Generate MCQs from a content chunk"""
        
        from messages import MCQPrompts
        
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": MCQPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": MCQPrompts.get_generation_prompt(
                        content, min_questions, max_questions
                    )}
                ],
                temperature=config.GROQ_TEMPERATURE,
                max_tokens=config.GROQ_MAX_TOKENS
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Raw API response: {response_text[:200]}...")
            
            # Try to extract JSON if wrapped in Markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON
            try:
                mcqs = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response text: {response_text}")
                
                # Try to fix common JSON issues
                fixed_text = self._fix_json_escaping(response_text)
                try:
                    mcqs = json.loads(fixed_text)
                    logger.info("Successfully parsed after fixing JSON")
                except json.JSONDecodeError:
                    logger.error("Failed to parse even after fixing")
                    return []
            
            # Validate and clean each MCQ
            validated_mcqs = []
            for mcq in mcqs:
                if self._validate_mcq(mcq):
                    # Clean the MCQ content
                    cleaned_mcq = self._clean_mcq(mcq)
                    validated_mcqs.append(cleaned_mcq)
            
            return validated_mcqs
            
        except Exception as e:
            logger.error(f"Error generating MCQs: {e}")
            return []
    
    def _fix_json_escaping(self, text: str) -> str:
        """Fix common JSON escaping issues"""
        # Replace invalid escape sequences
        # This is a simple fix - replace \' with '
        text = text.replace("\\'", "'")
        # Fix other common issues
        text = text.replace("\\<", "<")
        text = text.replace("\\>", ">")
        return text
    
    def _validate_mcq(self, mcq: dict) -> bool:
        """Validate MCQ structure"""
        required_keys = ['question', 'options', 'correct_answer', 'explanation']
        
        if not all(key in mcq for key in required_keys):
            logger.warning(f"MCQ missing required keys: {mcq.keys()}")
            return False
        
        if not isinstance(mcq['options'], list) or len(mcq['options']) != 4:
            logger.warning(f"MCQ has invalid options: {mcq.get('options')}")
            return False
        
        if mcq['correct_answer'] not in ['A', 'B', 'C', 'D']:
            logger.warning(f"MCQ has invalid correct_answer: {mcq.get('correct_answer')}")
            return False
        
        return True
    
    def _clean_mcq(self, mcq: dict) -> dict:
        """Clean MCQ content to prevent parsing issues"""
        def deep_clean(text):
            """Aggressively clean text to basic ASCII"""
            if not isinstance(text, str):
                text = str(text)
            
            # Convert to ASCII only
            import unicodedata
            text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
            
            # Replace special characters
            import string
            allowed = string.ascii_letters + string.digits + string.punctuation + ' '
            text = ''.join(c if c in allowed else ' ' for c in text)
            
            # Clean up whitespace
            return ' '.join(text.split()).strip()
        
        return {
            'question': deep_clean(mcq['question']),
            'options': [deep_clean(opt) for opt in mcq['options']],
            'correct_answer': mcq['correct_answer'].strip().upper(),
            'explanation': deep_clean(mcq['explanation'])
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean text to prevent HTML/Markdown parsing issues"""
        if not isinstance(text, str):
            text = str(text)
        
        # Convert smart quotes to regular quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Replace other potentially problematic characters
        text = text.replace('—', '-').replace('–', '-')  # Em/en dashes to hyphen
        text = text.replace('…', '...').replace('•', '*') # Ellipsis and bullets
        
        # Remove zero-width spaces and other invisible characters
        text = ''.join(char for char in text if ord(char) >= 32)
        
        # Clean up whitespace
        text = ' '.join(text.split())  # Normalize spaces
        text = text.strip()
        
        return text


def chunk_pdf_by_pages(file_bytes: bytes) -> List[tuple]:
    """Extract text from PDF and return list of (page_number, text) tuples"""
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    chunks = []
    
    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            chunks.append((f"Page {page_num}", text))
    
    return chunks