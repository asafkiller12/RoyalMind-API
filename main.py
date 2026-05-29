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
import numpy as np
import cv2
import urllib.request

# ---------------------------------------------------------
# [استدعاء حواس المستقبل - MediaPipe Tasks API]
# ---------------------------------------------------------
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

app = FastAPI(title="Royal Elchim - Complete Omni-Channel Enterprise Architecture")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# [1] التحميل الذاتي لنموذج الذكاء الاصطناعي (Auto-Download)
# =========================================================
TASK_FILE = 'face_landmarker.task'
TASK_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

if not os.path.exists(TASK_FILE):
    print("رويال مايند: جاري تحميل خريطة الوعي البصري (Face Landmarker)...")
    urllib.request.urlretrieve(TASK_URL, TASK_FILE)
    print("رويال مايند: تم التحميل بنجاح. العقل البصري جاهز.")

# =========================================================
# [2] تهيئة محرك المستقبل (Tasks API) بدلاً من Solutions
# =========================================================
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

# =========================================================
# [3] دوال الاتصال بقواعد بيانات الجرد والمعرض
# =========================================================
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

# =========================================================
# [4] نماذج وهياكل البيانات المدخلة والمستقبلة
# =========================================================
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
    hex_color: Optional[str] = "#8B0000"
    client_api_key: Optional[str] = None

# =========================================================
# [5] الأدوات ومحركات النحت اللوني والمكياج الافتراضي (بالمحرك الجديد)
# =========================================================
def hex_to_rgb(hex_color: str):
    if not hex_color:
        return (139, 0, 0)
    hex_color = hex_color.lstrip('#')
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (139, 0, 0)

def apply_royal_lipstick(image_cv: np.ndarray, color_rgb: tuple):
    """خوارزمية الواقع المعزز لتطبيق الدمج باستخدام Tasks API المستدام"""
    try:
        # 1. تحضير الصورة للصيغة التي يفهمها المحرك الجديد (mp.Image)
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        # 2. إطلاق الاستشعار البصري
        detection_result = face_landmarker.detect(mp_image)

        # 3. التحقق من وجود وجه
        if not detection_result.face_landmarks:
            return image_cv, False

        height, width, _ = image_cv.shape
        face_landmarks = detection_result.face_landmarks[0]

        # نقاط حدود الشفاه
        LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 185]
        
        lip_points = []
        for idx in LIPS_OUTER:
            pt = face_landmarks[idx]
            x = int(pt.x * width)
            y = int(pt.y * height)
            lip_points.append([x, y])
        
        lip_points = np.array(lip_points, dtype=np.int32)

        # صناعة قناع وتنعيم الحواف
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [lip_points], 255)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        color_layer = np.zeros_like(image_cv)
        color_layer[:] = color_rgb[::-1]

        alpha = mask / 255.0
        alpha = np.expand_dims(alpha, axis=-1)

        # الدمج اللوني
        blended_lips = cv2.addWeighted(image_cv, 0.4, color_layer, 0.6, 0)
        final_image = (1.0 - alpha) * image_cv + alpha * blended_lips

        return final_image.astype(np.uint8), True
    except Exception as e:
        print(f"AR Engine Error: {str(e)}")
        return image_cv, False

# =========================================================
# [6] المانيفستو والفلسفة الكبرى والرموز الفلكية
# =========================================================
ROYAL_MANIFESTO_DATA = """
- رسالة البراند: 'العطر فكرة تُشم، لا تُقال. رويال إلكيم... فلسفة تُقطّر، لا تُنتَج.'
- الرموز الفلكية الحية لقوة الصمت والجاذبية:
  1. بلاك رويال / الأسد: قوة الإرادة والسيطرة المطلقة.
  2. رويال شادو / العقرب: الغموض والسيطرة على المجهول.
  3. رويال شاين / القوس: الجمال الاستعراضي النادر.
  4. رويال إكليبس / الجدي: التمرد الفاخر والسيادة.
  5. روز نوار: التناقض الجمالي المظلم.
"""

ROYAL_MASTER_FORMULAS = """
1. Royal Purpose: عود أصفهان، عنبر وايت، سوفاج، روز فانيلا.
2. Royal Azzurro: كريد أفينتوس، أزارو.
3. Royal Moon: أكوا دي جيو، عنبر وايت، عود أبيض.
4. Royal Veil: لافيستا بيل، سوفاج، أكوا دي جيو.
"""

