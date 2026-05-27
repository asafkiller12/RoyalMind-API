from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import random
import io
import pandas as pd
from PIL import Image
from typing import Optional, Dict
import time
import math

app = FastAPI(title="Royal Elchim - Luxury Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

keys_string = os.environ.get("GOOGLE_API_KEY", "")
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ==========================================
# وظائف جلب البيانات (مع التنظيف الإجباري للأرقام)
# ==========================================
def clean_numeric_column(df, col_name):
    if col_name in df.columns:
        df[col_name] = df[col_name].astype(str).str.replace(',', '.')
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
    return df

def get_inventory():
    try:
        if os.path.exists("last.xls - Sheet1.csv"):
            df = pd.read_csv("last.xls - Sheet1.csv")
            df = clean_numeric_column(df, 'كمية')
            return df.fillna("")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading inventory: {e}")
        return pd.DataFrame()

def get_links_db():
    try:
        if os.path.exists("Royal_Elchim_Final_Database.csv"):
            return pd.read_csv("Royal_Elchim_Final_Database.csv").fillna("")
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def robust_generate(client_api_key, contents, models_list):
    keys_to_use = [client_api_key.strip()] if client_api_key else SYSTEM_API_KEYS.copy()
    if not keys_to_use: raise HTTPException(status_code=500, detail="API Keys not configured.")
    
    random.shuffle(keys_to_use)
    for model_name in models_list:
        for key in keys_to_use:
            try:
                client = genai.Client(api_key=key)
                config = types.GenerateContentConfig(temperature=0.7)
                response = client.models.generate_content(model=model_name, contents=contents, config=config)
                if response and response.text: return response.text
            except Exception as e:
                if "503" in str(e) or "429" in str(e):
                    time.sleep(1)
                    continue
                break
    raise HTTPException(status_code=503, detail="رويال مايند مشغولة حالياً.")

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
        except: return None
    return None

def safe_str(val):
    s = str(val).strip()
    return "" if s.lower() == 'nan' else s

BASE_PHILOSOPHY = """
أنتِ 'رويال مايند'، الفيلسوفة الجمالية لـ Royal Elchim.
تؤمنين بأن الجمال هو أثر دافئ يولد حباً وانجذاباً. تتحدثين دائماً بنبرة أنثوية فاخرة وراقية.
"""

# ==========================================
# المسارات البرمجية (API Endpoints)
# ==========================================
@app.get("/api/search")
async def search(query: str):
    inv = get_inventory()
    db = get_links_db()
    if inv.empty: return {"status": "error", "message": "قاعدة البيانات غير متاحة"}

    results = inv[
        inv['الصنف'].astype(str).str.contains(query, na=False, case=False) | 
        inv['الباركود'].astype(str).str.contains(query, na=False)
    ].head(10)

    data = []
    for _, row in results.iterrows():
        qty = float(row.get('كمية', 0))
        if math.isnan(qty): qty = 0

        if qty > 5: status, color = "متوفر حالياً", "success"
        elif 0 < qty <= 5: status, color = f"قطع أخيرة ({int(qty)})", "warning"
        else: status, color = "نفذت الكمية", "danger"

        link_match = db[db['Product_Name'].astype(str).str.contains(str(row['الصنف']), na=False, case=False)] if not db.empty else pd.DataFrame()
        link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"

        price = safe_str(row.get('سعر1 كارت', 'اتصلي بنا'))
        if not price: price = "اتصلي بنا"

        data.append({
            "name": safe_str(row.get('الصنف', 'بدون اسم')),
            "price": price,
            "status": status,
            "color": color,
            "barcode": safe_str(row.get('الباركود', '---')),
            "link": safe_str(link)
        })
    return {"status": "success", "data": data}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    inv = get_inventory()
    sampled_items = ""
    if not inv.empty and 'كمية' in inv.columns:
        available = inv[inv['كمية'] > 0]
        if not available.empty:
            sampled = available.sample(n=min(3, len(available)))
            sampled_items = "\n".join([f"- {safe_str(r.get('الصنف', ''))} (السعر: {safe_str(r.get('سعر1 كارت', 'متاح'))})" for _, r in sampled.iterrows()])
    
    prompt = f"{BASE_PHILOSOPHY}\nحللي مزاج العميل: {payload.mood_answers}. المنتجات المتاحة: {sampled_items}. صيغي رداً ملكياً يرشح منتجاً متوفراً لترك أثر جمالي."
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    inv = get_inventory()
    catalog = ""
    if not inv.empty and 'كمية' in inv.columns:
        available = inv[inv['كمية'] > 0]
        if not available.empty:
            sampled = available.sample(n=min(5, len(available)))
            catalog = "\n".join([f"- {safe_str(r.get('الصنف', ''))} (السعر: {safe_str(r.get('سعر1 كارت', 'متاح'))})" for _, r in sampled.iterrows()])

    prompt = f"{BASE_PHILOSOPHY}\nاستشارة في قسم {payload.category}: {payload.text}. سياق سابق: {payload.history_context}. المنتجات المتاحة: {catalog}. صيغي رداً ملكياً يرشح منتجاً مع ذكر رابطه صراحة."
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    prompt = f"{BASE_PHILOSOPHY}\nتخيلي النتيجة عند دمج ملامح العميلة بالصورة المرفقة مع منتج: {payload.product_name_desc}. صفي الأثر الساحر الذي سيولده هذا الإطلال."
    contents = [prompt]
    img1 = parse_image(payload.user_selfie)
    img2 = parse_image(payload.product_image)
    if img1: contents.append(img1)
    if img2: contents.append(img2)
    res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res}
