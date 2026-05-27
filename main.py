from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import random
import base64
import io
import pandas as pd
from PIL import Image
from typing import Optional, Dict
import time

app = FastAPI(title="Royal Elchim - Luxury Inventory Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# جلب المفاتيح من السيرفر
keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# وظائف جلب البيانات من الملفات المرفوعة
def get_inventory():
    try:
        if os.path.exists("last.xls - Sheet1.csv"):
            return pd.read_csv("last.xls - Sheet1.csv")
        return pd.DataFrame()
    except: 
        return pd.DataFrame()

def get_links_db():
    try:
        if os.path.exists("Royal_Elchim_Final_Database.csv"):
            return pd.read_csv("Royal_Elchim_Final_Database.csv")
        return pd.DataFrame()
    except: 
        return pd.DataFrame()

# محرك الـ Router المرن والمقاوم للأخطاء
def robust_generate(client_api_key, contents, models_list):
    if client_api_key and client_api_key.strip():
        keys_to_use = [client_api_key.strip()]
    else:
        if not SYSTEM_API_KEYS:
            raise HTTPException(status_code=500, detail="مفاتيح النظام غير مهيأة بالسيرفر حالياً.")
        keys_to_use = SYSTEM_API_KEYS.copy()
        random.shuffle(keys_to_use)

    for model_name in models_list:
        for key in keys_to_use:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    client = genai.Client(api_key=key)
                    config = types.GenerateContentConfig(temperature=0.75, top_p=0.95)
                    response = client.models.generate_content(model=model_name, contents=contents, config=config)
                    if response and response.text:
                        return response.text, model_name
                except Exception as e:
                    error_msg = str(e)
                    if "503" in error_msg or "ResourceExhausted" in error_msg or "429" in error_msg:
                        time.sleep(1.5)
                        continue
                    else:
                        break
    raise HTTPException(status_code=503, detail="جلسة رويال مايند ممتلئة حالياً، ثوانٍ وأعيدي المحاولة.")

BASE_PHILOSOPHY = """
أنتِ 'رويال مايند'، الفيلسوفة الجمالية لـ Royal Elchim.
تؤمنين بأن الجمال ليس مجرد طبقة خارجية، بل هو 'معنى عميق، حضور ساحر، وأثر دافئ يولد حباً وانجذاباً نقياً من الجميع'.
تتحدثين دائماً بنبرة أنثوية فاخرة، راقية، وممتلئة بالعاطفة الصادقة والتخفيف من المصطلحات المعقدة.
"""

class DiagnosisPayload(BaseModel):
    mood_answers: Dict[str, str]
    image: Optional[str] = None
    client_api_key: Optional[str] = None

class ChatPayload(BaseModel):
    text: str
    category: str  
    image: Optional[str] = None
    history_context: Optional[str] = None
    client_api_key: Optional[str] = None

def parse_image(base64_string):
    if base64_string and "," in base64_string:
        try:
            img_data = base64.b64decode(base64_string.split(",")[1])
            return Image.open(io.BytesIO(img_data))
        except:
            return None
    return None

# مسار البحث الملكي (المحسن لعرض الحالة والربط الذكي)
@app.get("/api/search")
async def search(query: str):
    inv = get_inventory()
    db = get_links_db()
    if inv.empty: return {"status": "error", "message": "السجلات غير متاحة"}

    results = inv[
        inv['الصنف'].str.contains(query, na=False, case=False) | 
        inv['الباركود'].astype(str).str.contains(query, na=False)
    ].head(10)

    data = []
    for _, row in results.iterrows():
        try:
            raw_qty = str(row['كمية']).replace(',', '.')
            stock_count = float(raw_qty) if raw_qty != 'nan' else 0
        except: 
            stock_count = 0

        if stock_count > 5:
            status, color = "متوفر حالياً", "success"
        elif 0 < stock_count <= 5:
            status, color = f"قطع أخيرة ({int(stock_count)})", "warning"
        else:
            status, color = "نفذت الكمية", "danger"

        link_match = db[db['Product_Name'].str.contains(str(row['الصنف']), na=False, case=False)] if not db.empty else pd.DataFrame()
        link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"

        data.append({
            "name": row['الصنف'],
            "price": row.get('سعر1 كارت', 'اتصلي بنا'),
            "status": status,
            "color": color,
            "barcode": row.get('الباركود', '---'),
            "link": link
        })
    return {"status": "success", "data": data}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    inv = get_inventory()
    suggestions_context = ""
    if not inv.empty and 'كمية' in inv.columns:
        available = inv[inv['كمية'] > 0]
        if not available.empty:
            sampled = available.sample(n=min(3, len(available)))
            suggestions_context = "\n".join([f"- {r['الصنف']} (السعر: {r.get('سعر1 كارت', 'متاح')})" for _, r in sampled.iterrows()])

    formatted_answers = "\n".join([f"- {k}: {v}" for k, v in payload.mood_answers.items()])
    prompt = f"{BASE_PHILOSOPHY}\nالعميل يمر بحدث ومزاج متمثل في:\n{formatted_answers}\nالمنتجات الحقيقية المتاحة بالمعرض حالياً:\n{suggestions_context}\nصيغي قراءة لروحه ورشحي منتجاً يترك أثراً وحضوراً يولد الحب."
    
    contents = [prompt]
    img = parse_image(payload.image)
    if img: contents.append(img)
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    inv = get_inventory()
    catalog_context = ""
    if not inv.empty:
        available = inv[inv['كمية'] > 0] if 'كمية' in inv.columns else inv
        sampled = available.sample(n=min(5, len(available))) if not available.empty else pd.DataFrame()
        catalog_context = "\n".join([f"- {r['الصنف']} (السعر: {r.get('سعر1 كارت', 'متاح')})" for _, r in sampled.iterrows()])

    prompt = f"{BASE_PHILOSOPHY}\nالمسار الحالي: {payload.category}\nالمنتجات الحية بالمخزن المتاحة للترشيح المباشر:\n{catalog_context}\nرسالة العميل: {payload.text}\nصيغي رداً جذاباً يولد الانجذاب والمحبة مع ذكر اسم المنتج ورابط الشراء المتوقع صراحة بـ https."
    
    contents = [prompt]
    img = parse_image(payload.image)
    if img: contents.append(img)
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "answer": res}
