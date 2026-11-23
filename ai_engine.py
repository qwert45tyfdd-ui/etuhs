import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openrouter/free"

client = None

if API_KEY:
    client = AsyncOpenAI(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

async def ask_ai(message, history=None):
    if not client:
        raise RuntimeError("مفتاح OpenRouter غير موجود")

    messages = [
        {
            "role": "system",
            "content": "أنت مساعد ذكي مفيد. أجب باللغة العربية بوضوح وود."
        }
    ]

    if history:
        messages.extend(history[-20:])

    messages.append({"role": "user", "content": message})

    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    return response.choices[0].message.content or "لم أتمكن من إنشاء رد."
