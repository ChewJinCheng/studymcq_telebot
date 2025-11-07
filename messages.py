class BotMessages:
    """All bot messages and text templates"""
    
    # Welcome and Help
    WELCOME_MESSAGE = """🌵 Welcome to StudyMCQ Bot!

I help you master your study materials through daily MCQ quizzes.

📚 *How to use:*
• Send me text or upload documents (PDF, DOCX, TXT)
• I'll generate quality MCQ questions and store them
• Use /quiz to practice with random questions from your bank
• Use /settings to customize your daily quiz

*Commands:*
/start - Instruction Manual
/upload - How to upload study materials
/custom\\_qn - Create a custom question
/quiz - Start a quiz with random questions
/settings - Configure daily questions & time
/stats - View your progress
/bank - View question bank statistics
/clear\\_knowledge - Clear knowledge base only
/clear\\_questions - Clear question bank only
/help - Show this message"""

    # Upload Instructions
    UPLOAD_INSTRUCTIONS = """📤 *Upload Your Study Materials*

Simply send me any of these:
• PDF files (.pdf) - I'll process each page
• Word documents (.docx)
• Text files (.txt)
• Or just paste text directly!

I'll automatically:
1️⃣ Save to your knowledge base
2️⃣ Split into manageable chunks
3️⃣ Generate quality MCQ questions
4️⃣ Store questions for instant quizzing"""

    # Question Bank
    EMPTY_QUESTION_BANK = """📊 Your question bank is empty!

Upload study materials to generate questions."""

    QUESTION_BANK_STATS = """📊 *Your Question Bank*

Total Questions: {count}
From {sources} source(s)
Average times asked: {avg_asked:.1f}
Overall accuracy: {accuracy:.1f}%

Ready to quiz! Use /quiz to practice. 🎯"""

    # Settings
    CURRENT_SETTINGS = """⚙️ *Current Settings*

Daily Quiz Settings:
• Questions per quiz: {daily_questions}
• Quiz Time: {quiz_time} (24-hour format)

Question Generation Settings:
• Min questions per chunk: {min_questions}
• Max questions per chunk: {max_questions}

Select an option to update:"""

    SET_MIN_QUESTIONS_PROMPT = """Enter minimum number of questions to generate per content chunk.

Note: While you can set any positive number, we recommend not exceeding 10 questions for better learning experience."""

    SET_MAX_QUESTIONS_PROMPT = """Now enter maximum number of questions (must be greater than or equal to {min_q}).

This sets the range of questions that can be generated for each chunk of content."""
    
    INVALID_MIN_QUESTIONS = "Please enter a positive number greater than 0"
    INVALID_MAX_QUESTIONS = "Maximum questions must be greater than or equal to minimum questions ({min_q})"
    
    QUESTIONS_PER_CHUNK_SET = """✅ Question generation settings updated:
• Minimum: {min_q} questions
• Maximum: {max_q} questions

The bot will generate {min_q}-{max_q} questions per chunk of content, depending on the content complexity."""

    # Quiz
    EMPTY_BANK_ERROR = "❌ Your question bank is empty! Please upload documents or send text first."
    
    ASK_QUIZ_COUNT = """🎯 *Start a Quiz*

You have {total} questions in your bank.

How many questions would you like in this quiz?

Please send a number between 1 and {total}."""
    
    QUIZ_START = "🎯 Starting quiz with {num} questions from your bank!"
    QUIZ_LOAD_ERROR = "❌ Failed to load questions. Please try again."
    INVALID_QUIZ_COUNT = "❌ Please send a valid number between 1 and {total}."
    
    QUIZ_COMPLETED = """✅ *Quiz Completed!*

Score: {score}/{total} ({percentage:.1f}%)

Great job! Keep studying to improve further! 🎓

Use /quiz to practice more questions."""

    QUIZ_ENDED_EARLY = """🛑 *Quiz Ended*

You answered {answered} out of {total} questions.
Score: {score}/{answered} ({percentage:.1f}%)

Use /quiz to start a new quiz!"""

    QUIZ_QUESTION = """📝 Question {current}/{total}

    {question}

    Source: {source}"""

    # Edit Question Messages
    EDIT_QUESTION_START = """📝 Current Question:
{question}

Would you like to edit the question phrasing?"""

    EDIT_OPTIONS_START = """Current Options:
{options}

Would you like to edit the option labels?"""

    EDIT_ANSWER_START = """Current correct answer: {current_answer}

Would you like to set a different option as the correct answer?"""

    EDIT_EXPLANATION_START = """Current explanation:
{explanation}

Would you like to edit the explanation?"""

    ENTER_NEW_QUESTION = "Please enter the new question text:"
    SELECT_NEW_ANSWER = "Select the correct answer:"
    ENTER_NEW_EXPLANATION = "Please enter the new explanation:"
    INVALID_OPTIONS_FORMAT = """Invalid option format. Please enter exactly 4 options, one per line, starting with A - B - C - D -
Example:
A - First option
B - Second option
C - Third option
D - Fourth option"""

    EDIT_COMPLETE = "✅ Question has been updated successfully!"
    SKIP_EDIT = "Skipping this edit..."
    INVALID_ANSWER_CHOICE = "Please select a valid answer (A, B, C, or D)"

    # Delete question
    CONFIRM_DELETE_QUESTION = "⚠️ *Delete Question*\n\nThis will permanently remove this question from your bank. Are you sure?"
    QUESTION_DELETED = "✅ Question deleted."

    # Answer Feedback
    CORRECT_ANSWER = "✅ *Correct!*\n\n{explanation}"
    INCORRECT_ANSWER = "❌ *Incorrect*\n\nYour answer: {user_answer}\n\nWould you like to retry or see the solution?"
    
    SOLUTION = """💡 *Solution*

Correct Answer: *{correct_answer}*

{explanation}"""

    # Statistics
    NO_QUIZ_HISTORY = "📊 No quiz history yet! Start practicing with /quiz"
    
    STATS_DISPLAY = """📊 *Your Statistics*

Total Questions Answered: {total}
Correct Answers: {correct}
Accuracy: {accuracy:.1f}%

Keep up the great work! 🎯"""

    # Clear Confirmations
    CONFIRM_CLEAR_KNOWLEDGE = """⚠️ *Clear Knowledge Base*

This will delete all your uploaded documents and text.
Your question bank will remain intact.

Are you sure?"""

    CONFIRM_CLEAR_QUESTIONS = """⚠️ *Clear Question Bank*

This will delete all generated MCQ questions.
Your knowledge base will remain intact.

Are you sure?"""

    KNOWLEDGE_CLEARED = "✅ Your knowledge base has been cleared!"
    QUESTIONS_CLEARED = "✅ Your question bank has been cleared!"

    # Document Processing
    PROCESSING_DOCUMENT = "📄 Processing your document..."
    PDF_SAVED = "✅ PDF saved! Processing {pages} pages to generate questions..."
    DOCUMENT_SAVED = "✅ Document saved! Generating questions..."
    TEXT_SAVED = "✅ Text file saved! Generating questions..."
    UNSUPPORTED_FORMAT = "❌ Unsupported file format. Please send PDF, DOCX, or TXT files."
    PROCESSING_ERROR = "❌ Error processing document. Please try again."
    
    GENERATION_COMPLETE = """🎉 *Complete!*

Generated {count} questions from '{source}'

Use /quiz to start practicing!"""

    TEXT_QUESTIONS_COMPLETE = """🎉 Generated {count} questions from your text!

Use /quiz to start practicing!"""

    # Settings Input
    SET_QUESTIONS_PROMPT = "How many questions would you like daily? (Send a number between 1-20)"
    SET_TIME_PROMPT = "What time would you like your daily quiz? (Send in 24-hour format, e.g., 09:00)"
    
    QUESTIONS_SET = "✅ Daily questions set to {num}"
    TIME_SET = "✅ Quiz time set to {time}"
    
    INVALID_NUMBER = "Please send a number between 1 and 20"
    INVALID_NUMBER_FORMAT = "Please send a valid number"
    INVALID_TIME_FORMAT = "Please send time in HH:MM format (e.g., 09:00)"

    # Daily Quiz Notification
    DAILY_QUIZ_NOTIFICATION = "🔔 Time for your daily quiz! Use /quiz to start practicing."


