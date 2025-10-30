# 🌵 StudyMCQ

StudyMCQ is a TeleBot that helps you master your study materials through daily multiple-choice quizzes.
You can upload your own documents, and the bot will automatically generate high-quality MCQs using an LLM (e.g. Groq, OpenAI).

---

## 🚀 Features

* 📚 Upload study materials (`PDF`, `DOCX`, `TXT`)
* 🧠 Automatically generate MCQs from your uploaded content
* 🎯 Take random quizzes from your personal question bank
* 📊 Track your progress with stats and question history
* 🕒 Configure daily quizzes with reminders
* 🧹 Clear your question bank or knowledge base anytime

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/studymcq_bot.git
cd studymcq_bot
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Setup

Create a `.env` file in the project root:

```
BOT_TOKEN = ''
BOT_USERNAME = ''
GROQ_API_KEY = ''
```

> 🧩 You can obtain your Telegram bot token from [@BotFather](https://t.me/BotFather).

---

## 🧠 Usage

### Start the bot:

```bash
python main.py
```

### Telegram Commands

| Command            | Description                             |
| ------------------ | --------------------------------------- |
| `/upload`          | Upload a study document                 |
| `/quiz`            | Start a quiz with random questions      |
| `/settings`        | Configure daily quiz time and frequency |
| `/stats`           | View quiz performance and accuracy      |
| `/bank`            | Show question bank statistics           |
| `/clear_knowledge` | Clear learned materials only            |
| `/clear_questions` | Clear MCQ question bank only            |
| `/help`            | Show help message                       |

---

## 🧪 How It Works

StudyMCQ uses a smart pipeline to convert your study materials into multiple-choice questions:

### 📄 Document Processing
- When you upload a file (`PDF`, `DOCX`, or `TXT`), the bot extracts the raw text.
- The text is split into chunks of approximately **1000 words** to ensure manageable context size for the LLM.

### 🧠 MCQ Generation
- Each chunk is sent to the LLM with a prompt to generate **between `[min_questions, max_questions]`** multiple-choice questions.
- The number of questions is dynamically chosen based on content depth, complexity, and natural breaks.
- All generated questions include:
  - 4 options (A–D)
  - One correct answer
  - A detailed explanation quoting the source content

### 🗃️ Storage & Efficiency
- All questions are stored in your personal question bank.
- The LLM is **only called once per upload**, minimizing token usage and cost.

---

## ⚙️ Usability Features

### 1. 🔧 Customizable Verbosity
- You can configure the `min_questions` and `max_questions` per chunk to control how many questions are generated.
- A higher number may increase coverage but could reduce individual question quality — find your balance!

### 2. ✏️ Editable Questions
- If the LLM generates hallucinated or low-quality questions, you can manually:
  - Edit the question text
  - Modify options
  - Correct the answer or explanation
- This ensures your question bank remains accurate and trustworthy.

### 3. 🗑️ Delete Questions
- You can delete any question from your personal bank if it's irrelevant, incorrect, or no longer needed.
- This helps you keep your quiz pool clean and focused.

### 4. 🧾 Create Custom Questions
- You can manually add your own MCQs to the question bank.
- Useful for inserting instructor-provided questions, textbook examples, or your own practice items.
- Custom questions follow the same format: 4 options, one correct answer, and an explanation.

---

## 📦 File Structure

```
📁 cactusbot/
├── main.py                 # Entry point
├── services/
│   ├── mcq_generator.py    # LLM-based MCQ generation
│   ├── database.py         # Question/knowledge storage
│   ├── scheduler.py        # Daily quiz scheduling
│   └── utils.py            # Helper functions
├── assets/
│   └── profilepic.png      # Bot profile image
├── .env                    # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## 🧑‍💻 Author

**Chew Jin Cheng**  

This project was made possible with:

- **Groq API** — ultra-fast LLM question generation  
- **python-telegram-bot** — Telegram bot framework  
- **SQLite3** — lightweight on-disk database for questions, progress, and knowledge

---


