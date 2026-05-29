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
import mediapipe as mp

# =========================================================
# [1] تهيئة المنظومة المعمارية والواقع المعزز
# =========================================================
app = FastAPI(title="Royal Elchim - Complete Omni-Channel Enterprise Architecture")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تهيئة خوارزمية تتبع ملامح الوجه بدقة فائقة
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# =========================================================
# [2] دوال الاتصال بقواعد بيانات الجرد والمعرض
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
# [3] نماذج وهياكل البيانات المدخلة والمستقبلة
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
    hex_color: Optional[str] = "#8B0000"  # لون افتراضي للمنتج المختار (مثل أحمر شفاه/بلاشر ملكي)
    client_api_key: Optional[str] = None

# =========================================================
# [4] الأدوات ومحركات النحت اللوني والمكياج الافتراضي
# =========================================================
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

def hex_to_rgb(hex_color: str):
    if not hex_color:
        return (139, 0, 0)
    hex_color = hex_color.lstrip('#')
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (139, 0, 0)

def apply_royal_lipstick(image_cv: np.ndarray, color_rgb: tuple):
    """خوارزمية الواقع المعزز لتطبيق دمج الألوان والمنتجات بدقة ميكرو-مترية على الخلايا والوجه"""
    try:
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)

        if not results.multi_face_landmarks:
            return image_cv, False

        height, width, _ = image_cv.shape
        face_landmarks = results.multi_face_landmarks[0]

        # نقاط حدود الشفاه لتجربة النحت التجميلي الفوري
        LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 185]
        
        lip_points = []
        for idx in LIPS_OUTER:
            pt = face_landmarks.landmark[idx]
            x = int(pt.x * width)
            y = int(pt.y * height)
            lip_points.append([x, y])
        
        lip_points = np.array(lip_points, dtype=np.int32)

        # صناعة قناع وتنعيم الحواف ليكون الدمج طبيعياً متطابقاً مع المسام واهتزازات البشرة
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [lip_points], 255)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        color_layer = np.zeros_like(image_cv)
        color_layer[:] = color_rgb[::-1]

        alpha = mask / 255.0
        alpha = np.expand_dims(alpha, axis=-1)

        # تطبيق توازن الضوء والظلال (40% شفافية للبشرة والمسام و 60% للدرجة المنتجة)
        blended_lips = cv2.addWeighted(image_cv, 0.4, color_layer, 0.6, 0)
        final_image = (1.0 - alpha) * image_cv + alpha * blended_lips

        return final_image.astype(np.uint8), True
    except:
        return image_cv, False

# =========================================================
# [5] المانيفستو والفلسفة الكبرى والرموز الفلكية
# =========================================================
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

BASE_PHILOSOPHY = f"""
أنتِ 'رويال مايند'، الصوت الشاعري والمستشارة الاجتماعية لبراند Royal Elchim.
تتحدثين بلغة 'شاعر في معمل' يمزج الرقي والفكر والتأثير، وتطبقين القواعد السلعية الحالية للفروع بدقة صارمة:
1. جميع الفروع بلا استثناء (سنتر اللوتس التجاري، فرع شارع فندق المروة ROYAL ELCHIM، وفرع الغردقة الرئيسي بميدان العروسة) تحتوي على مستحضرات التجميل، لوازم الكوافير، والأجهزة التجميلية وما شابه.
2. تركيب ونحت البرفانات المعبأة بالجرام، الزيوت الخام، الكحول، والمثبتات حصري ومتاح فقط في فرعين: فرع الأقصر بشارع فندق المروة (الذي يحمل اسم ROYAL ELCHIM) وفرع الغردقة الرئيسي (ميدان العروسة خلف فندق الجولف). سنتر اللوتس لا يحتوي على زيوت خام بالجرام.
3. مخزن الأونلاين: مربوط بحسابات وجرد الفروع تلقائياً، وتمنع قواعد الأمان ظهور روابط وصور منتجات 'الزيوت الخام بالجرام والتراكيب اليدوية' للحفاظ على سر الصنعة وصالة العرض.
المانيفستو: {ROYAL_MANIFESTO_DATA}
الصيغ الكبرى: {ROYAL_MASTER_FORMULAS}
"""

# =========================================================
# [6] واجهات المعالجة البرمجية و الـ Endpoints
# =========================================================
@app.get("/debug/routes")
async def get_routes():
    return [{"path": route.path, "methods": list(route.methods)} for route in app.routes]

