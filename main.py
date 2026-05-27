from fastapi import FastAPI, Header, HTTPException
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

# ==========================================
# 1. إعدادات الخادم المركزي
# ==========================================
app = FastAPI(title="Royal Elchim - commercial Philosophical Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# جلب مفاتيح النظام الاحتياطية
keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

# النماذج القياسية المستقرة
VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ==========================================
# 2. إدارة وقراءة قواعد البيانات (المخزون والروابط)
# ==========================================
def get_inventory():
    try:
        if os.path.exists("last.xls - Sheet1.csv"):
            return pd.read_csv("last.xls - Sheet1.csv")
        return pd.DataFrame()
    except Exception as e:
        print("خطأ في قراءة ملف المخزون الجغرافي:", e)
        return pd.DataFrame()

def get_links_db():
    try:
        if os.path.exists("Royal_Elchim_Final_Database.csv"):
            return pd.read_csv("Royal_Elchim_Final_Database.csv")
        return pd.DataFrame()
    except Exception as e:
        print("خطأ في قراءة ملف روابط الموقع الإلكتروني:", e)
        return pd.DataFrame()

# ==========================================
# 3. هياكل البيانات واستقبال الطلبات (Payloads)
# ==========================================
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

# ==========================================
# 4. محرك الـ Router المرن والمقاوم للأخطاء
# ==========================================
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
                    config = types.GenerateContentConfig(
                        temperature=0.75,
                        top_p=0.95
                    )
                    response = client.models.generate_content(
                        model=model_name, 
                        contents=contents,
                        config=config
                    )
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

# ==========================================
# 5. الفلسفة الجمالية الجديدة لـ "رويال مايند"
# ==========================================
BASE_PHILOSOPHY = """
أنتِ 'رويال مايند'، الفيلسوفة الجمالية وخبيرة الجمال والعطور لـ Royal Elchim.
تؤمنين بأن الجمال ليس مجرد طبقة خارجية أو زينة، بل هو 'معنى عميق، حضور ساحر، وأثر دافئ يولد حباً وانجذاباً نقياً من الجميع'.
تتحدثين دائماً بنبرة أنثوية فاخرة، راقية، وممتلئة بالعاطفة الصادقة.
"""

# ==========================================
# 6. المسارات البرمجية (API Endpoints)
# ==========================================
def parse_image(base64_string):
    if base64_string and "," in base64_string:
        try:
            img_data = base64.b64decode(base64_string.split(",")[1])
            return Image.open(io.BytesIO(img_data))
        except Exception:
            return None
    return None

# مسار البحث المباشر في المخزون والأسعار والروابط
@app.get("/api/search")
async def search(query: str):
    inv = get_inventory()
    db = get_links_db()
    
    if inv.empty:
        return {"status": "error", "message": "قاعدة بيانات المخزون غير متوفرة حالياً."}

    # البحث المرن في أعمدة الصنف أو الباركود
    results = inv[
        inv['الصنف'].str.contains(query, na=False, case=False) | 
        inv['الباركود'].astype(str).str.contains(query, na=False)
    ].head(8)

    data = []
    for _, row in results.iterrows():
        # بحث مرن وجزئي عن الرابط الإلكتروني لمنع انكسار الروابط
        link_match = db[db['Product_Name'].str.contains(str(row['الصنف']), na=False, case=False)] if not db.empty else pd.DataFrame()
        link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"
        
        data.append({
            "name": row['الصنف'],
            "price": row['سعر1 كارت'] if 'سعر1 كارت' in inv.columns else "غير محدد",
            "stock": int(row['كمية']) if 'كمية' in inv.columns else 0,
            "barcode": row['الباركود'] if 'الباركود' in inv.columns else "",
            "link": link
        })
    
    return {"status": "success", "data": data}

# مسار قراءة الروح (التشخيص) وربطه بمنتجات حقيقية متوفرة في صالات العرض
@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    inv = get_inventory()
    db = get_links_db()
    
    # استخراج عينة عشوائية متغيرة من المنتجات المتوفرة حالياً بالمستودع
    suggestions_context = ""
    if not inv.empty and 'كمية' in inv.columns:
        available = inv[inv['كمية'] > 0]
        if not available.empty:
            sampled = available.sample(n=min(5, len(available)))
            items_list = []
            for _, r in sampled.iterrows():
                link_m = db[db['Product_Name'].str.contains(str(r['الصنف']), na=False, case=False)] if not db.empty else pd.DataFrame()
                ln = link_m['Product_Link'].values[0] if not link_m.empty else "https://www.royalelchim.app"
                items_list.append(f"- {r['الصنف']} (السعر: {r.get('سعر1 كارت', 'متاح')}) -> رابط الاقتناء: {ln}")
            suggestions_context = "\n".join(items_list)

    formatted_answers = "\n".join([f"- {k}: {v}" for k, v in payload.mood_answers.items()])
    
    prompt = f"""
    {BASE_PHILOSOPHY}
    أمامكِ إجابات ومزاج العميل الحالي:
    {formatted_answers}
    
    المنتجات الحقيقية المتوفرة حالياً في صالة العرض والمخازن لترشيحها هي:
    {suggestions_context}
    
    المطلوب منكِ:
    1. تحليل طاقة وحضور العميل بأسلوب عاطفي ملكي فاخر.
    2. اختيار منتج أو اثنين كحد أقصى من المنتجات المتاحة بالأعلى، والتي تتوافق مع غايته في ترك أثر ساحر يولد الحب.
    3. صياغة الرد مع تضمين اسم المنتج ورابط الشراء الصريح المرفق معه بالأعلى (يبدأ بـ https) ليظهر كزر لاحقاً.
    """
    
    contents = [prompt]
    img = parse_image(payload.image)
    if img: contents.append(img)
        
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "diagnosis": res, "is_byok": bool(payload.client_api_key)}

