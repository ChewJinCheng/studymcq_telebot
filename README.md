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


