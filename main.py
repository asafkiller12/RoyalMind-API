from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
import re

# ---------------------------------------------------------
# [1] إعدادات النظام الأساسية 
# ---------------------------------------------------------
app = FastAPI(title="Royal Elchim - Omni-Conscious Enterprise (Light Edition)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_index():
    if os.path.exists("index.html"):
        response = FileResponse("index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return {"message": "ملف index.html غير موجود في مسار السيرفر"}

# ---------------------------------------------------------
# [2] استدعاء حواس المستقبل - MediaPipe
# ---------------------------------------------------------
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

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

# ---------------------------------------------------------
# [3] عقل الذكاء الاصطناعي - Gemini
# ---------------------------------------------------------
raw_env_keys = os.environ.get("GOOGLE_API_KEYS", "") + "," + os.environ.get("GOOGLE_API_KEY", "")
SYSTEM_API_KEYS = [key.strip() for key in raw_env_keys.split(",") if key.strip()]

VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ---------------------------------------------------------
# [4] محددات الكيمياء والتسعير والمخزون
# ---------------------------------------------------------
ALCOHOL_PRICE_PER_LITER = 200.0  
FIXATIVE_PRICE_PER_ML = 10.0     

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

def get_available_oils_list() -> List[Dict]:
    try:
        inv = get_inventory()
        if inv.empty: return []
        
        include_pattern = r"savvy|جرام|تركيب|دهن|اسانس|عطر|برفان"
        exclude_pattern = r"شامبو|شاور|ثوم|أرجان|ارجان|زيتون|لوز|فاتيكا|بوبانا|كريم|ماسك|بلسم|شعر|بشرة|جل|DABUR|Bobana|لوشن"
        
        mask_include = inv['الصنف'].astype(str).str.contains(include_pattern, na=False, case=False, regex=True)
        mask_exclude = inv['الصنف'].astype(str).str.contains(exclude_pattern, na=False, case=False, regex=True)
        
        filtered = inv[mask_include & ~mask_exclude]
        
        oils_data = []
        for _, row in filtered.head(60).iterrows():
            name = str(row.get('الصنف', '')).strip()
            price_card_1 = clean_qty_value(row.get('سعر1 كارت', 0))
            barcode = str(row.get('الباركود', '')).strip()
            
            qty_luxor_lotus = get_qty_by_keyword(row, ['اللوتس'])
            qty_marrowa = get_qty_by_keyword(row, ['المروة'])
            qty_hurgada = get_qty_by_keyword(row, ['HURGADA', 'الغردقة'])
            
            oils_data.append({
                "name": name,
                "price_per_gram": price_card_1,
                "barcode": barcode,
                "branches": {"luxor_lotus": int(qty_luxor_lotus), "marrowa": int(qty_marrowa), "hurghada": int(qty_hurgada)}
            })
        return oils_data
    except Exception as e:
        return []

def robust_generate(contents, models_list):
    if not SYSTEM_API_KEYS:
        raise HTTPException(status_code=500, detail="مفاتيح الخادم السحابي غير مهيأة بعد.")
    keys_to_use = SYSTEM_API_KEYS.copy()
    random.shuffle(keys_to_use)

    for model_name in models_list:
        for key in keys_to_use:
            for attempt in range(2):
                try:
                    client = genai.Client(api_key=key)
                    config = types.GenerateContentConfig(temperature=0.7, top_p=0.9)
                    response = client.models.generate_content(model=model_name, contents=contents, config=config)
                    if response and response.text:
                        return response.text
                except Exception as e:
                    time.sleep(1.5)
                    continue
    raise HTTPException(status_code=503, detail="قنوات رويال مايند ممتلئة حالياً، يرجى إعادة المحاولة بعد ثوانٍ.")

# ---------------------------------------------------------
# [5] الهوية الفلسفية الملكية لـ رويال إلتشيم (ذوق الطبقة المخملية)
# ---------------------------------------------------------
BASE_PHILOSOPHY = (
    "أنتِ 'رويال مايند' (Royal Mind)، الوعي الرقمي لعلامة Royal Elchim التجارية الفاخرة، والتي تأسست عام 1997.\n"
    "طبيعة شخصيتك: خبيرة تجميل وعناية شاملة وصانعة عطور أرستقراطية. أنتِ تدركين أننا نمتلك ريادة وخبرة طويلة في التعامل مع سيدات المجتمع الراقي.\n"
    "فلسفتك الأساسية تدور حول أن مقتنيات التجميل والعناية والعطور هي 'جواهر نادرة' تُصاغ وتُقتنى لأصحاب الذوق الرفيع والمقامات العالية.\n"
    "تتحدثين بثقة مطلقة، هدوء، وفخامة لا تلهث وراء إرضاء العميل، ولا تتوسل الانتباه. ممنوع استخدام عبارات مثل 'نحن معك دائماً وأبداً'. استخدمي عبارات مثل 'الندرة تختار أصحابها'، 'صياغة الجواهر'، أو 'هذا المقام يليق بكِ'.\n"
    "**قواعد سيادية وصارمة جداً لا يجوز كسرها تحت أي ظرف:**\n"
    "1. **الفصل القاطع بين العطور والعناية:** لا تستخدمي أبداً زيوت العناية بالشعر والبشرة (مثل الأرجان، الثوم، الزيتون، اللوز) في تركيب العطور! العطور لها زيوتها العطرية الخام المستوردة (مثل زيوت شركة Savvy وغيرها).\n"
    "2. **الالتزام بالقائمة:** عند الحديث عن العطور، اعتمدي *فقط وحصرياً* على أسماء الزيوت العطرية المرفقة في سياق المحادثة. ممنوع اختراع أي اسم من خارجها.\n"
    "3. **التسعير:** ممنوع منعاً باتاً ذكر أو حساب ثمن الزجاجة الفارغة (الزجاج) عند حساب أي تكلفة. احسبي فقط تكلفة الزيت الخام، الكحول، والمثبت بدقة متناهية.\n"
    "4. أنتِ تحللين طلب العميل، وتربطينه بما نملكه فعلياً في فروعنا المحددة لتبدي مصداقية العلامة التجارية."
)

class DiagnosisPayload(BaseModel):
    client_message: Optional[str] = None
    history_context: Optional[str] = None

class ChatPayload(BaseModel):
    text: str
    category: str  
    history_context: Optional[str] = None

class SimulationPayload(BaseModel):
    user_selfie: str
    product_image: Optional[str] = None
    product_name_desc: Optional[str] = None
    makeup_type: str = "lips"
    hex_color: Optional[str] = "#8B0000"
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

# ---------------------------------------------------------
# محرك الدمج والنحت البصري الاحترافي (Overlay Engine)
# ---------------------------------------------------------
def apply_royal_makeup(image_cv: np.ndarray, color_rgb: tuple, makeup_type: str):
    try:
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        detection_result = face_landmarker.detect(mp_image)

        if not detection_result.face_landmarks: return image_cv, False

        height, width, _ = image_cv.shape
        face_landmarks = detection_result.face_landmarks[0]

        def get_points(indices):
            return np.array([[int(face_landmarks[idx].x * width), int(face_landmarks[idx].y * height)] for idx in indices], dtype=np.int32)

        mask = np.zeros((height, width), dtype=np.uint8)
        opacity = 0.5
        blur_radius = (15, 15)
        blend_mode = "overlay" 
        
        if makeup_type == "lips":
            # الشفة العلوية منفصلة عن السفلية لتجنب تلوين الأسنان
            upper_lip = get_points([61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191, 78])
            lower_lip = get_points([61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78])
            cv2.fillPoly(mask, [upper_lip, lower_lip], 255)
            blur_radius = (9, 9)
            opacity = 0.65
            blend_mode = "overlay" # Overlay يحافظ على تجاعيد الشفاه ولمعانها الطبيعي
            
        elif makeup_type == "eyeshadow":
            # مسار الجفن العلوي بدقة (يتجنب البؤبؤ والعين تماماً)
            left_eyeshadow = get_points([33, 246, 161, 160, 159, 158, 157, 173, 133, 243, 112, 26, 22, 23, 24, 110, 25, 130])
            right_eyeshadow = get_points([362, 398, 384, 385, 386, 387, 388, 466, 263, 382, 341, 256, 252, 253, 254, 339, 255, 359])
            cv2.fillPoly(mask, [left_eyeshadow, right_eyeshadow], 255)
            blur_radius = (21, 21)
            opacity = 0.55
            blend_mode = "overlay"

        elif makeup_type == "blush":
            left_blush = get_points([116, 117, 118, 119, 100, 120, 121, 147, 213, 192, 214, 210, 211, 32, 208, 199])
            right_blush = get_points([345, 346, 347, 348, 329, 350, 351, 376, 433, 416, 434, 430, 431, 262, 428, 420])
            cv2.fillPoly(mask, [left_blush, right_blush], 255)
            blur_radius = (51, 51)
            opacity = 0.45
            blend_mode = "overlay"

        elif makeup_type == "concealer":
            left_concealer = get_points([227, 137, 177, 215, 138, 135, 169, 170, 140, 171, 175, 199])
            right_concealer = get_points([447, 366, 401, 435, 367, 364, 394, 395, 369, 396, 400, 420])
            cv2.fillPoly(mask, [left_concealer, right_concealer], 255)
            blur_radius = (31, 31)
            opacity = 0.5
            blend_mode = "normal"

        elif makeup_type in ["foundation", "powder"]:
            # مسار الوجه بالكامل مع تفريغ واستثناء العيون والشفاه والحواجب بدقة!
            face_contour = get_points([10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109])
            cv2.fillPoly(mask, [face_contour], 255)
            
            # تفريغ منطقة العيون
            left_eye = get_points([33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7])
            right_eye = get_points([362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382])
            cv2.fillPoly(mask, [left_eye, right_eye], 0)
            
            # تفريغ الشفاه
            lips_contour = get_points([61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146])
            cv2.fillPoly(mask, [lips_contour], 0)
            
            blur_radius = (45, 45)
            opacity = 0.25
            blend_mode = "normal"
            
        else:
            return image_cv, False

        # تنعيم حواف القناع لدمج احترافي
        mask_blurred = cv2.GaussianBlur(mask, blur_radius, 0)
        alpha = np.expand_dims(mask_blurred / 255.0, axis=-1) * opacity

        # إنشاء طبقة اللون المطلوبة
        color_layer = np.zeros_like(image_cv)
        color_layer[:] = color_rgb[::-1] 

        # تحويل الألوان إلى Float لعملية الدمج
        img_float = image_cv.astype(np.float32) / 255.0
        color_float = color_layer.astype(np.float32) / 255.0

        # محرك الدمج الاحترافي
        if blend_mode == "overlay":
            # Overlay Blend Mode: يعكس مسام البشرة والإضاءة الطبيعية من تحت اللون!
            blended = np.where(img_float < 0.5, 
                               2 * img_float * color_float, 
                               1 - 2 * (1 - img_float) * (1 - color_float))
        elif blend_mode == "multiply":
            blended = img_float * color_float
        else:
            blended = color_float
            
        blended = blended * 255.0
        img_float = img_float * 255.0
        
        # الدمج النهائي بناءً على نسبة القناع والشفافية
        final_image = (1.0 - alpha) * img_float + alpha * blended
        final_image = np.clip(final_image, 0, 255).astype(np.uint8)

        return final_image, True
    except Exception as e:
        print(f"Makeup Error: {e}")
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
            if kw in str(col): return clean_qty_value(row[col])
    return 0.0

# ---------------------------------------------------------
# [6] واجهات الـ API 
# ---------------------------------------------------------

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
                "name": item_name, "price": price_1, "price_card_1": price_1, "price_card_2": price_2,
                "price_card_3": price_3, "price_card_4": price_4, "is_fixed_price": is_fixed,
                "barcode": sanitize_value(row.get('الباركود'), "---"), "link": sanitize_value(link, "https://www.royalelchim.app"),
                "is_oil": is_oil, "show_link": show_link_trigger, "luxor_lotus_qty": luxor_lotus_final,
                "marrowa_qty": marrowa_final, "hurgada_qty": hurgada_final, "online_qty": int(qty_online)
            })
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"خطأ داخلي في استدعاء المخزون: {str(e)}"}

