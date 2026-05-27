from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
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

# النماذج الحديثة
VISION_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ==========================================
# 2. قراءة قاعدة البيانات
# ==========================================
def load_inventory():
    try:
        df = pd.read_csv("Royal_Elchim_Final_Database.csv")
        products = []
        for _, row in df.iterrows():
            products.append({
                "name": str(row['Product_Name']).strip(),
                "price": str(row['Price']).strip(),
                "link": str(row['Product_Link']).strip()
            })
        return products
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
    image: Optional[str] = None
    category: str  
    history_context: Optional[str] = None
    client_api_key: Optional[str] = None

class SimulationPayload(BaseModel):
    user_selfie: str
    product_image: str
    product_name_desc: str
    client_api_key: Optional[str] = None

# ==========================================
# 4. محرك المرونة (MATRIX ROUTER)
# ==========================================
def robust_generate(client_api_key, contents, models_list):
    if client_api_key and client_api_key.strip():
        keys_to_use = [client_api_key.strip()]
    else:
        if not SYSTEM_API_KEYS:
            raise HTTPException(status_code=500, detail="لا توجد مفاتيح النظام.")
        keys_to_use = SYSTEM_API_KEYS.copy()
        random.shuffle(keys_to_use)

    for model_name in models_list:
        for key in keys_to_use:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    client = genai.Client(api_key=key)
                    response = client.models.generate_content(model=model_name, contents=contents)
                    if response and response.text:
                        return response.text, model_name
                except Exception as e:
                    error_msg = str(e)
                    if "503" in error_msg:
                        time.sleep(1.5)
                        continue
                    else:
                        break
    raise HTTPException(status_code=503, detail="خبراء رويال مايند مشغولون حالياً. يرجى المحاولة بعد لحظات قليلة.")

# ==========================================
# 5. التوجيهات الفلسفية (PROMPTS)
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
رسالتكِ هي البحث عن الجمال الذي يملك حضوراً طاغياً ويولد المحبة.

اقترحي عطراً من الكتالوج المتاح وروابط الشراء.
اشرحي كيف سيكون هذا العطر بمثابة توقيع غير مرئي للعميل، يسبق حضوره، ويأسر القلوب، ويجعل كل من حوله يقع في حب طاقته المهيبة أو الأنثوية.
"""

MAKEUP_PROMPT = """
أنتِ 'رويال مايند'، فيلسوفة النحت الجمالي.
تؤمنين بأن المكياج ليس لإخفاء الملامح، بل لإبراز "الجمال الذي يترك أثراً ويولد حباً".

اقترحي المنتجات المتاحة وروابط شرائها.
اشرحي كيف ستجعل هذه اللمسات ملامح العميلة تشع بالثقة، لتصبح هي مركز الجاذبية والإعجاب، وتولد حالة من الانبهار والحب في أي مكان تدخله.
"""

MAKEUP_SIMULATION_PROMPT = """
أنتِ 'رويال مايند'، العقل الفلسفي والجمالي لـ Royal Elchim.
أمامك صورة للعميلة وصورة لمنتج.
تؤمنين بفلسفة "الجمال كأثر وحضور يولد الحب والإعجاب من الجميع".

تخيلي النتيجة الجمالية عند تطبيق هذا المنتج على ملامحها، وصيغي رداً ساحراً يحتوي على:
1. ديباجة عن كيف سيُبرز هذا المنتج روحها الساحرة وجمالها الكامن.
2. وصف التأثير: كيف سيجعل ملامحها تشع بالحضور الذي لا يُقاوم.
3. التوافق الملكي: (نسبة مئوية %).
4. الأثر العاطفي: كيف سيجعلها هذا الإطلال تشعر بثقة مطلقة، ويجذب حب وإعجاب كل من ينظر إليها.

تحدثي دائماً بفخامة، رقي، وعاطفة صادقة.
"""

# ==========================================
# 6. المسارات (API ENDPOINTS)
# ==========================================
def parse_image(base64_string):
    if base64_string and "," in base64_string:
        img_data = base64.b64decode(base64_string.split(",")[1])
        return Image.open(io.BytesIO(img_data))
    return None

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    formatted_answers = "\n".join([f"- {k}: {v}" for k, v in payload.mood_answers.items()])
    contents = [DIAGNOSIS_PROMPT, f"الإجابات:\n{formatted_answers}"]
    img = parse_image(payload.image)
    if img: contents.append(img)
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "diagnosis": res, "is_byok": bool(payload.client_api_key)}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    inst = PERFUME_PROMPT if payload.category == "perfume" else MAKEUP_PROMPT
    ctx = f"\n\nالمنتجات المتاحة:\n" + "\n".join([f"- {p['name']} ({p['price']}): {p['link']}" for p in PRODUCTS_DATABASE[:80]])
    if payload.history_context: ctx += f"\n\nالتاريخ:\n{payload.history_context[:1000]}"
    contents = [inst + ctx, payload.text]
    img = parse_image(payload.image)
    if img: contents.append(img)
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS if img else TEXT_MODELS)
    return {"status": "success", "answer": res, "is_byok": bool(payload.client_api_key)}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    contents = [f"{MAKEUP_SIMULATION_PROMPT}\n\nاسم المنتج:\n{payload.product_name_desc}"]
    img1 = parse_image(payload.user_selfie)
    img2 = parse_image(payload.product_image)
    if img1: contents.append(img1)
    if img2: contents.append(img2)
    res, model = robust_generate(payload.client_api_key, contents, VISION_MODELS)
    return {"status": "success", "simulation_result": res, "is_byok": bool(payload.client_api_key)}
