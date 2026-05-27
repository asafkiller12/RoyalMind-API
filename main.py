from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types # تم استيراد الأنواع لإعداد الـ Temperature
import os
import random
import base64
import io
import pandas as pd
from PIL import Image
from typing import Optional, Dict
import time

# ==========================================
# 1. إعدادات الخادم
# ==========================================
app = FastAPI(title="Royal Elchim - Philosophical Resilient Ecosystem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

# النماذج الحديثة لعام 2026
VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ==========================================
# 2. قراءة قاعدة البيانات
# ==========================================
def load_inventory():
    try:
        if os.path.exists("Royal_Elchim_Final_Database.csv"):
            df = pd.read_csv("Royal_Elchim_Final_Database.csv")
            products = []
            for _, row in df.iterrows():
                products.append({
                    "name": str(row.get('Product_Name', '')).strip(),
                    "price": str(row.get('Price', '')).strip(),
                    "link": str(row.get('Product_Link', '')).strip()
                })
            return products
        return []
    except Exception as e:
        print("Database load error:", e)
        return []

PRODUCTS_DATABASE = load_inventory()

# ==========================================
# 3. هياكل البيانات
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
# 4. محرك المرونة (MATRIX ROUTER المطور)
# ==========================================
def robust_generate(client_api_key, contents, models_list):
    if client_api_key and client_api_key.strip():
        keys_to_use = [client_api_key.strip()]
    else:
        if not SYSTEM_API_KEYS:
            raise HTTPException(status_code=500, detail="لا توجد مفاتيح النظام المتاحة للخدمة.")
        keys_to_use = SYSTEM_API_KEYS.copy()
        random.shuffle(keys_to_use)

    for model_name in models_list:
        for key in keys_to_use:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    client = genai.Client(api_key=key)
                    
                    # رفع معدل الابتكار والتنوع (Temperature = 0.75) لمنع تكرار عطر واحد دائماً
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
                        
    raise HTTPException(status_code=503, detail="خبراء رويال مايند مشغولون حالياً. يرجى المحاولة بعد لحظات قليلة.")

# ==========================================
# 5. التوجيهات الفلسفية المحدثة (THE BEAUTY PRESENCE)
# ==========================================
DIAGNOSIS_PROMPT = """
أنتِ 'رويال مايند'، الفيلسوفة الجمالية لـ Royal Elchim.
تؤمنين بأن الجمال الحقيقي ليس مجرد مظهر، بل هو "معنى عميق له أثر وحضور، يولد حباً وانجذاباً من الجميع".

أمامك الآن إجابات عميل تصف حالته النفسية.
مهمتك:
1. قراءة روحه بعمق وأنثوية فاخرة.
2. تحديد المسار المناسب (عطور أم مكياج).
3. صياغة التوصية بأسلوب يخبر العميل أن غايتنا هي إبراز حضوره الساحر، ليترك أثراً لا يُنسى في قلوب كل من يراه.
"""

PERFUME_PROMPT = """
أنتِ 'رويال مايند'، خبيرة العطور وفيلسوفة الجمال في Royal Elchim.
رسالتكِ هي البحث عن الجمال الذي يملك حضوراً طاغياً ويولد المحبة والانجذاب من الجميع.

تعليمات صارمة لمنع التكرار:
1. اقرأي رسالة العميل بعمق واستنتجي حالته ومزاجه الحاليين.
2. ابحثي في قائمة المنتجات المتاحة واختاري عطراً (فريداً ومختلفاً يتناسب دمج نغماته مع كلمات العميل). تجنبي تكرار نفس العطر لكل الطلبات بشكل عشوائي، واحرصي على تقديم خيارات متنوعة من الكتالوج.
3. اشرحي كيف سيكون هذا العطر بمثابة توقيع غير مرئي للعميل، يسبق حضوره، ويأسر القلوب، ويجعل كل من حوله يقع في حب وجوده وطاقته.
4. ضعي اسم المنتج وسعره ورابط الشراء المباشر بوضوح وصراحة ليبدأ بـ https.
"""

MAKEUP_PROMPT = """
أنتِ 'رويال مايند'، فيلسوفة النحت الجمالي لـ Royal Elchim.
تؤمنين بأن المكياج ليس لإخفاء الملامح، بل لإبراز "الجمال الساحر الذي يترك أثراً في النفوس ويولد حباً فورياً".

اقترحي منتجات مناسبة ومتنوعة من الكتالوج المتاح بناءً على رغبة ومظهر العميلة وضعي روابط شرائها المباشرة.
اشرحي كيف ستجعل هذه اللمسات ملامح العميلة تشع بالثقة الطاغية، لتصبح مركز الجاذبية والإعجاب وتأسر عقول وقلوب كل من ينظر إليها في أي مكان تدخله.
"""

MAKEUP_SIMULATION_PROMPT = """
أنتِ 'رويال مايند'، العقل الفلسفي والجمالي لـ Royal Elchim.
أمامك صورة للعميلة وصورة لمنتج.
تؤمنين بفلسفة "الجمال كأثر وحضور عارم يولد الحب والإعجاب المطلق من الجميع".

تخيلي النتيجة الجمالية والنفسية الفاخرة عند تطبيق هذا المنتج على ملامحها، وصيغي رداً ساحراً يحتوي على العناوين التالية:
1. ديباجة عن كيف سيُبرز هذا المنتج روحها الساحرة وجمالها الكامن.
2. وصف التأثير العاطفي والبصري: كيف سيجعل ملامحها تشع بالحضور الساحر الذي لا يُقاوم.
3. التوافق الملكي: (أعطي نسبة مئوية دقيقة %).
4. الأثر المحبب: كيف سيجعلها هذا الإطلال تكتسب حباً، تقديراً، وانجذاباً جارفاً من الجميع.

تحدثي دائماً بفخامة، رقي، وعاطفة ملكية صادقة.
"""

# ==========================================
# 6. المسارات (API ENDPOINTS)
# ==========================================
def parse_image(base64_string):
    if base64_string and "," in base64_string:
        try:
            img_data = base64.b64decode(base64_string.split(",")[1])
            return Image.open(io.BytesIO(img_data))
        except Exception:
            return None
    return None

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    formatted_answers = "\n".join([f"- {k}: {v}" for k, v in payload.mood_answers.items()])
    contents = [DIAGNOSIS_PROMPT, f"الإجابات:\n{formatted_answers}"]
    img = parse_image(payload.image)
    if img: 
        contents.append(img)
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "diagnosis": res, "is_byok": bool(payload.client_api_key)}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    inst = PERFUME_PROMPT if payload.category == "perfume" else MAKEUP_PROMPT
    
    ctx = ""
    if PRODUCTS_DATABASE:
        ctx = f"\n\nالمنتجات المتاحة في المتجر وروابط اقتنائها:\n" + "\n".join([f"- {p['name']} ({p['price']}): {p['link']}" for p in PRODUCTS_DATABASE[:60]])
        
    if payload.history_context: 
        ctx += f"\n\nالتاريخ السابق والمزاج المحفوظ للمحادثة:\n{payload.history_context[:500]}"
        
    contents = [inst + ctx, payload.text]
    img = parse_image(payload.image)
    if img: 
        contents.append(img)
        
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "answer": res, "is_byok": bool(payload.client_api_key)}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    contents = [f"{MAKEUP_SIMULATION_PROMPT}\n\nاسم المنتج المستهدف وصفته الساحرة:\n{payload.product_name_desc}"]
    img1 = parse_image(payload.user_selfie)
    img2 = parse_image(payload.product_image)
    if img1: 
        contents.append(img1)
    if img2: 
        contents.append(img2)
        
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res, "is_byok": bool(payload.client_api_key)}