class MCQPrompts:
    """Prompts for MCQ generation"""
    
    SYSTEM_PROMPT = """You are a university professor that creates educational MCQ questions for final examinations. 
Always respond with valid JSON only, no additional text. 
Keep questions and explanations simple and avoid using special characters, HTML, or Markdown formatting."""
    
    @staticmethod
    @staticmethod
    def get_generation_prompt(content: str, min_questions: int, max_questions: int, max_length: int = 6000) -> str:
        return f"""Based on the following content, generate between {min_questions} and {max_questions} high-quality multiple-choice questions.
    Choose the number of questions based on:
    - Content complexity and depth
    - Important concepts and key points
    - Natural breaks in the content
    - Meaningful testable information

    You may incorporate additional relevant information from the web **only if it directly supports or extends the concepts in the content**. If you do, you **must cite the source clearly** in the "explanation" field using plain text (e.g., "According to [source name], ..."). Do not use external information that contradicts or distracts from the original material.

    Each question should:
    - Test deep understanding, not just memorization
    - Have 4 options (A, B, C, D) with one correct answer
    - Include a detailed explanation that quotes specific parts from the content
    - Cover different aspects of the content (avoid redundant questions)
    - Include a few harder reasoning questions in the format:
    "Which of the following statements are true?"
    (i) ...
    (ii) ...
    (iii) ...
    (iv) ... (or more if needed)
    The statements (i), (ii), (iii), (iv), etc. must be included inside the "question" field itself, each on a new line and indented for clarity.
    Use this exact format inside the question string:
    "Which of the following statements are true?\\n  (i) Statement one\\n  (ii) Statement two\\n  (iii) Statement three"
    The options must follow this format:
    ["A) Only (i)", "B) Only (i) and (ii)", "C) All of the above", "D) None of the above"]

    - All options must be logically distinct and non-redundant.
    - Do not repeat the same option text under different labels (e.g., avoid both "A) Only (i)" and "D) Only (i)").
    - Each option must represent a unique combination or interpretation of the statements (if relevant).

    Content:
    {content[:max_length]}

    IMPORTANT: Return ONLY valid JSON in this exact format, with no additional text:
    [
    {{
        "question": "Question text here, including any (i), (ii), (iii) statements if applicable",
        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
        "correct_answer": "A",
        "explanation": "Detailed explanation with quotes from content"
    }}
    ]"""

CUSTOM_QN_START = "📝 *Create Your Own Question*\n\nLet's create a custom MCQ question!\n\nPlease enter your question:"