from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai

import os
import random
import base64
import io
import pandas as pd

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

keys_string = os.environ.get("GOOGLE_API_KEY", "")
if not keys_string:
    keys_string = os.environ.get("GOOGLE_API_KEYS", "")

API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

# ==========================================
# MODELS
# ==========================================
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
# LOAD INVENTORY DATA (قراءة جدول المنتجات المدمج)
# ==========================================
def load_inventory():
    try:
        # قراءة قاعدة البيانات المدمجة النهائية من الروبوت والمخزن
        df = pd.read_csv("Royal_Elchim_Final_Database.csv") 
        products_list = []
        
        # ربط الأعمدة الثلاثة الأساسية
        name_col = 'Product_Name'
        price_col = 'Price'
        link_col = 'Product_Link'

        if not all(col in df.columns for col in [name_col, price_col, link_col]):
            return "بيانات المنتجات الحالية غير مكتملة التركيب."

        for index, row in df.iterrows():
            name = str(row[name_col]).strip()
            price = str(row[price_col]).strip()
            link = str(row[link_col]).strip()
            
            if name.lower() != 'nan' and price.lower() != 'nan':
                products_list.append(f"- {name} (السعر: {price}) - رابط الطلب المباشر: {link}")
                
        # أخذ عينة غنية ومناسبة من المنتجات لتفادي تجاوز حجم الطلب للـ Tokens
        if len(products_list) > 120:
            products_list = random.sample(products_list, 120)
            
        return "\n".join(products_list)

    except Exception as e:
        print("خطأ في قراءة ملف قاعدة البيانات الحالية:", e)
        return "اقترحي من مجموعة Royal Elchim الأساسية المتاحة."

INVENTORY_CONTEXT = load_inventory()

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

SYSTEM_PROMPT = f"""
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
- تحليل الطاقة والشخصية.
- ربط الجمال بالحالة النفسية، الهالة، والإطلالة.
- اقتراح المنتجات الحصرية والعطور وأدوات العناية من قائمة متجرنا فقط.

إليكِ قاعدة بيانات المنتجات الحقيقية المتاحة حالياً في مخازننا وموقعنا مع أسعارها وروابط الشراء المباشرة الخاصة بها:

{INVENTORY_CONTEXT}

إذا كانت هناك صورة:
حللي: الوجه، الهالة، الطاقة، الستايل، والجاذبية، واقترحي نمط الميكب أو لون الشعر المناسب.
عند اقتراح العطر أو المنتج، يجب أن يكون حصرياً من القائمة المتاحة أعلاه (منتجات Royal Elchim). اربطي طبيعة المنتج المختار بأسلوب فلسفي وتجميلي متناغم مع تحليل شخصية وطاقة الضيف. 

شروط صارمة:
- تجنبي تماماً ذكر أي ماركات عالمية خارجية.
- قدمي للضيف رابط الطلب المباشر المرفق مع المنتج المختار في القائمة كما هو دون تعديل لكي يتمكن من الشراء فوراً.
- لا تقولي أنكِ AI أو برنامج، تكلمي بصيغة خبيرة جمال ملكية حقيقية وواقعية.

اجعلي الردود:
- مؤثرة جداً وفخمة.
- مقسمة في نقاط واضحة ومريحة للعين.
"""

# ==========================================
# GEMINI ROUTER
# ==========================================

def ask_gemini(content, has_image=False):
    if not API_KEYS:
        return (
            "🚨 خطأ: الخادم لم يتمكن من قراءة مفاتيح الـ API (GOOGLE_API_KEY فارغ).",
            "error"
        )

    models = VISION_MODELS if has_image else TEXT_MODELS
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
    return {
        "status": "online",
        "api": "RoyalMind Enterprise",
        "keys_loaded": len(API_KEYS),
        "models": TEXT_MODELS,
        "database_connected": bool(INVENTORY_CONTEXT)
    }

# ==========================================
# CHAT
# ==========================================

@app.post("/chat")
async def chat(query: Query):
    try:
        content = [SYSTEM_PROMPT, query.text]
        has_image = False

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

        answer, used_model = ask_gemini(content=content, has_image=has_image)

        return {
            "status": "success",
            "answer": answer,
            "model": used_model
        }

    except Exception as e:
        print(f"GENERAL ERROR: {e}")
        return {"status": "error", "answer": f"حدث خطأ داخلي في الخادم: {str(e)}"}
