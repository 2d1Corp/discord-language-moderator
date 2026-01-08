import discord
from discord import app_commands # Для слеш-команд
import re
import asyncio
import logging
import os
from groq import Groq
from google import genai
from dotenv import load_dotenv

# Налаштування
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WHITELIST_FILE = os.path.join(BASE_DIR, "whitelist.txt")

# Клієнти
groq_client = Groq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Регулярні вирази
UA_UNIQUE = set("іїєґ")
RU_UNIQUE = set("ыёэъ")
RU_MARKERS = {"что", "это", "как", "меня", "тебя", "было", "есть", "когда", "только"}
UA_WORD_RE = re.compile(r"[а-щьюяіїєґ']+", re.IGNORECASE)

# Глобальні змінні
whitelist_lock = asyncio.Lock()
ai_semaphore = asyncio.Semaphore(2)
whitelist = set()
# Пам'ять для команди /why: {channel_id: "Причина"}
last_deleted_reason = {}

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    return set()

whitelist = load_whitelist()

# Налаштування бота
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Реєструємо слеш-команди
        await self.tree.sync()

bot = MyBot()

async def save_to_whitelist(text):
    words = UA_WORD_RE.findall(text.lower())
    new_words = [w for w in words if len(w) >= 4 and w not in whitelist]
    if new_words:
        async with whitelist_lock:
            with open(WHITELIST_FILE, "a", encoding="utf-8") as f:
                for word in new_words:
                    f.write(word + "\n")
                    whitelist.add(word)
            logging.info(f"💾 Словник +{len(new_words)}")

async def analyze_with_ai(text: str):
    system_prompt = (
        "Identify ONLY pure Russian. ALLOW Ukrainian dialects/Surzhyk but if word looks like russian with mistake check if there is such an dialct/surzyk word in Ukrainian. Answer ONLY 'yes' or 'no'."
    )
    async with ai_semaphore:
        # Groq
        try:
            chat = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
                model="llama-3.3-70b-versatile",
                temperature=0.0
            )
            res = chat.choices[0].message.content.strip().lower()
            return "yes" in res # Повертаємо True/False
        except: pass
        # Gemini
        try:
            response = gemini_client.models.generate_content(model='gemini-2.0-flash', contents=text)
            return "yes" in response.text.strip().lower()
        except: return None

# --- КОМАНДА /WHY ---
@bot.tree.command(name="why", description="Дізнатися причину останнього видалення повідомлення")
async def why(interaction: discord.Interaction):
    reason = last_deleted_reason.get(interaction.channel_id, "Останнім часом у цьому каналі нічого не видалялося.")
    await interaction.response.send_message(f"🧐 **Причина видалення:** {reason}", ephemeral=True)

@bot.event
async def on_ready():
    logging.info(f"🚀 Бот v3.1 онлайн | /why активовано")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.content: return

    content_lower = message.content.lower().strip()
    words = content_lower.split()

    # 1. Whitelist
    if any(word in whitelist for word in words): return

    # 2. Укр літери
    if any(char in UA_UNIQUE for char in content_lower):
        await save_to_whitelist(message.content)
        return

    # 3. Швидке видалення
    reason = ""
    if any(char in RU_UNIQUE for char in content_lower):
        reason = "Повідомлення містить символи, що не використовуються в українській мові."
    elif any(word in RU_MARKERS for word in words):
        reason = "Спрацював автоматичний лінгвістичний фільтр (невідповідність мовним нормам чату)."

    if reason:
        last_deleted_reason[message.channel.id] = f"Користувач {message.author.name}: {reason}"
        try: return await message.delete()
        except: pass

    # 4. Довжина
    if len(message.content) < 4: return

    # 5. AI
    res = await analyze_with_ai(message.content)
    if res is True:
        last_deleted_reason[message.channel.id] = f"Користувач {message.author.name}: Мовна модель ідентифікувала текст як порушення мовної політики."
        try: await message.delete()
        except: pass
    elif res is False:
        await save_to_whitelist(message.content)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)