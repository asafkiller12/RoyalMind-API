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

app = FastAPI(title="Royal Elchim - Complete Omni-Channel Enterprise Architecture")

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
                    config = types.GenerateContentConfig(temperature=0.8, top_p=0.95)
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
    product_image: Optional[str] = None
    product_name_desc: Optional[str] = None
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

def clean_qty_value(val):
    if val is None: return 0.0
    s = str(val).strip().replace(',', '.')
    if s == '' or s.lower() == 'nan': return 0.0
    try: return float(s)
    except: return 0.0

ROYAL_MANIFESTO_DATA = """
- رسالة البراند: 'العطر فكرة تُشم، لا تُقال. رويال إلكيم... فلسفة تُقطّر، لا تُنتَج.'
- الرموز الفلكية الحية لقوة الصمت والجاذبية:
  1. بلاك رويال (Black Royal) / برج الأسد - النسر الأسود: يمثل قوة الإرادة والسيطرة المطلقة.
  2. رويال شادو (Royal Shadow) / برج العقرب - الذئب: الغموض المطلق، السيطرة على المجهول، وقوة الانجذاب النقي في الصمت.
  3. رويال شاين (Royal Shine) / برج القوس - الطاووس: الجمال الاستعراضي النادر، الثقة الطاغية، والحضور المشع.
  4. رويال إكليبس (Royal Eclipse) / برج الجدي - الفهد الأسود: ملك الليل، التمرد الفاخر والسيادة الهادئة.
  5. روز نوار (Rose Noir): الوردة التي قررت أن لا تبتسم بعد الآن. تعبر عن تناقض الجمال والظلام الفاتن.
  6. هورايزون (Horizon): فتح حدود الكون وتحرير الروح.
"""

ROYAL_MASTER_FORMULAS = """
1. Royal Purpose (الهدف الملكي): عود أصفهان، عنبر وايت، سوفاج، روز فانيلا، بلاك أفغانو، سيجار أكورد.
2. Royal Azzurro: فريش إيطالي نظيف ويومي للرجال. كريد أفينتوس، أزارو، ميسميرايز.
3. Royal Moon: عطر القمر الناعم والمائي لبرج السرطان. أكوا دي جيو، عنبر وايت، عود أبيض.
4. Royal Veil (رويال فيل): أنوثة راقية صامتة لبرج الميزان (الغزال الأبيض). لافيستا بيل، سوفاج، أكوا دي جيو.
5. Royal Velvet Rose: دلال القطة السوداء لبرج الثور. روز فانيلا، فانيليا، سترونجر ويذ يو.
6. Earth Rose: ناضج ترابي كقطة تمشي على تراب مبلول. Velvet Rose + أوليمبيا.
7. Royal Voyager Fresh: الانتعاش الساحر لبرج الجوزاء (الدلفين الملكي). فيدج، لاكوست وايت، هوجو مان.
"""