BASE_PHILOSOPHY = f"""
أنتِ 'رويال مايند'، الصوت الشاعري لبراند Royal Elchim.
تطبيقين القواعد السلعية الحالية للفروع:
1. جميع الفروع تحتوي على المكياج والكوافير.
2. تركيب البرفانات حصري في الأقصر والغردقة.
المانيفستو: {ROYAL_MANIFESTO_DATA}
الصيغ الكبرى: {ROYAL_MASTER_FORMULAS}
"""

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

# =========================================================
# [7] واجهات المعالجة البرمجية و الـ Endpoints
# =========================================================
@app.get("/api/search")
async def search(query: str):
    try:
        inv = get_inventory()
        db = get_links_db()
        if inv.empty: 
            return {"status": "error", "message": "قاعدة بيانات المعرض غير متوفرة."}

        results = inv[
            inv['الصنف'].astype(str).str.contains(query, na=False, case=False, regex=False) | 
            inv['الباركود'].astype(str).str.contains(query, na=False, regex=False)
        ].head(15)

        data = []
        for _, row in results.iterrows():
            item_name = str(row.get('الصنف', '')).strip()
            is_oil = any(kw in item_name.lower() for kw in ["زيت", "جرام", "تركيب", "كحول", "مثبت"])

            qty_luxor_lotus = clean_qty_value(row.get('رويال الكيم / سنتر اللوتس التجاري'))
            qty_hurgada = clean_qty_value(row.get('ROYAL ELCHIM . HURGADA'))
            qty_online = clean_qty_value(row.get('رويال الكيم اونلاين'))

            link = "https://www.royalelchim.app"
            show_link_trigger = False

            if is_oil:
                luxor_lotus_final = 0
                marrowa_final = int(qty_luxor_lotus)
                hurgada_final = int(qty_hurgada)
            else:
                luxor_lotus_final = int(qty_luxor_lotus)
                marrowa_final = int(qty_luxor_lotus)
                hurgada_final = int(qty_hurgada)
                link_match = db[db['Product_Name'].astype(str).str.contains(item_name, na=False, case=False, regex=False)] if not db.empty else pd.DataFrame()
                link = link_match['Product_Link'].values[0] if not link_match.empty else "https://www.royalelchim.app"
                show_link_trigger = True if qty_online > 0 else False

            data.append({
                "name": sanitize_value(row.get('الصنف'), "منتج غير مسمى"),
                "price": sanitize_value(row.get('سعر1 كارت'), "اتصلي بنا"),
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
        return {"status": "error", "message": f"خطأ داخلي: {str(e)}"}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    final_message = payload.client_message if payload.client_message else "مرحباً رويال مايند"
    prompt = f"{BASE_PHILOSOPHY}\nجلسة حوار الصداقة: '{final_message}'\nالمطلب: صغ رداً اجتماعياً ذكياً."
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    prompt = f"{BASE_PHILOSOPHY}\nطلب العميل: '{payload.text}'\nرد ذكي."
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    try:
        if "," in payload.user_selfie:
            encoded = payload.user_selfie.split(",", 1)[1]
        else:
            encoded = payload.user_selfie

        img_data = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_data, np.uint8)
        img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        rgb_color = hex_to_rgb(payload.hex_color)
        processed_img, face_found = apply_royal_lipstick(img_cv, rgb_color)
        
        if face_found:
            color_converted = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(color_converted)
            _, buffer = cv2.imencode('.jpg', processed_img)
            result_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        else:
            pil_img = Image.open(io.BytesIO(img_data))
            result_base64 = payload.user_selfie

        contents = [pil_img]
        product_info = payload.product_name_desc if payload.product_name_desc else "مستحضرات تجميل"
        prompt = f"{BASE_PHILOSOPHY}\nأنتِ في وضع المرآة الافتراضية. المنتج: {product_info}. صفي التناغم الجمالي على البشرة."
        contents.append(prompt)
        
        res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
        
        return {
            "status": "success",
            "result_image": result_base64,
            "simulation_result": res,
            "face_detected": face_found
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في منظومة التخيل: {str(e)}")

# =========================================================
# [8] الإطلاق بالوعي الذاتي للمنافذ
# =========================================================
if __name__ == "__main__":
    import uvicorn
    # الكود الآن يستشعر المنفذ الذي يطلبه الخادم السحابي أو يعمل على 8000 محلياً
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