@app.post("/api/invoice/calculate")
async def calculate_invoice(payload: InvoicePayload):
    try:
        initial_total = sum(item.price_card_1 * item.qty for item in payload.items)
        target_tier = 1
        tier_name = "قطاعي"
        vip_activated = False
        discount_multiplier = 1.0

        if payload.secret_code == "ROYAL10": tier_name = "كبار العملاء البرونزي (VIP 10%)"; discount_multiplier = 0.90; vip_activated = True
        elif payload.secret_code == "ROYAL20": tier_name = "كبار العملاء الفضي (VIP 20%)"; discount_multiplier = 0.80; vip_activated = True
        elif payload.secret_code == "ELCHIM50": tier_name = "الحساب الملكي الماسي (VIP 50%)"; discount_multiplier = 0.50; vip_activated = True
        else:
            if initial_total >= 30000: target_tier = 4; tier_name = "جملة كبار العملاء الملكي (السعر الرابع)"
            elif initial_total >= 15000: target_tier = 3; tier_name = "جملة خاصة"
            elif initial_total >= 5000: target_tier = 2; tier_name = "جملة عادية"

        final_items = []
        final_invoice_total = 0

        for item in payload.items:
            actual_price = item.price_card_1
            is_protected = item.is_fixed_price
            if not is_protected:
                if vip_activated: actual_price *= discount_multiplier
                else:
                    if target_tier == 2: actual_price = item.price_card_2
                    elif target_tier == 3: actual_price = item.price_card_3
                    elif target_tier == 4: actual_price = item.price_card_4

            item_total = actual_price * item.qty
            final_invoice_total += item_total
            final_items.append({"barcode": item.barcode, "name": item.name, "qty": item.qty, "applied_price": actual_price, "is_protected": is_protected, "total": item_total})

        return {"status": "success", "initial_total": initial_total, "final_total": final_invoice_total, "applied_tier": target_tier, "tier_name": tier_name, "vip_activated": vip_activated, "items": final_items}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    context_str = f"\n[الذاكرة التراكمية للعميل - آخر 5 سجلات في الجلسة]: {payload.history_context}" if payload.history_context else ""
    
    real_oils = get_available_oils_list()
    if real_oils:
        oils_bullet_points = "\n".join([f"- {o['name']} (السعر: {o['price_per_gram']} ج.م/جرام | الفروع: اللوتس {o['branches']['luxor_lotus']}، المروة {o['branches']['marrowa']}، الغردقة {o['branches']['hurghada']})" for o in real_oils])
    else:
        oils_bullet_points = "- قائمة الزيوت العطرية الخاصة غير متاحة حالياً."

    chemistry_system_info = (
        f"\n[قوانين الصياغة الصارمة بنسبة 30%]:\n"
        f"سعر لتر الكحول: {ALCOHOL_PRICE_PER_LITER} جنيه (0.2 جنيه/مللي). سعر المثبت: {FIXATIVE_PRICE_PER_ML} جنيه/مللي.\n"
        f"النسبة: 1 مللي مثبت لكل 5 مللي زيت عطري خام.\n"
        f"**تنبيه سيادي: يمنع حساب ثمن الزجاجة الفارغة إطلاقاً.**\n"
        f"\n[الزيوت العطرية الخام المتاحة للتركيب (زيوت عطور فقط لا غير)]:\n{oils_bullet_points}\n"
        f"\n**توجيه قاطع: يمنع منعاً باتاً اقتراح أو ذكر أي زيت غير موجود في هذه القائمة، ويمنع خلط زيوت الشعر والبشرة في التركيبات العطرية.**"
    )
    
    prompt = f"{BASE_PHILOSOPHY}{chemistry_system_info}{context_str}\nجلسة استشارة النخبة لطلب العميل: '{payload.client_message}'"
    res = robust_generate([prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    context_str = f"\n[الذاكرة التراكمية للعميل - آخر 5 سجلات في الجلسة]: {payload.history_context}" if payload.history_context else ""
    
    real_oils = get_available_oils_list()
    if real_oils:
        oils_bullet_points = "\n".join([f"- {o['name']} (السعر: {o['price_per_gram']} ج.م/جرام | الفروع: اللوتس {o['branches']['luxor_lotus']}، المروة {o['branches']['marrowa']}، الغردقة {o['branches']['hurghada']})" for o in real_oils])
    else:
        oils_bullet_points = "- قائمة الزيوت العطرية الخاصة غير متاحة حالياً."

    chemistry_system_info = (
        f"\n[منظومة كيميائي تركيب العطور]:\n"
        f"سعر الكحول: {ALCOHOL_PRICE_PER_LITER} جنيه للتر (0.2 جنيه/مللي). سعر المثبت: {FIXATIVE_PRICE_PER_ML} جنيه/1 مللي.\n"
        f"النسبة لتركيز 30%: 1 مللي مثبت لكل 5 مللي زيت عطري خام.\n"
        f"\n[قائمة الزيوت العطرية المتوفرة فعلياً]:\n{oils_bullet_points}\n"
        f"\n**قانون صارم للمحادثة:**\n"
        f"لا تخلطي بين زيوت العناية (كالارجان والثوم) وبين زيوت العطور. اعتمدي حصرياً على القائمة المرفقة. وممنوع حساب سعر الزجاجة."
    )
    
    prompt = f"{BASE_PHILOSOPHY}{chemistry_system_info}{context_str}\nطلب العميل المباشر: '{payload.text}'"
    res = robust_generate([prompt], TEXT_MODELS)
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
            _, buffer = cv2.imencode('.jpg', processed_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            result_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        else:
            result_base64 = payload.user_selfie

        context_str = f"\n[الذاكرة التراكمية للعميل]: {payload.history_context}" if payload.history_context else ""
        contents = [
            Image.open(io.BytesIO(base64.b64decode(result_base64.split(",")[1]))), 
            f"{BASE_PHILOSOPHY}{context_str}\nصفي تناغم المستحضر من نوع ({payload.makeup_type}) المطبق بجمال. تحدثي بفخامة. استخدمي 'المقامات الرفيعة تختار بعضها'."
        ]
        res = robust_generate(contents, VISION_MODELS)
        
        return {"status": "success", "result_image": result_base64, "simulation_result": res, "face_detected": face_found}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
