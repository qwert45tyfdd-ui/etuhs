from pathlib import Path
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ai_engine import ask_ai

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Smart Assistant",
    description="المساعد الذكي المتكامل",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)

@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="اكتب رسالتك أولاً"
        )

    history = []

    for item in request.history[-20:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role in ("user", "assistant") and isinstance(content, str):
            history.append({
                "role": role,
                "content": content
            })

    try:
        answer = await ask_ai(message, history)
        return {"reply": answer}

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="إعداد مفتاح الذكاء الاصطناعي غير مكتمل"
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"خطأ في الاتصال بالذكاء الاصطناعي: {type(e).__name__}"
        )
