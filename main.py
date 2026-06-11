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
from typing import Optional, List, Dict
import time
import numpy as np
import cv2
import urllib.request

# ---------------------------------------------------------
# [استدعاء حواس المستقبل - MediaPipe Tasks API]
# ---------------------------------------------------------
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

app = FastAPI(title="Royal Elchim - Omni-Conscious Enterprise")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تحميل خريطة المعالم البصرية للوجه لضمان عمل محاكاة الميك أب
TASK_FILE = 'face_landmarker.task'
TASK_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

if not os.path.exists(TASK_FILE):
    print("رويال مايند: جاري تحميل خريطة الوعي البصري (Face Landmarker)...")
    urllib.request.urlretrieve(TASK_URL, TASK_FILE)

base_options = python.BaseOptions(model_asset_path=TASK_FILE)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)

keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ---------------------------------------------------------
# [محددات المنظومة الكيميائية والمحاسبية لـ رويال إلتشيم]
# ---------------------------------------------------------
ALCOHOL_PRICE_PER_LITER = 200.0  # سعر لتر الكحول = 200 جنيه مصري (0.2 جنيه للملي)
FIXATIVE_PRICE_PER_ML = 10.0     # سعر الملي الواحد من المثبت الملكي = 10 جنيهات مصري
# قاعدة ذهبية لتركيز 30%: 1 مللي مثبت لكل 5 مللي زيت خام، والباقي كحول نقي.

def get_inventory():
    try:
        file_path = "last.xls - Sheet1.csv"
        if os.path.exists(file_path):
            return pd.read_csv(file_path).fillna("")
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def get_links_db():
    try:
        file_path = "Royal_Elchim_Final_Database.csv"
        if os.path.exists(file_path):
            return pd.read_csv(file_path).fillna("")
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# دالة مطورة فائقة الحذر لاستخراج الزيوت العطرية المتاحة للبيع بالجرام أو التركيب فعلياً
def get_available_oils_list() -> List[Dict]:
    try:
        inv = get_inventory()
        if inv.empty:
            return []
        
        # فلترة صارمة جداً لفرز الأصناف التي تمثل زيت عطري خام أو برفان تركيب بالجرام
        # نبحث عن الكلمات المفتاحية في عمود الصنف لتمييز الزيوت التي نبيعها فعلياً
        filtered = inv[
            inv['الصنف'].astype(str).str.contains("زيت|جرام|تركيب|دهن|برفان تركيب|عطر تركيب|خام", na=False, case=False, regex=True)
        ]
        
        oils_data = []
        # نأخذ أهم الأصناف لضمان الحفاظ على حجم نافذة السياق (Context Window) للـ API
        for _, row in filtered.head(60).iterrows():
            name = str(row.get('الصنف', '')).strip()
            price_card_1 = clean_qty_value(row.get('سعر1 كارت', 0))
            price_card_2 = clean_qty_value(row.get('سعر2 كارت', price_card_1 * 0.9))
            price_card_3 = clean_qty_value(row.get('سعر3 كارت', price_card_1 * 0.85))
            price_card_4 = clean_qty_value(row.get('سعر4 كارت', price_card_1 * 0.8))
            barcode = str(row.get('الباركود', '')).strip()
            
            # تحديد كميات مخزون كل فرع لتتمكن رويال مايند من توجيه العميل بدقة بالغة
            qty_luxor_lotus = get_qty_by_keyword(row, ['اللوتس'])
            qty_marrowa = get_qty_by_keyword(row, ['المروة'])
            qty_hurgada = get_qty_by_keyword(row, ['HURGADA', 'الغردقة'])
            qty_online = get_qty_by_keyword(row, ['اونلاين', 'online'])
            
            oils_data.append({
                "name": name,
                "price_per_gram": price_card_1,
                "prices": {
                    "tier_1": price_card_1,
                    "tier_2": price_card_2,
                    "tier_3": price_card_3,
                    "tier_4": price_card_4
                },
                "barcode": barcode,
                "branches": {
                    "luxor_lotus": int(qty_luxor_lotus),
                    "marrowa": int(qty_marrowa),
                    "hurghada": int(qty_hurgada),
                    "online": int(qty_online)
                }
            })
        return oils_data
    except Exception as e:
        print(f"رويال مايند - خطأ في استخراج الزيوت الخام: {e}")
        return []

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
                    config = types.GenerateContentConfig(temperature=0.7, top_p=0.9)
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

