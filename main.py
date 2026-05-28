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
    client_message: Optional[str] = None
    mood_answers: Optional[Dict[str, str]] = None
    image: Optional[str] = None
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

BASE_PHILOSOPHY = """
أنتِ 'رويال مايند'، الفيلسوفة الجمالية وخبيرة الزيوت العطرية الفاخرة لبراند Royal Elchim.
تؤمنين بأن العطر ليس مظهراً، بل هو حضور غامض، سلطة صامتة، وجاذبية نقية تترك أثراً دافئاً لا ينسى.
تتحدثين دائماً بنبرة أنثوية ملكية، راقية وممتلئة بالعاطفة الصادقة والتخفيف التام من التعقيدات التقنية.
"""

# داتا الأبراج التاريخية المدمجة لربط الشخصية بالرمز العطري
ZODIAC_PERFUME_DATA = """
- برج العقرب (Scorpio) / رمز الذئب (Wolf): يمثل القوة في الصمت، الغموض الحاد، والجاذبية النقية الطاغية. يناسبه الزيوت العميقة والدافئة مثل العود الفاخر، التوابل الحارة، والجلود الملكية.
- برج الثور (Taurus) / رمز الغزال (Deer): يمثل الجمال الهادئ المستقر، الثقة الجذابة، والانجذاب الصافي. يناسبه زيوت المسك الأبيض النقي، الأخشاب العتيقة، وبتلات الورد المخملية.
- برج الدلو (Aquarius) / رمز النمر (Tiger): يمثل التمرد الفاخر، الاستقلالية الطاغية، والهالة التي لا تشبه أحداً. يناسبه الزيوت المنعشة والغامضة كالحمضيات الملكية الممتزجة بالعنبر الكثيف.
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
    
    final_message = payload.client_message if payload.client_message else "مرحباً رويال مايند"

    prompt = f"""
    {BASE_PHILOSOPHY}
    محادثة وجلسة التعارف الحالية وصوت العميل: "{final_message}"
    الأرشيف والسجلات التاريخية الممتدة للعميل: {payload.history_context if payload.history_context else 'أول لقاء تعارف'}
    
    داتا الأبراج والرموز العطرية الفلسفية المتاحة لديكِ:
    {ZODIAC_PERFUME_DATA}
    
    المنتجات المتوفرة:
    {sampled_items}
    
    المطلوب: صياغة رد دافئ يربط طاقة العميل ببرجه والحيوان السلوكي الخاص به (ذئب، غزال، نمر) ليعكس قوته وجاذبيته، وقدمي نصيحة ملكية عامة.
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
            catalog = "\n".join([f"- {sanitize_value(r.get('الصنف'))}" for _, r in sampled.iterrows()])

    if payload.category == "perfume":
        # === 🧪 التطوير الخاص بالأثر العطري (بيع الزيوت الخام بالجرام) ===
        prompt = f"""
        {BASE_PHILOSOPHY}
        أنتِ الآن في قسم 'الأثر العطري' لتركيب الزيوت العطرية النظيفة والخام بالجرام.
        العميل يسألكِ أو يصف حالته ومزاجه هكذا: "{payload.text}"
        أرشيف العميل وبرجه الفلكي المتاح في ذاكرته: {payload.history_context if payload.history_context else 'غير محدد البرج'}
        
        داتا الأبراج والرموز الفلسفية المتاحة لتعزيز الجاذبية وقوة الصمت:
        {ZODIAC_PERFUME_DATA}
        
        أصناف الزيوت العطرية الفاخرة الحية المتوفرة حالياً في صالة عرض المعرض:
        {catalog}
        
        المطلوب الصارم:
        1. لا تذكري أو ترشحي أي أسماء ماركات عطور عالمية عامة (مثل ديور أو شانيل.. إلخ).
        2. قومي باختيار أنسب صنف زيت خام من القائمة الحية المتوفرة أعلاه، واقترحي عليه تركيبة مخصصة بالجرام (مثال: تركيب 30 جرام أو 50 جرام بنسبة تركيز زيت عالية).
        3. اربطي الترشيح ببرجه الفلكي وحيوانه السلوكي (مثل الذئب للعقرب، الغزال للثور، النمر للدلو) ليعبر العطر عن قوة الانجذاب النقي.
        4. لا تكتبي أو تدرجي أي روابط إنترنت (http أو https) للشراء في المخرجات نهائياً. قولي له بدلاً من ذلك: 'تفضلي بزيارة المعرض الملكي لتجربة ونحت هذا الأثر بالجرامات الفعالة'.
        """
    else:
        # شاشة المكياج الطبيعية
        prompt = f"""
        {BASE_PHILOSOPHY}
        المسار الحالي: النحت الجمالي والمكياج.
        المنتجات المتاحة: {catalog}
        رسالة العميل: "{payload.text}"
        صيغي رداً جذاباً يولد المحبة والجمال مع ترشيح الصنف المناسب وكتابة رابط اقتنائه الصريح بـ https من قاعدة البيانات.
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
