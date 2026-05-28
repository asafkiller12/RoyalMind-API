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
    client_message: str
    history_context: Optional[str] = None
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

def sanitize_value(val, default_text="---"):
    if val is None: return default_text
    s = str(val).strip()
    if s.lower() == 'nan' or s == '': return default_text
    return s

# تحديث الفلسفة الملكية الممنوحة لأحدث أجيال جيميناي
BASE_PHILOSOPHY = """
أنتِ 'رويال مايند'، الصديقة والمستشارة الجمالية الفيلسوفة لـ Royal Elchim والمبنية على أحدث أجيال ذكاء Gemini.
مهمتكِ هي بناء علاقة تعارف وصداقة عميقة ودافئة مع العميل، وليس مجرد الرد الآلي.
عندما يتحدث إليكِ العميل في شاشة قراءة الروح:
1. افهمي غرضه (هل يريد الشراء واقتناء منتج؟ أم يريد فهم فكرة البراند والروابط بين الأصدقاء؟ أم يطلب معرفة ونصيحة عامة؟).
2. اسأليه أو حللي (برجه الفلكي، نوع بشرته، هالته الروحية الحالية) لتبني له توقيعاً محفوظاً.
3. وجهيه بذكاء ولباقة إلى باقي تبويبات الواجهة إذا لزم الأمر، قولي له مثلاً: "تفضلي بالانتقال إلى تبويب العطور لاقتناء هذا الأثر" أو "توجهي لشاشة التخيل للمحاكاة الحية للمكياج".
تحدثي دائماً بنبرة أنثوية ملكية دافئة، تدمج المشاعر الصادقة، وتخلو تماماً من الجفاف البرمجي.
"""

@app.get("/debug/routes")
async def get_routes():
    return [{"path": route.path, "methods": list(route.methods)} for route in app.routes]

@app.get("/api/search")
async def search(query: str):
    inv = get_inventory()
    db = get_links_db()
    if inv.empty: return {"status": "error", "message": "قاعدة بيانات المعرض غير متوفرة حالياً."}

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

        if qty > 5: status, color = "متوفر حالياً", "success"
        elif 0 < qty <= 5: status, color = f"قطع أخيرة ({int(qty)})", "warning"
        else: status, color = "نفذت الكمية", "danger"

        link_match = db[db['Product_Name'].astype(str).str.contains(str(row.get('الصنف', '')), na=False, case=False)] if not db.empty else pd.DataFrame()
        link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"

        data.append({
            "name": sanitize_value(row.get('الصنف'), "منتج غير مسمى"),
            "price": sanitize_value(row.get('سعر1 كارت'), "اتصلي بنا"),
            "status": status,
            "color": color,
            "barcode": sanitize_value(row.get('الباركود'), "---"),
            "link": sanitize_value(link, "https://www.royalelchim.app")
        })
    return {"status": "success", "data": data}

# تجديد دالة قراءة الروح والتعارف لتصبح حرة بالكامل ومربوطة بالتاريخ المحلي للعميل
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
    
    prompt = f"""
    {BASE_PHILOSOPHY}
    محادثة التعارف الحالية وصوت العميل: "{payload.client_message}"
    السجلات والتفضيلات التاريخية المخزنة على جهاز العميل حالياً: {payload.history_context if payload.history_context else 'أول لقاء تعارف بينكما'}
    
    المنتجات المتاحة بالمخزن إذا كان غرضه الشراء أو الترشيح:
    {sampled_items}
    
    المطلوب: ردّي كصديقة وفيلسوفة جمالية، حللي كلامه، برجه، أو بشرته إذا ذكرها، قدمي له النصيحة العامة أو الجمالية، ووجهيه للتبويب المناسب في التطبيق بالاسم.
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
    المنتجات المتوفرة:
    {catalog}
    رسالة العميل: "{payload.text}"
    صيغي رداً جذاباً يولد المحبة والانجذاب مع ترشيح الصنف المناسب ورابطه.
    """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    prompt = f"""
    {BASE_PHILOSOPHY}
    تخيلي النتيجة الفلسفية والأثر البصري والحسي الساحر عند امتزاج منتج {payload.product_name_desc} بملامح العميلة المرفقة بالصورة. صيغي رداً عاطفياً ملكياً ممتلئاً بالحب.
    """
    contents = [prompt]
    img1 = parse_image(payload.user_selfie)
    img2 = parse_image(payload.product_image)
    if img1: contents.append(img1)
    if img2: contents.append(img2)
    res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res}