@app.get("/api/search")
async def search(query: str):
    try:
        inv = get_inventory()
        db = get_links_db()
        if inv.empty: 
            return {"status": "error", "message": "قاعدة بيانات المعرض غير متوفرة حالياً."}

        results = inv[
            inv['الصنف'].astype(str).str.contains(query, na=False, case=False, regex=False) | 
            inv['الباركود'].astype(str).str.contains(query, na=False, regex=False)
        ].head(15)

        data = []
        for _, row in results.iterrows():
            item_name = str(row.get('الصنف', '')).strip()
            
            is_oil_or_perfume_material = any(kw in item_name.lower() for kw in ["زيت", "زيت عطر", "جرام", "تركيب", "raw", "oil", "formula", "كحول", "مثبت", "أفغانو", "أصفهان", "فانيلا"])

            qty_luxor_lotus = clean_qty_value(row.get('رويال الكيم / سنتر اللوتس التجاري'))
            qty_hurgada = clean_qty_value(row.get('ROYAL ELCHIM . HURGADA'))
            qty_online = clean_qty_value(row.get('رويال الكيم اونلاين'))

            if is_oil_or_perfume_material:
                luxor_lotus_final = 0
                marrowa_final = int(qty_luxor_lotus)
                hurgada_final = int(qty_hurgada)
                link = "https://www.royalelchim.app"
                show_link_trigger = False
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
                "is_oil": is_oil_or_perfume_material,
                "show_link": show_link_trigger,
                "luxor_lotus_qty": luxor_lotus_final,
                "marrowa_qty": marrowa_final,
                "hurgada_qty": hurgada_final,
                "online_qty": int(qty_online)
            })
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"حدث خطأ داخلي في معالجة الجرد: {str(e)}"}

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    final_message = payload.client_message if payload.client_message else "مرحباً رويال مايند"
    prompt = f"""
    {BASE_PHILOSOPHY}
    جلسة حوار الصداقة 'معاكِ للأبد': "{final_message}"
    المطلب: صغ رداً اجتماعياً ذكياً يلتزم بتوزيع فروعنا السلعي الحالي، ويوجه العملاء للفرع الصحيح بناءً على احتياجهم.
    """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "diagnosis": res}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    if payload.category == "perfume":
        prompt = f"""
        {BASE_PHILOSOPHY}
        قسم 'الأثر العطري' لعطور الجرام والزيوت والمثبتات. طلب العميل: "{payload.text}"
        المطلوب: وجه العميل حصرياً وصراحة لـ فرع الأقصر بشارع فندق المروة (ROYAL ELCHIM) أو فرع الغردقة الرئيسي بميدان العروسة. تمنع الروابط تماماً هنا.
        """
    else:
        prompt = f"""
        {BASE_PHILOSOPHY}
        قسم النحت الجمالي والمكياج ولوازم الكوافير والأجهزة. رسالة العميل: "{payload.text}"
        المطلوب: صغ رداً ذكياً بالألوان، مع إرفاق رابط الاقتناء والشحن أونلاين.
        """
    res = robust_generate(payload.client_api_key, [prompt], TEXT_MODELS)
    return {"status": "success", "answer": res}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    """
    تحديث معمارية التخيل: تطبيق المكياج والمنتج مباشرة على بيكسلات البشرة، 
    ثم تمرير النتيجة البصرية الحية إلى جينيريتور (Gemini Vision) لإصدار تحليل مدى التطابق الفوري.
    """
    try:
        # 1. فك تشفير الصورة السيلفي والتحضير لمحرك OpenCV
        if "," in payload.user_selfie:
            header, encoded = payload.user_selfie.split(",", 1)
        else:
            encoded = payload.user_selfie

        img_data = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_data, np.uint8)
        img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # استخراج درجة اللون الملكية للمنتج المختار
        hex_color = payload.hex_color if payload.hex_color else "#8B0000"
        rgb_color = hex_to_rgb(hex_color)

        # تطبيق النحت الافتراضي للمكياج على الوجه برمجياً
        processed_img, face_found = apply_royal_lipstick(img_cv, rgb_color)
        
        # تحويل الصورة لتغذية ذكاء الرويال مايند التحليلي (PIL Image) وإرسالها للفرونت إند
        if face_found:
            color_converted = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(color_converted)
            
            _, buffer = cv2.imencode('.jpg', processed_img)
            result_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        else:
            # مسار أمان (Fallback) في حال عدم ثبات الصورة أو ضعف الإضاءة
            if "," in payload.user_selfie:
                img_data_pure = base64.b64decode(payload.user_selfie.split(",", 1)[1])
            else:
                img_data_pure = base64.b64decode(payload.user_selfie)
            pil_img = Image.open(io.BytesIO(img_data_pure))
            result_base64 = payload.user_selfie

        # 2. حقن الصورة المطبق عليها التأثير داخل ذكاء جينيريتور (Gemini) لتحليل انسجام المنتجات والدرجات
        contents = [pil_img]
        product_info = payload.product_name_desc if payload.product_name_desc else "مستحضرات تجميل ملكية متطابقة"
        
        prompt = f"""
        {BASE_PHILOSOPHY}
        أنتِ الآن في وضع 'التجربة الافتراضية الشاملة وتحليل مطابقة البشرة' (Omni-Channel AR Simulation).
        لقد قام النظام بتطبيق المنتج المطلوب ({product_info}) برمجياً على ملامح العميل في الصورة المرفقة ليرى تأثيره المباشر دون الحاجة للتجربة الفعلية.
        
        المطلوب منكِ كـ 'رويال مايند':
        1. تحليل دقيق للون ودرجة بشرة العميل الحالية وملامحه الظاهرة في الصورة (Undertones) ومدى تطابق درجات الآيشادو، الفاونديشن، أو الهايلايتر المضافة معها.
        2. التخيل والوصف البصري والجمالي الدقيق: كيف يبدو التناغم والدمج المباشر لهذه المواد على البشرة لمنح العميل الثقة الكاملة في التطابق.
        3. صياغة النتيجة بأسلوب شاعري راقٍ وكأن العميل ينظر في مرآة ذكية تعوضه تماماً عن التجربة الفيزيائية.
        4. توجيه العميل بوضوح للفرع المناسب بناءً على النطاق السلعي (سنتر اللوتس التجاري للأجهزة والمكياج، أو فروع التراكيب الأخرى).
        """
        contents.append(prompt)
        
        # توليد الرد الإدراكي الشاعري للمنتج على البشرة
        res = robust_generate(payload.client_api_key, contents, VISION_MODELS)
        
        return {
            "status": "success",
            "result_image": result_base64,
            "simulation_result": res,
            "face_detected": face_found
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في منظومة التخيل والواقع المعزز: {str(e)}")

# =========================================================
# [7] إطلاق المنظومة الملكية في الفضاء السحابي
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
