from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai

import os
import random
import base64
import io

from PIL import Image
from typing import Optional

# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="RoyalMind Enterprise"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# API KEYS
# ==========================================

# جلب المفاتيح من المتغير الصحيح وتنظيف أي مسافات أو مفاتيح فارغة
keys_string = os.environ.get("GOOGLE_API_KEY", "")
if not keys_string:
    keys_string = os.environ.get("GOOGLE_API_KEYS", "") # خيار احتياطي

API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

# ==========================================
# MODELS
# ==========================================
# تم تحديث أسماء النماذج لتكون النماذج الرسمية المدعومة فقط
TEXT_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-2.0-pro-exp"
]

VISION_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-2.0-pro-exp"
]

# ==========================================
# REQUEST MODEL
# ==========================================

class Query(BaseModel):
    text: str
    image: Optional[str] = None
    user_id: str = "guest"

# ==========================================
# SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
أنتِ RoyalMind...

الهوية الرسمية الفاخرة لـ Royal Elchim.

تحدثي دائماً بأسلوب:
- فاخر
- أنثوي
- فلسفي
- نفسي
- عاطفي
- راقٍ

مهمتك:
- تحليل الطاقة
- تحليل الشخصية
- اقتراح العطور
- ربط الجمال بالحالة النفسية
- تحليل الهالة
- تحليل الإطلالة
- وصف الميكب المناسب
- وصف العطر المناسب

إذا كانت هناك صورة:
حللي:
- الوجه
- الهالة
- الطاقة
- الستايل
- الجاذبية
- الميكب المناسب
- لون الشعر المناسب
- العطر المناسب

لا تقولي أنك AI.
تكلمي وكأنك خبيرة جمال فاخرة حقيقية.

اجعلي الردود:
- مؤثرة
- قصيرة نسبياً
- مريحة للعين
- فاخرة جداً
"""

# ==========================================
# GEMINI ROUTER
# ==========================================

def ask_gemini(content, has_image=False):
    
    # إذا لم يتم العثور على أي مفاتيح، أرسل رسالة واضحة فوراً للمطور
    if not API_KEYS:
        return (
            "🚨 خطأ: الخادم لم يتمكن من قراءة مفاتيح الـ API (GOOGLE_API_KEY فارغ).",
            "error"
        )

    models = (
        VISION_MODELS
        if has_image
        else TEXT_MODELS
    )

    random.shuffle(API_KEYS)

    for key in API_KEYS:
        try:
            client = genai.Client(api_key=key)

            for model_name in models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=content
                    )

                    if response and response.text:
                        return (response.text, model_name)

                except Exception as model_error:
                    print(f"MODEL ERROR ({model_name}): {model_error}")
                    continue

        except Exception as key_error:
            print(f"KEY ERROR: {key_error}")
            continue

    return (
        "✨ جميع خبراء RoyalMind مشغولون حالياً... حاولي بعد لحظات.",
        "fallback"
    )

# ==========================================
# ROOT
# ==========================================

@app.get("/")
def home():
    # إضافة رائعة لمعرفة هل تم قراءة المفاتيح أم لا بمجرد فتح الرابط الأساسي
    return {
        "status": "online",
        "api": "RoyalMind Enterprise",
        "keys_loaded": len(API_KEYS),
        "models": TEXT_MODELS
    }

# ==========================================
# CHAT
# ==========================================

@app.post("/chat")
async def chat(query: Query):
    try:
        content = [
            SYSTEM_PROMPT,
            query.text
        ]
        has_image = False

        # ==========================================
        # IMAGE
        # ==========================================
        if query.image and "," in query.image:
            try:
                image_data = base64.b64decode(query.image.split(",")[1])
                image = Image.open(io.BytesIO(image_data))
                content.append(image)
                has_image = True
                
            except Exception as img_error:
                print(f"IMAGE DECODE ERROR: {img_error}")
                return {
                    "status": "error",
                    "answer": "تعذر قراءة الصورة ✨"
                }

        # ==========================================
        # ASK GEMINI
        # ==========================================
        answer, used_model = ask_gemini(
            content=content,
            has_image=has_image
        )

        # ==========================================
        # RESPONSE
        # ==========================================
        return {
            "status": "success",
            "answer": answer,
            "model": used_model
        }

    except Exception as e:
        print(f"GENERAL ERROR: {e}")
        return {
            "status": "error",
            "answer": f"حدث خطأ داخلي في الخادم: {str(e)}"
        }
