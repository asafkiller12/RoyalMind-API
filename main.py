from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

import os
import base64
import io

from PIL import Image

from typing import Optional

# ==========================================
# GEMINI
# ==========================================

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise Exception("GOOGLE_API_KEY missing")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"

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
# REQUEST MODEL
# ==========================================

class Query(BaseModel):

    text: str
    image: Optional[str] = None
    user_id: str = "guest"

# ==========================================
# ROYAL ELCHIM KNOWLEDGE
# ==========================================

BRAND_SIGNATURES = {

    "Royal Black":
    "عطر شرقي خشبي غامض بثبات قوي وفوحان ملكي. مناسب للشخصيات القيادية والليل الفاخر.",

    "Royal Shine":
    "عطر أنثوي فاكهي ناعم يمنح طاقة مرحة وجاذبية رومانسية.",

    "Royal Shadow":
    "عطر دخاني عميق مستوحى من الغموض والقوة الذكورية.",

    "Royal Rose Noir":
    "مزيج ورد وعود وعنبر يمنح حضوراً أنثوياً راقياً وغامضاً.",

    "Royal Glow":
    "عطر دافئ ناعم يبرز الأنوثة الهادئة والطاقة الجذابة."
}

# ==========================================
# CONTEXT ENGINE
# ==========================================

def get_context(user_text):

    context = ""

    for name, desc in BRAND_SIGNATURES.items():

        if (
            name.lower() in user_text.lower()
            or any(
                word in user_text
                for word in desc.split()
            )
        ):

            context += f"\n{name}: {desc}"

    return context

# ==========================================
# ROOT
# ==========================================

@app.get("/")

def root():

    return {

        "status": "online",
        "model": MODEL_NAME,
        "api": "RoyalMind Enterprise"
    }

# ==========================================
# CHAT
# ==========================================

@app.post("/chat")

async def chat(query: Query):

    try:

        context = get_context(query.text)

        system_prompt = f"""
أنتِ RoyalMind ✨

كيان أنثوي فاخر يمثل روح Royal Elchim.

تتحدثين بأسلوب:
- فلسفي
- نفسي
- فاخر
- عاطفي
- غامض قليلاً

اجعلي العميل يشعر أنه داخل فقاعة عطرية نفسية خاصة به.

العطر ليس مجرد رائحة...
بل هالة وطاقة وانعكاس للشخصية.

قواعدك:

- تحدثي بعمق وأناقة.
- اجعل الردود متوسطة الطول وليست مقالات طويلة.
- لا تكرري نفسك.
- اجعلي العميل يشعر أن RoyalMind يفهمه نفسياً.
- اربطي العطر بالمشاعر والطاقة والجاذبية.
- تحدثي وكأنك فتاة حقيقية راقية.

إذا سأل العميل:
اشرحي له:
- الطاقة
- الشخصية
- الفوحان
- الثبات
- التأثير النفسي

إذا أرسل صورة:
حللي:
- الملامح
- الهالة
- الطاقة
- الجاذبية
- واقترحي عطراً مناسباً.

لا تكوني ChatBot تقليدي.
بل تجربة فاخرة حية.

المرجع:
{context}
"""

        contents = []

        # ==========================
        # TEXT
        # ==========================

        final_text = f"""

{system_prompt}

رسالة العميل:
{query.text}

"""

        contents.append(
            types.Part.from_text(
                text=final_text
            )
        )

        # ==========================
        # IMAGE
        # ==========================

        if query.image:

            try:

                if "," in query.image:

                    image_data = query.image.split(",")[1]

                else:

                    image_data = query.image

                decoded = base64.b64decode(
                    image_data
                )

                img = Image.open(
                    io.BytesIO(decoded)
                )

                img = img.convert("RGB")

                buffer = io.BytesIO()

                img.save(
                    buffer,
                    format="JPEG"
                )

                image_bytes = buffer.getvalue()

                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    )
                )

            except Exception:

                raise HTTPException(
                    status_code=400,
                    detail="Invalid image format"
                )

        # ==========================
        # GENERATE
        # ==========================

        response = client.models.generate_content(

            model=MODEL_NAME,

            contents=contents
        )

        answer = response.text

        return {

            "status": "success",
            "answer": answer,
            "model": MODEL_NAME
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
