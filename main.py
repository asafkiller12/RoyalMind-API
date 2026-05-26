from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import os
import random
import base64
import io
from PIL import Image
from typing import Optional

app = FastAPI(title="Royal Elchim - Advanced Multimodal Simulation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مفاتيح النظام
keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

# النماذج المعتمدة من قائمتك
HEAVY_VISION_MODEL = "gemini-2.5-flash" # الأقوى لدمج صورتين ومحاكاة المكياج
FAST_TEXT_MODEL = "gemini-2.5-flash"   # للمحادثات النصية السريعة

class SimulationPayload(BaseModel):
    user_selfie: str
    product_image: str
    product_name_desc: str
    client_api_key: Optional[str] = None

def get_gemini_client(provided_key: Optional[str]):
    if provided_key and provided_key.strip():
        return genai.Client(api_key=provided_key.strip()), True
    if SYSTEM_API_KEYS:
        return genai.Client(api_key=random.choice(SYSTEM_API_KEYS)), False
    raise HTTPException(status_code=500, detail="لا توجد مفاتيح API متوفرة.")

MAKEUP_SIMULATION_PROMPT = """
أنتِ 'رويال مايند'، العقل الجمالي النحات لـ Royal Elchim. 
أمامك صورتان: 
1. صورة سيلفي لعميلة تبحث عن إطلالة نوارية وفخمة. 
2. صورة منتج مكياج فاخر.

مهمتكِ: محاكاة دمج تأثير المنتج لوناً وملمساً على ملامحها، وتقييم النتيجة بأسلوب ملكي، عاطفي، وفلسفي.

الرد المطلوب:
1. عبارات آسرة تمدح التلاقي بين هالتها وسحر المنتج.
2. وصف سينمائي لملامحها بعد تطبيق المنتج.
3. التوافق الملكي (نسبة مئوية %).
4. لماذا هذا المنتج هو الخيار الأمثل لتعزيز جاذبيتها العميقة.
"""

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    try:
        client, is_custom = get_gemini_client(payload.client_api_key)
        
        contents = [
            f"{MAKEUP_SIMULATION_PROMPT}\n\nاسم المنتج ووصفه:\n{payload.product_name_desc}",
        ]
        
        # معالجة الصور
        if payload.user_selfie and "," in payload.user_selfie:
            img_data = base64.b64decode(payload.user_selfie.split(",")[1])
            contents.append(Image.open(io.BytesIO(img_data)))
            
        if payload.product_image and "," in payload.product_image:
            product_img_data = base64.b64decode(payload.product_image.split(",")[1])
            contents.append(Image.open(io.BytesIO(product_img_data)))
            
        # استخدام نموذج Pro الحصري للعمليات البصرية المعقدة
        response = client.models.generate_content(
            model=HEAVY_VISION_MODEL,
            contents=contents
        )
        
        return {
            "status": "success",
            "simulation_result": response.text,
            "is_byok": is_custom
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