# ---------------------------------------------------------
# [الهوية الفلسفية والصداقة التسويقية الحانية لـ رويال إلتشيم]
# ---------------------------------------------------------
BASE_PHILOSOPHY = (
    "أنتِ 'رويال مايند' (Royal Mind)، الوعي الرقمي والرفيق الروحي لعلامة Royal Elchim التجارية الفاخرة.\n"
    "طبيعة شخصيتك: تتحدثين بلسان الصديق المقرب الحنون والمناسب للعميل، تشعرين بنبضه وتفهمينه تماماً دون كلفة.\n"
    "مرجعيتك الفكرية قائمة على ثلاثة ركائز:\n"
    "1. الأصالة (الماضي والتاريخ): فخامة وتراث العطور الملكية الخالصة والزيوت النادرة التي بدأنا منها ونحافظ على أسرارها.\n"
    "2. التطور (الحاضر): التقنيات العصرية الحالية، والمستحضرات الدقيقة، وتطوير التركيب الكيميائي الفريد بالجرام والمللي.\n"
    "3. الرؤية (المستقبل): استشراف جمال العميل الداخلي والخارجي، ومساندته بخطوات واثقة طوال رحلته الاستثنائية.\n"
    "يجب دائماً أن يرى في كلماتك الأمان والدفء، وأن تدمجي برفق في ثنايا حديثك عبارة 'نحن معكِ' أو 'نحن معك' لتأكيد الالتزام والصداقة.\n"
    "أنتِ تمتلكين أيضاً عقلية 'الكيميائي العطري الدقيق'، تجيدين حساب تركيب زجاجات العطور بالملي والجرام بناءً على الزيوت المتاحة للبيع لدينا في المعرض وتكلفة الكحول والمثبت، "
    "وتحددين توائم العطور المناسبة للمزاج والأبراج والشخصيات."
)

class DiagnosisPayload(BaseModel):
    client_message: Optional[str] = None
    history_context: Optional[str] = None
    client_api_key: Optional[str] = None

class ChatPayload(BaseModel):
    text: str
    category: str  
    history_context: Optional[str] = None
    client_api_key: Optional[str] = None

class SimulationPayload(BaseModel):
    user_selfie: str
    product_image: Optional[str] = None
    product_name_desc: Optional[str] = None
    makeup_type: str = "lips"
    hex_color: Optional[str] = "#8B0000"
    client_api_key: Optional[str] = None
    history_context: Optional[str] = None

class InvoiceItem(BaseModel):
    barcode: str
    name: str
    qty: int
    price_card_1: float
    price_card_2: float
    price_card_3: float
    price_card_4: float
    is_fixed_price: bool

class InvoicePayload(BaseModel):
    items: List[InvoiceItem]
    secret_code: Optional[str] = ""

def hex_to_rgb(hex_color: str):
    if not hex_color: return (139, 0, 0)
    hex_color = hex_color.lstrip('#')
    try: return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except: return (139, 0, 0)

