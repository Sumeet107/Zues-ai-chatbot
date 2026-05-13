# ZEUS AI — Advanced Agentic OS & Productivity Assistant

![ZEUS AI Banner](https://raw.githubusercontent.com/your-username/your-repo/main/static/images/banner.png) 

ZEUS AI is a futuristic, agentic AI Operating System designed to be your personal executive assistant. Built on top of **Django** and powered by **Llama 3 (via Ollama)**, ZEUS doesn't just chat—it thinks, plans, and executes.

## 🚀 Key Features

- **🧠 Agentic Neural Core**: Powered by Llama 3, ZEUS understands complex intent and can route tasks between chat, reminders, and meeting scheduling.
- **💾 Persistent AI Memory**: ZEUS features long-term memory, allowing it to remember your preferences, work habits, and personal facts across sessions.
- **📅 Smart Meeting Management**: Schedule meetings with natural language. ZEUS handles participants, locations, and priorities automatically.
- **🔔 Proactive Reminders**: Set reminders in seconds. ZEUS monitors them in the background and notifies you via real-time WebSockets.
- **📊 Behavioral Analytics**: An integrated analytics engine that analyzes your productivity patterns and provides strategic improvement steps.
- **🌌 Cinematic OS Interface**: A high-end, sci-fi aesthetic featuring glassmorphism, glowing neon elements, and smooth animations.
- **🎙️ Voice Integration**: (Coming Soon / Experimental) Voice-ready processing for hands-free interaction.

## 🛠️ Tech Stack

- **Backend**: Django 5.x
- **Real-time**: Django Channels (WebSockets)
- **AI Engine**: Ollama (Llama 3)
- **Frontend**: Vanilla JS, CSS3 (Glassmorphism), HTML5
- **Database**: SQLite (Development) / PostgreSQL (Production ready)
- **Task Logic**: Custom Thread-based Background Scheduler

## 📦 Installation & Setup

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: [Download Ollama](https://ollama.com/)
- **Llama 3 Model**: Run `ollama pull llama3` in your terminal.

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/zeus-ai-chatbot.git
cd zeus-ai-chatbot
```

### 3. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install django channels daphne requests
```

### 5. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Run the Server
```bash
python manage.py runserver
```
*Ensure Ollama is running in the background (`ollama serve`).*

## 🎮 Usage Guide

- **General Chat**: "Who are you?" or "Tell me a joke."
- **Set Reminders**: "Remind me to call the manager in 15 minutes."
- **Schedule Meetings**: "Schedule a Design Review for tomorrow with Alice and Bob."
- **Analysis**: Check the Dashboard to see your AI-generated productivity summary.

## 🎨 Design Philosophy
ZEUS is designed to feel like a high-end AI Operating System from a sci-fi film. It uses a dark-themed UI with vibrant neon accents (`#00f2ff`, `#7000ff`) and micro-animations to provide a premium user experience.

---

## 🤝 Contributing
Contributions are welcome! If you have ideas for new features or improvements, feel free to open an issue or submit a pull request.

## 📄 License
This project is licensed under the MIT License.

---
*Created with ❤️ by [Your Name/GitHub]*
