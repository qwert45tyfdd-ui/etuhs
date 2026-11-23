
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")
API_KEY = os.getenv("OPENROUTER_API_KEY")

client = None
if API_KEY:
    client = AsyncOpenAI(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

MODEL = "openrouter/free"

app = FastAPI(
    title="Smart Assistant",
    description="المساعد الذكي المتكامل",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: ChatRequest):
    if not client:
        raise HTTPException(
            status_code=500,
            detail="مفتاح OpenRouter غير موجود في ملف .env"
        )

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="اكتب رسالتك أولاً")

    history = []
    for item in request.history[-20:]:
        if item.get("role") in ("user", "assistant"):
            content = item.get("content")
            if isinstance(content, str):
                history.append({
                    "role": item["role"],
                    "content": content
                })

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد ذكي مفيد. أجب باللغة العربية بوضوح وود."
                },
                *history,
                {"role": "user", "content": message}
            ]
        )

        answer = response.choices[0].message.content
        return {"reply": answer or "لم أتمكن من إنشاء رد."}

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"خطأ في الاتصال بالذكاء الاصطناعي: {type(e).__name__}"
        )