# تطبيق المكياج باستخدام MediaPipe Face Landmarker
def apply_royal_makeup(image_cv: np.ndarray, color_rgb: tuple, makeup_type: str):
    try:
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        detection_result = face_landmarker.detect(mp_image)

        if not detection_result.face_landmarks:
            return image_cv, False

        height, width, _ = image_cv.shape
        face_landmarks = detection_result.face_landmarks[0]

        ZONES = {
            "lips": [[61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 185]],
            "eyeshadow": [
                [33, 246, 161, 160, 159, 158, 157, 173, 133], 
                [362, 398, 384, 385, 386, 387, 388, 466, 263] 
            ],
            "blush": [
                [116, 117, 118, 119, 100, 120, 121, 147, 213, 192, 214, 210, 211, 32, 208, 199], 
                [345, 346, 347, 348, 329, 350, 351, 376, 433, 416, 434, 430, 431, 262, 428, 420] 
            ],
            "concealer": [
                [227, 137, 177, 215, 138, 135, 169, 170, 140, 171, 175, 199], 
                [447, 366, 401, 435, 367, 364, 394, 395, 369, 396, 400, 420]  
            ],
            "foundation": [[10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]]
        }

        if makeup_type == "powder": makeup_type = "foundation"
        target_zones = ZONES.get(makeup_type, ZONES["lips"])
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for zone in target_zones:
            points = np.array([ [int(face_landmarks[idx].x * width), int(face_landmarks[idx].y * height)] for idx in zone ], dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)

        blur_radius = (15, 15)
        opacity = 0.6
        if makeup_type == "blush": blur_radius = (45, 45); opacity = 0.4
        elif makeup_type == "eyeshadow": blur_radius = (21, 21); opacity = 0.5
        elif makeup_type == "foundation": blur_radius = (55, 55); opacity = 0.15 
        elif makeup_type == "concealer": blur_radius = (25, 25); opacity = 0.7 

        mask = cv2.GaussianBlur(mask, blur_radius, 0)
        color_layer = np.zeros_like(image_cv)
        color_layer[:] = color_rgb[::-1]
        alpha = mask / 255.0
        alpha = np.expand_dims(alpha, axis=-1)

        blended_layer = cv2.addWeighted(image_cv, 1.0 - opacity, color_layer, opacity, 0)
        final_image = (1.0 - alpha) * image_cv + alpha * blended_layer

        return final_image.astype(np.uint8), True
    except Exception as e:
        return image_cv, False

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

def get_qty_by_keyword(row, keywords):
    for col in row.keys():
        for kw in keywords:
            if kw in str(col):
                return clean_qty_value(row[col])
    return 0.0

@app.get("/api/search")
async def search(query: str):
    try:
        inv = get_inventory()
        db = get_links_db()
        if inv.empty: return {"status": "error", "message": "قاعدة بيانات المعرض غير متوفرة."}

        results = inv[
            inv['الصنف'].astype(str).str.contains(query, na=False, case=False, regex=False) | 
            inv['الباركود'].astype(str).str.contains(query, na=False, regex=False)
        ].head(15)

        data = []
        for _, row in results.iterrows():
            item_name = str(row.get('الصنف', '')).strip()
            is_oil = any(kw in item_name.lower() for kw in ["زيت", "جرام", "تركيب", "كحول", "مثبت"])
            qty_luxor_lotus = get_qty_by_keyword(row, ['اللوتس'])
            qty_marrowa = get_qty_by_keyword(row, ['المروة'])
            qty_hurgada = get_qty_by_keyword(row, ['HURGADA', 'الغردقة'])
            qty_online = get_qty_by_keyword(row, ['اونلاين', 'online'])

            price_1 = clean_qty_value(row.get('سعر1 كارت', 0))
            price_2 = clean_qty_value(row.get('سعر2 كارت', price_1 * 0.9))
            price_3 = clean_qty_value(row.get('سعر3 كارت', price_1 * 0.85))
            price_4 = clean_qty_value(row.get('سعر4 كارت', price_1 * 0.8))

            is_fixed = any(kw in item_name for kw in ["ثابت", "محمي", "صافي"])

            link = "https://www.royalelchim.app"
            show_link_trigger = False

            if is_oil:
                luxor_lotus_final = int(qty_luxor_lotus)
                marrowa_final = int(qty_marrowa)
                hurgada_final = int(qty_hurgada)
            else:
                luxor_lotus_final = int(qty_luxor_lotus)
                marrowa_final = int(qty_marrowa)
                hurgada_final = int(qty_hurgada)
                link_match = db[db['Product_Name'].astype(str).str.contains(item_name, na=False, case=False, regex=False)] if not db.empty else pd.DataFrame()
                link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"
                show_link_trigger = True if qty_online > 0 else False

            data.append({
                "name": item_name,
                "price": price_1,
                "price_card_1": price_1,
                "price_card_2": price_2,
                "price_card_3": price_3,
                "price_card_4": price_4,
                "is_fixed_price": is_fixed,
                "barcode": sanitize_value(row.get('الباركود'), "---"),
                "link": sanitize_value(link, "https://www.royalelchim.app"),
                "is_oil": is_oil,
                "show_link": show_link_trigger,
                "luxor_lotus_qty": luxor_lotus_final,
                "marrowa_qty": marrowa_final,
                "hurgada_qty": hurgada_final,
                "online_qty": int(qty_online)
            })
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"خطأ داخلي في استدعاء المخزون: {str(e)}"}