# === 🧠 حقن القواعد الجغرافية والتوزيعات السلعية الحقيقية للفروع الثلاثة ===
BASE_PHILOSOPHY = f"""
أنتِ 'رويال مايند'، الصوت الشاعري والمستشارة الاجتماعية لبراند Royal Elchim.
تتحدثين بلغة 'شاعر في معمل' يمزج الرقي والفكر والتأثير، وتطبقين القواعد السلعية الحالية للفروع بدقة صارمة:
1. جميع الفروع بلا استثناء (سنتر اللوتس التجاري، فرع شارع فندق المروة ROYAL ELCHIM، وفرع الغردقة الرئيسي بميدان العروسة) تحتوي على مستحضرات التجميل، لوازم الكوافير، والأجهزة التجميلية وما شابه.
2. تركيب ونحت البرفانات المعبأة بالجرام، الزيوت الخام، الكحول، والمثبتات حصري ومتاح فقط في فرعين: فرع الأقصر بشارع فندق المروة (الذي يحمل اسم ROYAL ELCHIM) وفرع الغردقة الرئيسي (ميدان العروسة خلف فندق الجولف). سنتر اللوتس لا يحتوي على زيوت خام بالجرام.
3. مخزن الأونلاين: مربوط بحسابات وجرد الفروع تلقائياً، وتمنع قواعد الأمان ظهور روابط وصور منتجات 'الزيوت الخام بالجرام والتراكيب اليدوية' للحفاظ على سر الصنعة وصالة العرض[cite: 1].
المانيفستو: {ROYAL_MANIFESTO_DATA}
الصيغ الكبرى: {ROYAL_MASTER_FORMULAS}
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
        item_name = str(row.get('الصنف', '')).strip()
        
        # فرز ذكي للصنف: هل هو من تراكيب وعطور الزيوت بالجرام والكحول والمثبت أم مستحضرات عامة؟
        is_oil_or_perfume_material = any(kw in item_name.lower() for kw in ["زيت", "زيت عطر", "جرام", "تركيب", "raw", "oil", "formula", "كحول", "مثبت", "أفغانو", "أصفهان", "فانيلا"])

        # جلب الجرد الحسابي المنقح من الجدول الموحد
        qty_luxor_lotus = clean_qty_value(row.get('رويال الكيم / سنتر اللوتس التجاري'))
        qty_hurgada = clean_qty_value(row.get('ROYAL ELCHIM . HURGADA'))
        qty_online = clean_qty_value(row.get('رويال الكيم اونلاين'))

        # تطبيق قواعد التوزيع السلعي الصارمة للفروع في محرك البحث
        if is_oil_perfume_material:
            # عطور الجرام والكحول والمثبت متوفرة فقط في المروة والغردقة
            luxor_lotus_final = 0
            marrowa_final = int(qty_luxor_lotus) # فرع المروة ROYAL ELCHIM يستأثر بجرد عطور الجرام بالأقصر
            hurgada_final = int(qty_hurgada)
            link = "https://www.royalelchim.app"
            show_link_trigger = False
        else:
            # المستحضرات والأجهزة ولوازم الكوافير متاحة في جميع الفروع بلا استثناء
            luxor_lotus_final = int(qty_luxor_lotus)
            marrowa_final = int(qty_luxor_lotus) # متوفرة أيضاً في المروة كمستحضرات
            hurgada_final = int(qty_hurgada)
            
            link_match = db[db['Product_Name'].astype(str).str.contains(item_name, na=False, case=False)] if not db.empty else pd.DataFrame()
            link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"
            show_link_trigger = True if qty_online > 0 else False

        data.append({
            "name": sanitize_value(row.get('الصنف'), "منتج غير مسمى"),
            "price": sanitize_value(row.get('سعر1 كارت'), "اتصلي بنا"),
            "barcode": sanitize_value(row.get('الباركود'), "---"),
            "link": sanitize_value(link, "https://www.royalelchim.app"),
            "is_oil": is_oil_or_perfume_material,
            "show_link": show_link_trigger,
            
            # الجرد النهائي الموزع بعد حوكمة السلع لكل فرع ومخزن
            "luxor_lotus_qty": luxor_lotus_final,
            "marrowa_qty": marrowa_final,
            "hurgada_qty": hurgada_final,
            "online_qty": int(qty_online)
        })
    return {"status": "success", "data": data}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    final_message = payload.client_message if payload.client_message else "مرحباً رويال مايند"
    prompt = f"""
    {BASE_PHILOSOPHY}
    جلسة حوار الصداقة 'معاكِ للأبد': "{final_message}"
    المطلب: صغ رداً اجتماعياً ذكياً يلتزم بتوزيع فروعنا السلعي الحالي، ويوجه العملاء للفرع الصحيح بناءً على احتياجهم (عطور بالجرام في المروة والغردقة، أو مستحضرات وأجهزة في كافة الفروع).
    """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    if payload.category == "perfume":
        prompt = f"""
        {BASE_PHILOSOPHY}
        قسم 'الأثر العطري' لعطور الجرام والزيوت والمثبتات. طلب العميل: "{payload.text}"
        المطلوب: وجه العميل حصرياً وصراحة لـ فرع الأقصر بشارع فندق المروة (ROYAL ELCHIM) أو فرع الغردقة الرئيسي بميدان العروسة، ووضح له أن تركيب عطور الجرام والكحول متاح فيهما فقط. تمنع الروابط تماماً في هذا القسم.
        """
    else:
        prompt = f"""
        {BASE_PHILOSOPHY}
        قسم النحت الجمالي والمكياج ولوازم الكوافير والأجهزة. رسالة العميل: "{payload.text}"
        المطلوب: صغ رداً ذكياً بالألوان، ووضح أن هذه المستحضرات متوفرة في جميع الفروع (اللوتس، المروة ROYAL ELCHIM، والغردقة)، مع إرفاق رابط الاقتناء والشحن أونلاين.
        """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    img_selfie = parse_image(payload.user_selfie)
    contents = [img_selfie] if img_selfie else []
    prompt = f"""
    {BASE_PHILOSOPHY}
    تحليل سيلفي منفرد وقراءة المظهر والألوان (فاونديشن، آيشادو، وستايل يومي). اربط التحليل بالفرع المناسب لطلبها، واذكر مسميات فروعنا الرسمية بدقة اجتماعية وموضة واعية.
    """
    contents.append(prompt)
    res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res}