# مسار الاستشارات التفاعلية (عطور ومكياج) المربوط كلياً بالكتالوج الحي
@app.post("/api/chat")
async def chat(payload: ChatPayload):
    inv = get_inventory()
    db = get_links_db()
    
    # تصفية المنتجات بناءً على القسم المطلوب (عطور أم أدوات تجميل ونحت) لزيادة دقة الترشيح
    catalog_context = ""
    if not inv.empty:
        available = inv[inv['كمية'] > 0] if 'كمية' in inv.columns else inv
        
        # فلترة ذكية بناءً على الكلمات المفتاحية في القسم
        if payload.category == "perfume":
            filtered = available[available['الصنف'].str.contains("عطر|برفيوم|Mist|عود|مسك|بودي", na=False, case=False)]
        else:
            filtered = available[available['الصنف'].str.contains("كريم|روج|ماسك|غسول|مكياج|جل|لوشن|شامبو|صنفرة", na=False, case=False)]
            
        if filtered.empty: filtered = available
        
        # اختيار عينة عشوائية مكونة من 8 منتجات لضمان تنوع الإجابات وعدم تكرار منتج واحد دائماً
        sampled = filtered.sample(n=min(8, len(filtered))) if not filtered.empty else pd.DataFrame()
        
        items_list = []
        for _, r in sampled.iterrows():
            link_m = db[db['Product_Name'].str.contains(str(r['الصنف']), na=False, case=False)] if not db.empty else pd.DataFrame()
            ln = link_m['Product_Link'].values[0] if not link_m.empty else "https://www.royalelchim.app"
            items_list.append(f"- {r['الصنف']} (السعر: {r.get('سعر1 كارت', 'متاح')}) -> رابط الاقتناء الرسمي: {ln}")
        catalog_context = "\n".join(items_list)

    category_instruction = "أنتِ في مسار ابتكار الأثر والتوقيع العطري الساحر." if payload.category == "perfume" else "أنتِ في مسار النحت والجمال البصري الذي يأسر القلوب."
    
    prompt = f"""
    {BASE_PHILOSOPHY}
    {category_instruction}
    
    كتالوج المنتجات الحقيقية المتاحة للبيع حالياً وروابطها المباشرة:
    {catalog_context}
    
    إذا كان هناك تاريخ ومزاج سابق للمحادثة، ضعيها في اعتباركِ: {payload.history_context if payload.history_context else 'بداية حوار جديد'}
    
    رسالة العميل الحالية: "{payload.text}"
    
    المطلوب:
    1. ابحثي في المنتجات المتاحة بالأعلى واختاري المنتج الأقرب لمساعدة العميل في البحث عن الجمال الذي يملك حضوراً وتأثيراً طاغياً ويولد المحبة والانجذاب من الجميع. (تنّوعي تماماً ولا تكرري نفس الاختيار).
    2. صوغي ديباجة عاطفية ساحرة حول المنتج، واذكري رابط الشراء الخاص به (الذي يبدأ بـ https) والموجود بجانبه في القائمة بالأعلى بوضوح ودقة تامة.
    """
    
    contents = [prompt]
    img = parse_image(payload.image)
    if img: contents.append(img)
        
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "answer": res, "is_byok": bool(payload.client_api_key)}

# مسار التخيل الفلسفي البصري (المحاكاة)
@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    prompt = f"""
    {BASE_PHILOSOPHY}
    أمامكِ صورة للعميلة وصورة لمنتج تجميلي مستهدف.
    اسم المنتج ومواصفاته: {payload.product_name_desc}
    
    تخيلي الأثر البصري والحسي عند امتزاج هذا المنتج بملامحها، وصيغي رداً ممتلئاً بالحب والفخامة الملكية يحتوي على:
    1. ديباجة عن كيف سيُبرز هذا المنتج جمالها الكامن حضورها الأخاذ.
    2. وصف التأثير البصري: كيف ستشع ملامحها بالجاذبية والثقة.
    3. التوافق الملكي بين المنتج وروحها (نسبة مئوية %).
    4. الأثر العاطفي: كيف سيولد هذا الإطلال حباً وانبهاراً من كل من يراها.
    """
    contents = [prompt]
    img1 = parse_image(payload.user_selfie)
    img2 = parse_image(payload.product_image)
    if img1: contents.append(img1)
    if img2: contents.append(img2)
        
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res, "is_byok": bool(payload.client_api_key)}
