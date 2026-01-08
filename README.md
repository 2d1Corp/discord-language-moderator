# Discord Language Moderation Bot

A Discord bot designed for automatic message moderation in Ukrainian-focused communities.  
The main goal is to detect and remove messages written in **pure Russian language**, while allowing Ukrainian, mixed speech (surzhyk), and regional dialects.

---

## 🚀 Features

- 🧹 Automatically removes messages written in **100% Russian**
- ✅ Allows:
  - Ukrainian language
  - Surzhyk (mixed Ukrainian-Russian speech)
  - Regional dialects (e.g. Transcarpathian)
- 🧠 Multi-layer language detection pipeline:
  1. **Word whitelist** for fast-pass filtering
  2. **Heuristic checks** based on unique characters
  3. **AI-based analysis** as a final decision layer
- 🤖 AI integrations:
  - **Groq API (LLaMA 3.3)** as primary model
  - **Google Gemini** as fallback provider
- 📚 Automatic whitelist learning to reduce AI usage
- 🔁 Failover between AI providers
- 📝 Detailed moderation event logging

---

## 🛠 Tech Stack

- Python
- discord.py
- asyncio
- Groq API (LLaMA 3.3)
- Google Gemini API
- Regular Expressions
- python-dotenv, logging

---

## ⚙️ Setup

```bash
git clone https://github.com/2d1Corp/discord-language-moderator.git
cd discord-language-moderator
pip install -r requirements.txt
# Create a .env file based on .env.example and provide the required API keys.
```
---

## ▶️ Run
python bot.py

---

## ⚠️ Disclaimer
This bot is intended for educational and community moderation purposes.

Final moderation decisions are made automatically based on predefined rules and AI analysis