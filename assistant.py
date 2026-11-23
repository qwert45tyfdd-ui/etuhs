import os
import json
from pathlib import Path
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

BASE = Path.home() / "smart_assistant"
MEMORY = BASE / "memory"
MEMORY.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE / ".env")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not API_KEY:
    raise RuntimeError("تأكد من مفاتيح TELEGRAM_BOT_TOKEN و OPENROUTER_API_KEY داخل .env")

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openrouter/free"
OWNER_ID = 8056015134

def memory_file(user_id):
    return MEMORY / f"{user_id}.json"

def load_memory(user_id):
    path = memory_file(user_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_memory(user_id, history):
    memory_file(user_id).write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("رقم حسابك: " + str(update.effective_user.id))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في المساعد الذكي 🤖\n"
        "اكتب سؤالك مباشرة.\n\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/clear - مسح ذاكرة المحادثة"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/clear - مسح ذاكرة المحادثة\n\n"
        "اكتب سؤالك مباشرة وسأساعدك."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_memory(update.effective_user.id, [])
    await update.message.reply_text("تم مسح ذاكرة المحادثة 🧹")


async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("غير مسموح لك.")
        return

    files = sorted(x.name for x in BASE.iterdir() if not x.name.startswith("."))
    await update.message.reply_text("ملفات المشروع:\n" + "\n".join(files))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        return
    user_id = update.effective_user.id
    message = update.message.text
    history = load_memory(user_id)

    history.append({"role": "user", "content": message})

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد ذكي مفيد. أجب باللغة العربية بوضوح وود."
                },
                *history
            ]
        )

        answer = response.choices[0].message.content or "لم أتمكن من إنشاء رد."

        history.append({"role": "assistant", "content": answer})
        save_memory(user_id, history)

        await update.message.reply_text(answer)

    except Exception as e:
        if history and history[-1]["role"] == "user":
            history.pop()
        save_memory(user_id, history)

        await update.message.reply_text(
            "حدث خطأ في الاتصال بالذكاء الاصطناعي:\n"
            f"{type(e).__name__}: {str(e)[:300]}"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("files", files_command))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("المساعد الذكي يعمل الآن عبر OpenRouter...")
    app.run_polling()

if __name__ == "__main__":
    main()
