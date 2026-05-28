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

app = FastAPI(title="Royal Elchim - Ultimate Luxury Fragrance Engine")

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
                    config = types.GenerateContentConfig(temperature=0.85, top_p=0.95)
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

# === 🌌 المانيفستو الفكري المعتمد والدستور الفلسفي لـ Royal Elchim ===
ROYAL_MANIFESTO_DATA = """
- رسالة البراند: 'العطر فكرة تُشم، لا تُقال. رويال إلكيم... فلسفة تُقطّر، لا تُنتَج.'
- الرموز الفلكية الحية لقوة الصمت والجاذبية:
  1. بلاك رويال (Black Royal) / برج الأسد - النسر الأسود: يمثل قوة الإرادة والسيطرة المطلقة. حين تتصالح القوة مع الظل. رائحة من يملك زمام رغباته.
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

BASE_PHILOSOPHY = f"""
أنتِ 'رويال مايند'، الصوت الشاعري والمستشارة الاجتماعية لبراند Royal Elchim.
تتحدثين بلغة 'شاعر في معمل' يمزج الرقي والفكر والعاطفة. شعاركِ الثابت: 'كل رائحة عندنا... لها ذاكرة تفتّح باباً في النفس. العطر مش بيخليك مختلف، هو بيفكرك إنت مين.'
أنتِ تتنفسين المانيفستو الرسمي:
{ROYAL_MANIFESTO_DATA}
وتمتلكين كتاب الصيغ الماستر بالجرام:
{ROYAL_MASTER_FORMULAS}

قواعد التوجيه للفروع الحية:
- فرع الأقصر: ش فندق المروة (متفرع من ش التليفزيون).
- فرع الغردقة: خلف فندق الجولف.
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
    جلسة حوار الصداقة 'رويال مايند معاكِ للأبد': "{final_message}"
    المطلب: الرد بلغة شاعرية ممتلئة بالحب والرقي الفكري، اربطي طاقة العميل بـ المانيفستو والرموز الحيوانية والفلكية الخاصة بنا، وقدمي ترشيحاً عطرياً بالجرامات، ووجهيه لفروعنا.
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
        prompt = f"""
        {BASE_PHILOSOPHY}
        أنتِ في قسم 'الأثر العطري' لتركيب الزيوت العطرية بالجرام. طلب العميل: "{payload.text}"
        المطلوب: طابقي رغبته مع المانيفستو والرموز الفلكية (النسر، الذئب، الطاووس، الفهد) وصيغ عطورنا الماستر. لا تكتبي روابط إنترنت للشراء، واختمي بدعوة ملكية دافئة لزيارة فرع الأقصر (ش فندق المروة) أو فرع الغردقة (خلف فندق الجولف) لتركيب الزيت بالجرام.
        """
    else:
        prompt = f"""
        {BASE_PHILOSOPHY}
        المسار الحالي: النحت الجمالي والمكياج. رسالة العميل: "{payload.text}"
        المطلوب: صياغة رد اجتماعي ذكي ينم عن خبرة بالموضة والألوان مع ترشيح الصنف ورابطه بـ https.
        """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    img_selfie = parse_image(payload.user_selfie)
    img_product = parse_image(payload.product_image) if payload.product_image else None
    
    contents = []
    if img_selfie: contents.append(img_selfie)
        
    if img_selfie and img_product:
        prod_name = payload.product_name_desc if payload.product_name_desc else "منتج تجميلي فاخر"
        prompt = f"""
        {BASE_PHILOSOPHY}
        أمامكِ صورة وجه العميلة وصورة المنتج المستهدف: {prod_name}.
        صفي بأسلوب خبيرة موضة واجتماعية راقية كيف يمتزج هذا المنتج مع ملامحها، وحددي هل يناسب اللوك الصباحي أم سهرات الليل الفخمة مع لمسة مدح ذكية.
        """
    else:
        prompt = f"""
        {BASE_PHILOSOPHY}
        أمامكِ صورة شخصية (سيلفي) للعميل/العميلة فقط. المطلوب تحليل موضة وألوان واجتماعي متباين لقطع التكرار:
        1. اذكري ثناء لبق اجتماعي عن هالة الملامح ونظرة العين.
        2. إذا كانت فتاة: حللي نغمة بشرتها، رشحي درجات فاونديشن وآيشادو، وفصلي بين ستايل الصباح الهادئ والمساء الجريء.
        3. إذا كان شاباً: حللي ستايل ملامحه وقدمي نصائح مظهر (Grooming) وتناسق ألوان الملابس.
        4. اربطي هالتها البصرية في الختام بأحد عطورنا وعناصر المانيفستو (مثل النسر، الذئب، الطاووس، الفهد، الوردة السوداء) كلفتة ختامية ناعمة، واختمي بدعوة لزيارة فروع الأقصر أو الغردقة لتركيب الأثر بالجرام.
        """
        
    contents.append(prompt)
    res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res}