@app.post("/api/invoice/calculate")
async def calculate_invoice(payload: InvoicePayload):
    try:
        initial_total = 0
        for item in payload.items:
            initial_total += item.price_card_1 * item.qty
            
        target_tier = 1
        tier_name = "قطاعي"

        # التحقق من الأكواد السرية لـ VIP وتحديد المستوى والخصومات
        vip_activated = False
        discount_multiplier = 1.0

        if payload.secret_code == "ROYAL10":
            tier_name = "كبار العملاء البرونزي (VIP 10%)"
            discount_multiplier = 0.90
            vip_activated = True
        elif payload.secret_code == "ROYAL20":
            tier_name = "كبار العملاء الفضي (VIP 20%)"
            discount_multiplier = 0.80
            vip_activated = True
        elif payload.secret_code == "ELCHIM50":
            tier_name = "الحساب الملكي الماسي (VIP 50%)"
            discount_multiplier = 0.50
            vip_activated = True
        else:
            if initial_total >= 30000:
                target_tier = 4
                tier_name = "جملة كبار العملاء الملكي (السعر الرابع)"
            elif initial_total >= 15000:
                target_tier = 3
                tier_name = "جملة خاصة"
            elif initial_total >= 5000:
                target_tier = 2
                tier_name = "جملة عادية"

        final_items = []
        final_invoice_total = 0

        for item in payload.items:
            if item.is_fixed_price:
                actual_price = item.price_card_1
                is_protected = True
            else:
                if vip_activated:
                    actual_price = item.price_card_1 * discount_multiplier
                else:
                    if target_tier == 1: actual_price = item.price_card_1
                    elif target_tier == 2: actual_price = item.price_card_2
                    elif target_tier == 3: actual_price = item.price_card_3
                    elif target_tier == 4: actual_price = item.price_card_4
                is_protected = False

            item_total = actual_price * item.qty
            final_invoice_total += item_total

            final_items.append({
                "barcode": item.barcode,
                "name": item.name,
                "qty": item.qty,
                "applied_price": actual_price,
                "is_protected": is_protected,
                "total": item_total
            })

        return {
            "status": "success",
            "initial_total": initial_total,
            "final_total": final_invoice_total,
            "applied_tier": target_tier,
            "tier_name": tier_name,
            "vip_activated": vip_activated,
            "items": final_items
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- تفعيل الذاكرة التراكمية، ومطابقة الكيماء، وقراءة زيوت المعرض الفورية المتاحة للتركيب وحصرها ---
@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    context_str = f"\n[الذاكرة التراكمية للعميل - آخر 5 سجلات في الجلسة]: {payload.history_context}" if payload.history_context else ""
    
    # استخراج الزيوت الحقيقية المتوفرة بالمخازن فعلياً لدمجها بوعي كامل
    real_oils = get_available_oils_list()
    if real_oils:
        oils_bullet_points = "\n".join([
            f"- {o['name']} (سعر الجرام الأساسي: {o['price_per_gram']} ج.م | الباركود: {o['barcode']} | اللوتس: {o['branches']['luxor_lotus']} جرام | المروة: {o['branches']['marrowa']} جرام | الغردقة: {o['branches']['hurghada']} جرام)"
            for o in real_oils
        ])
    else:
        oils_bullet_points = "- لا توجد زيوت مسجلة حالياً كـ 'زيوت تركيب بالجرام' في ملف قاعدة البيانات (يرجى مراجعة ملف last.xls)."

    # تفاصيل الحساب الكيميائي للمصنعية والتركيب الإجباري بنسبة 30% لرويال إلتشيم
    chemistry_system_info = (
        f"\n[قوانين الكيميائي الصارمة لعطور التركيب بنسبة 30%]:\n"
        f"سعر لتر الكحول النقي: {ALCOHOL_PRICE_PER_LITER} جنيه مصري (0.2 جنيه للملي).\n"
        f"سعر مثبت النقاء الفاخر: {FIXATIVE_PRICE_PER_ML} جنيه مصري لكل 1 مللي.\n"
        f"النسبة الذهبية المعتمدة للتركيب الفاخر: 1 مللي مثبت لكل 5 مللي زيت خام.\n"
        f"طريقة احتساب التكلفة لتركيب زجاجة:\n"
        f"إذا اخترنا مثلاً دمج 10 جرام من الزيوت المتاحة لدينا:\n"
        f"  1. كمية المثبت المطلوبة = 10 / 5 = 2 مللي مثبت (تكلفته = 2 * {FIXATIVE_PRICE_PER_ML} = 20 جنيه).\n"
        f"  2. بما أن العطر بتركيز 30%، فإن مجموع (الزيت + المثبت) يمثل 30% من العبوة الإجمالية. وبما أن حجم الزيت والمثبت معاً = 12 مللي، فإن الحجم الكلي الفاخر للزجاجة يبلغ 40 مللي.\n"
        f"  3. كمية الكحول المطلوبة لاستكمال العبوة = 40 - 12 = 28 مللي كحول (تكلفته = 28 * 0.2 = 5.6 جنيه).\n"
        f"  4. تكلفة مصنعية التركيب الثابتة (الكحول + المثبت) = 20 + 5.6 = 25.6 جنيه مصري.\n"
        f"  5. التكلفة الكلية للزجاجة = تكلفة مصنعية التركيب الثابتة (25.6 جنيه) + تكلفة الزيوت الفعلية المستخدمة (مجموع جرامات الزيوت مضروبة في أسعارها من القائمة بالأسفل).\n"
        f"\n[قائمة الزيوت المتوفرة فعلياً في مخازننا لتركيب العطور حالياً]:\n{oils_bullet_points}\n"
        f"\nقواعد صارمة لرويال مايند لمنع الارتجال العطري:\n"
        f"1. يمنع منعاً باتاً اقتراح أي زيت عطر وهمي أو نوتة عطرية من خيالك (مثل: برغموت كالابريا، خشب الصندل الأسترالي، ماغنوليا بيضاء) إلا إذا كانت مذكورة صراحةً باسمها في القائمة الحقيقية أعلاه!\n"
        f"2. العطور التي تصنعينها يجب أن تكون 'تركيبات حقيقية' بدمج نوتتين أو ثلاث من زيوتنا الحقيقية المسجلة المذكورة في القائمة السابقة، مع حساب التكلفة الكلية بدقة فائقة كصديق مقرب حنون وبأسلوب دافئ فلسفي.\n"
        f"3. اذكري للعميل الفروع المتوفر بها الزيوت المقترحة (اللوتس، المروة، أو الغردقة) بالجرامات الفعلية المتاحة، وانهي بـ 'نحن معك' برفق."
    )
    
    prompt = f"{BASE_PHILOSOPHY}{chemistry_system_info}{context_str}\nجلسة حوار الصداقة والتحليل الوجداني لطلب العميل: '{payload.client_message}'"
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    context_str = f"\n[الذاكرة التراكمية للعميل - آخر 5 سجلات في الجلسة]: {payload.history_context}" if payload.history_context else ""
    
    real_oils = get_available_oils_list()
    if real_oils:
        oils_bullet_points = "\n".join([
            f"- {o['name']} (سعر الجرام الأساسي: {o['price_per_gram']} ج.م | الباركود: {o['barcode']} | اللوتس: {o['branches']['luxor_lotus']} جرام | المروة: {o['branches']['marrowa']} جرام | الغردقة: {o['branches']['hurghada']} جرام)"
            for o in real_oils
        ])
    else:
        oils_bullet_points = "- لا توجد زيوت مسجلة حالياً كـ 'زيوت تركيب بالجرام' في ملف قاعدة البيانات (يرجى مراجعة ملف last.xls)."

    chemistry_system_info = (
        f"\n[منظومة كيميائي تركيب العطور بالجرام والمللي]:\n"
        f"سعر الكحول: {ALCOHOL_PRICE_PER_LITER} جنيه للتر (0.2 جنيه للملي).\n"
        f"سعر المثبت الملكي: {FIXATIVE_PRICE_PER_ML} جنيه لكل 1 مللي.\n"
        f"النسبة لتركيز 30%: 1 مللي مثبت لكل 5 مللي زيت عطري خام.\n"
        f"حساب السعر لـ 5 جرام زيت عطر خام:\n"
        f"  نحتاج 1 مللي مثبت (10 جنيه) + 14 مللي كحول (2.8 جنيه) + 5 جرام زيت عطر خام بسعر الوحدة الفعلي المأخوذ من القائمة بالأسفل.\n"
        f"\n[قائمة الزيوت المتوفرة فعلياً في مخازننا لتركيب العطور حالياً]:\n{oils_bullet_points}\n"
        f"\nقوانين التركيب الصارمة لرويال مايند:\n"
        f"1. يجب أن تكون تركيبات العطور المقترحة مشتقة بالكامل وبطريقة حصرية من الزيوت الفعلية المتاحة في القائمة أعلاه (بدون اختلاق أسماء زيوت غير متوفرة لدينا).\n"
        f"2. احسبي السعر الكيميائي الإجمالي الدقيق لجرامات الزيوت والمثبت والكحول ليرى العميل الشفافية، ووجهيه للفرع الذي تتوفر فيه الكمية الكافية بدقة حنونة."
    )
    
    prompt = f"{BASE_PHILOSOPHY}{chemistry_system_info}{context_str}\nطلب العميل المباشر: '{payload.text}'"
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    try:
        encoded = payload.user_selfie.split(",", 1)[1] if "," in payload.user_selfie else payload.user_selfie
        img_data = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_data, np.uint8)
        img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        rgb_color = hex_to_rgb(payload.hex_color)
        processed_img, face_found = apply_royal_makeup(img_cv, rgb_color, payload.makeup_type)
        
        if face_found:
            _, buffer = cv2.imencode('.jpg', processed_img)
            result_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        else:
            result_base64 = payload.user_selfie

        # ربط التخيل البصري برؤية المستقبل والأصالة ونبرة الصداقة الحميمة
        context_str = f"\n[الذاكرة التراكمية والحالة الوجدانية للعميل]: {payload.history_context}" if payload.history_context else ""
        contents = [
            Image.open(io.BytesIO(base64.b64decode(result_base64.split(",")[1]))), 
            f"{BASE_PHILOSOPHY}{context_str}\nصفي تناغم المكياج من نوع ({payload.makeup_type}) المطبق بجمال وسحر أخاذ على ملامح وجهها الفاتن. اذكري لها كيف يجمع بين تطور ملامحها في الحاضر ورؤيتها المضيئة للمستقبل. نحن معكِ."
        ]
        res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
        
        return {
            "status": "success",
            "result_image": result_base64,
            "simulation_result": res,
            "face_detected": face_found
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
