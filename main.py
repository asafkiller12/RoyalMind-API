from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import random
import io
import base64
import pandas as pd
from PIL import Image
from typing import Optional, Dict
import time
import math

app = FastAPI(title="Royal Elchim - Luxury Engine Production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

def get_inventory():
    try:
        file_path = "last.xls - Sheet1.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df.fillna("")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading inventory file: {e}")
        return pd.DataFrame()

def get_links_db():
    try:
        file_path = "Royal_Elchim_Final_Database.csv"
        if os.path.exists(file_path):
            return pd.read_csv(file_path).fillna("")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading links database: {e}")
        return pd.DataFrame()

def robust_generate(client_api_key, contents, models_list):
    if client_api_key and client_api_key.strip():
        keys_to_use = [client_api_key.strip()]
    else:
        if not SYSTEM_API_KEYS:
            raise HTTPException(status_code=500, detail="مفاتيح الخادم السحابي غير مهيأة بعد.")
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
                        return response.text
                except Exception as e:
                    error_str = str(e)
                    if "503" in error_str or "ResourceExhausted" in error_str or "429" in error_str:
                        time.sleep(1.5)
                        continue
                    else:
                        break
                        
    raise HTTPException(status_code=503, detail="قنوات رويال مايند ممتلئة حالياً، يرجى إعادة المحاولة بعد ثوانٍ.")

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

class SimulationPayload(BaseModel):
    user_selfie: str
    product_image: str
    product_name_desc: str
    client_api_key: Optional[str] = None

def parse_image(base64_string):
    if base64_string and "," in base64_string:
        try:
            img_data = base64.b64decode(base64_string.split(",")[1])
            return Image.open(io.BytesIO(img_data))
        except:
            return None
    return None

# دالة صارمة لفحص وتطهير المخرجات النهائية قبل إرسالها لـ JSON
def sanitize_value(val, default_text="---"):
    if val is None:
        return default_text
    s = str(val).strip()
    if s.lower() == 'nan' or s == '':
        return default_text
    return s

BASE_PHILOSOPHY = """
أنتِ 'رويال مايند'، الفيلسوفة الجمالية وخبيرة الجمال والعطور الفاخرة لبراند Royal Elchim.
تؤمنين بأن الجمال ليس مظهراً خارجيفحسب، بل هو 'معنى عميق، حضور ساحر، وأثر دافئ يولد حباً وانجذاباً نقياً من الجميع'.
تتحدثين دائماً بنبرة أنثوية ملكية، راقية وممتلئة بالعاطفة الصادقة والتخفيف التام من التعقيدات التقنية.
"""

@app.get("/debug/routes")
async def get_routes():
    return [{"path": route.path, "methods": list(route.methods)} for route in app.routes]

@app.get("/api/search")
async def search(query: str):
    inv = get_inventory()
    db = get_links_db()
    if inv.empty: return {"status": "error", "message": "قاعدة بيانات المعرض غير متوفرة حالياً."}

    # البحث المرن الآمن
    results = inv[
        inv['الصنف'].astype(str).str.contains(query, na=False, case=False) | 
        inv['الباركود'].astype(str).str.contains(query, na=False)
    ].head(10)

    data = []
    for _, row in results.iterrows():
        try:
            raw_qty = str(row.get('كمية', '0')).replace(',', '.')
            qty = float(raw_qty) if (raw_qty and raw_qty.strip() != '' and raw_qty.lower() != 'nan') else 0.0
        except:
            qty = 0.0
        if math.isnan(qty): qty = 0.0

        if qty > 5:
            status, color = "متوفر حالياً", "success"
        elif 0 < qty <= 5:
            status, color = f"قطع أخيرة ({int(qty)})", "warning"
        else:
            status, color = "نفذت الكمية", "danger"

        link_match = db[db['Product_Name'].astype(str).str.contains(str(row.get('الصنف', '')), na=False, case=False)] if not db.empty else pd.DataFrame()
        link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"

        # حقن نظام التطهير الصارم على جميع الحقول المرسلة لـ JSON
        final_name = sanitize_value(row.get('الصنف'), "منتج غير مسمى")
        final_price = sanitize_value(row.get('سعر1 كارت'), "اتصلي بنا")
        final_barcode = sanitize_value(row.get('الباركود'), "---")
        final_link = sanitize_value(link, "https://www.royalelchim.app")

        data.append({
            "name": final_name,
            "price": final_price,
            "status": status,
            "color": color,
            "barcode": final_barcode,
            "link": final_link
        })
    return {"status": "success", "data": data}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    inv = get_inventory()
    sampled_items = ""
    
    if not inv.empty and 'كمية' in inv.columns:
        qty_series = pd.to_numeric(inv['كمية'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        available = inv[qty_series > 0]
        if not available.empty:
            sampled = available.sample(n=min(3, len(available)))
            sampled_items = "\n".join([f"- {sanitize_value(r.get('الصنف'))} (السعر: {sanitize_value(r.get('سعر1 كارت'), 'متاح')})" for _, r in sampled.iterrows()])
    
    formatted_answers = "\n".join([f"- {k}: {v}" for k, v in payload.mood_answers.items()])
    prompt = f"""
    {BASE_PHILOSOPHY}
    العميلة تشعر بطاقة ومزاج متمثل في:
    {formatted_answers}
    
    المنتجات الحقيقية المتوفرة حالياً في صالة العرض والمخازن لترشيحها هي:
    {sampled_items}
    
    صيغي قراءة لروحها ورشحي منتجاً واحداً بأسلوب ملكي فاخر، واكتبي اسم المنتج ورابط الشراء المتوقع له المرفق بالأعلى بوضوح.
    """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    inv = get_inventory()
    catalog = ""
    
    if not inv.empty and 'كمية' in inv.columns:
        qty_series = pd.to_numeric(inv['كمية'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        available = inv[qty_series > 0]
        if not available.empty:
            sampled = available.sample(n=min(5, len(available)))
            catalog = "\n".join([f"- {sanitize_value(r.get('الصنف'))} (السعر: {sanitize_value(r.get('سعر1 كارت'), 'متاح')})" for _, r in sampled.iterrows()])

    prompt = f"""
    {BASE_PHILOSOPHY}
    المسار الاستشاري الحالي: {payload.category}
    المنتجات المتوفرة للبيع الفوري داخل المخازن الحية للبراند:
    {catalog}
    
    السياق السابق للمحادثة إذا وجد: {payload.history_context if payload.history_context else 'حوار جديد'}
    رسالة العميل الحالية: "{payload.text}"
    
    المطلوب: صياغة ديباجة استشارية جمالية ساحرة، مع اختيار أفضل منتج من قائمة المنتجات المتوفرة بالأعلى وكتابة اسمه ورابط اقتنائه المباشر صراحة بـ https.
    """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    prompt = f"""
    {BASE_PHILOSOPHY}
    أمامكِ صورة للعميلة وصورة لمنتج تجميلي مستهدف ومطروح بالمعارض.
    اسم وصنف المنتج الحالي: {payload.product_name_desc}
    
    تخيلي النتيجة الفلسفية والأثر البصري والحسي الساحر عند امتزاج هذا المنتج بملامحها وعينيها، وصيغي رداً عاطفياً ملكياً ممتلئاً بالحب يصف جودة وتأثير هذا الإطلال وحضورها الأخاذ.
    """
    contents = [prompt]
    img1 = parse_image(payload.user_selfie)
    img2 = parse_image(payload.product_image)
    if img1: contents.append(img1)
    if img2: contents.append(img2)
        
    res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res}
