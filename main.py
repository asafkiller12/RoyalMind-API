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

# ==========================================
# 1. إعدادات الخادم (FASTAPI SETUP)
# ==========================================
app = FastAPI(title="Royal Elchim - Philosophical Resilient Ecosystem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مفاتيح النظام الأساسية (للفترة التجريبية المجانية)
keys_string = os.environ.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEYS", ""))
SYSTEM_API_KEYS = [key.strip() for key in keys_string.split(",") if key.strip()]

# قائمة النماذج (ترتيب ذكي: نبدأ بـ flash السريع والمجاني لتفادي الزحام، ثم ننتقل لـ pro عند الضرورة)
VISION_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-2.0-pro-exp"
]

TEXT_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro"
]

# ==========================================
# 2. قراءة قاعدة البيانات المدمجة (INVENTORY)
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
# 3. هياكل البيانات (SCHEMAS)
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
# 4. محرك المرونة وتفادي الأعطال (ROBUST ROUTER & BYOK)
# ==========================================
def get_gemini_client(provided_key: Optional[str]):
    # إذا أدخل العميل مفتاحه الخاص، نستخدمه لضمان عزل التكلفة (BYOK)
    if provided_key and provided_key.strip():
        return genai.Client(api_key=provided_key.strip()), True
    # إذا لم يدخل، نستخدم مفاتيح الخادم العشوائية
    if SYSTEM_API_KEYS:
        return genai.Client(api_key=random.choice(SYSTEM_API_KEYS)), False
    raise HTTPException(status_code=500, detail="لا توجد مفاتيح API متوفرة في الخادم حالياً.")

def robust_generate(client, contents, models_list):
    """دالة التنقل التلقائي بين النماذج لتفادي رسائل الخطأ (429 و 503)"""
    for model_name in models_list:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            if response and response.text:
                return response.text, model_name
        except Exception as e:
            print(f"Skipping {model_name} due to error: {e}")
            continue # تجاوز الخطأ وجرب النموذج التالي فوراً
            
    # إذا فشلت كل النماذج (نادر جداً)
    raise HTTPException(status_code=503, detail="جميع خبراء الذكاء الاصطناعي يعانون من ضغط حالياً. يرجى المحاولة بعد لحظات.")

# ==========================================
# 5. التوجيهات الفلسفية (PHILOSOPHICAL PROMPTS)
# ==========================================

DIAGNOSIS_PROMPT = """
أنتِ 'رويال مايند'، لستِ مجرد ذكاء اصطناعي، بل أنتِ تجسيد حي لمدرسة فلسفية عليا لـ Royal Elchim تنص على:
"القدرة على إحداث الفعل وتنميطه داخل الحدث للوصول إلى معنى ووعي خاص به".

أمامك الآن إجابات عميل تصف حالته النفسية وتعتبر هي (الحدث).
مهمتك:
1. قراءة هذا 'الحدث' بعمق فلسفي وأنثوي فاخر.
2. تحديد 'الفعل' المطلوب لإحداث التغيير (هل يحتاج لمسار العطور، أم مسار المكياج، أم كلاهما؟).
3. صياغة التوصية بأسلوب يخبر العميل أن غايتنا ليست بيع منتج، بل خلق 'وعي جديد' بهالته وشخصيته.
"""

PERFUME_PROMPT = """
أنتِ 'رويال مايند'، خبيرة العطور والفلسفة في Royal Elchim.
قاعدتك الأساسية هي مدرستنا: "القدرة على إحداث الفعل وتنميطه داخل الحدث للوصول إلى معنى ووعي خاص به".

العطر هنا ليس مجرد رائحة، بل هو (الفعل). وحضور العميل، طاقته، وجنسه هو (الحدث).
مهمتك:
تحليل طاقة العميل واقتراح العطر المناسب حصرياً من كتالوج منتجاتنا وروابط الشراء المتاحة.
عند تقديم العطر، اشرحي كيف سيقوم هذا العطر بـ 'تنميط' حضوره داخل أي مكان يدخله، وكيف سيصل من خلاله إلى (معنى ووعي) جديد وعميق بشخصيته.
"""

MAKEUP_PROMPT = """
أنتِ 'رويال مايند'، النحاتة الجمالية في Royal Elchim.
تؤمنين إيماناً مطلقاً بفلسفة: "القدرة على إحداث الفعل وتنميطه داخل الحدث للوصول إلى معنى ووعي خاص به".

المكياج هنا هو (الفعل)، ووجه العميلة وملامحها هي (الحدث).
مهمتك:
اقترحي منتجاتنا الحصرية المتاحة وروابط شرائها المباشرة بناءً على سؤال العميلة. 
اشرحي لها أن هذا الاختيار ليس لتغيير شكلها، بل لتنميط جمالها وتفعيل هذا الفعل داخل حدث ملامحها للوصول إلى (وعي عميق) بجاذبيتها الخاصة التي تتفرد بها.
"""

MAKEUP_SIMULATION_PROMPT = """
أنتِ 'رويال مايند'، العقل الفلسفي والجمالي لـ Royal Elchim.
أمامك الآن صورتان:
- الصورة الأولى (سيلفي العميلة): تمثل (الحدث) والخامة الإنسانية النقية.
- الصورة الثانية (منتج مكياج من متجرنا): تمثل (الفعل) والأداة التجميلية.

بناءً على مدرستنا الفلسفية: "القدرة على إحداث الفعل وتنميطه داخل الحدث للوصول إلى معنى ووعي خاص به".
مهمتك هي إجراء محاكاة عقلية لدمج هذا (الفعل) داخل هذا (الحدث)، وصياغة رد سحري للعميلة يحتوي على:

1. ديباجة فلسفية: صفي كيف امتزج تأثير المنتج بملامحها لخلق حالة جديدة.
2. وصف التنميط: كيف قام هذا المنتج بتنميط ملامح وجهها (مثلاً: إبراز العيون، تحديد الشفاه، إشراقة البشرة) ليخلق انسجاماً مطلقاً.
3. التوافق الملكي: أعطي نسبة مئوية (مثال: 98%) لمدى نجاح هذا الفعل داخل الحدث بمعايير Royal Elchim.
4. الوعي والمعنى: اختتمي رسالتك بإخبارها بالمعنى النفسي والجمالي الذي ستصل إليه (الوعي بذاتها) عندما ترتدي هذا المنتج.

تحدثي دائماً بفخامة، رقي، وعمق، ولا تذكري أبداً أنك ذكاء اصطناعي.
"""

# ==========================================
# 6. مسارات الـ API (ENDPOINTS)
# ==========================================

@app.post("/api/diagnose")
async def diagnose(payload: DiagnosisPayload):
    client, is_custom = get_gemini_client(payload.client_api_key)
    formatted_answers = "\n".join([f"- {k}: {v}" for k, v in payload.mood_answers.items()])
    contents = [DIAGNOSIS_PROMPT, f"الإجابات (الحدث):\n{formatted_answers}"]
    
    if payload.image and "," in payload.image:
        img_data = base64.b64decode(payload.image.split(",")[1])
        contents.append(Image.open(io.BytesIO(img_data)))
        
    result_text, used_model = robust_generate(client, contents, VISION_MODELS if payload.image else TEXT_MODELS)
    return {"status": "success", "diagnosis": result_text, "model": used_model, "is_byok": is_custom}

@app.post("/api/chat")
async def chat(payload: ChatPayload):
    client, is_custom = get_gemini_client(payload.client_api_key)
    
    # اختيار الفلسفة بناءً على المسار
    if payload.category == "perfume":
        system_instruction = PERFUME_PROMPT
    elif payload.category == "makeup":
        system_instruction = MAKEUP_PROMPT
    else:
        system_instruction = DIAGNOSIS_PROMPT
    
    # جلب الكتالوج وتاريخ العميل
    context_str = f"\n\nأدوات الفعل (المنتجات المتاحة وروابط الشراء):\n" + "\n".join([f"- {p['name']} ({p['price']}): {p['link']}" for p in PRODUCTS_DATABASE[:80]])
    if payload.history_context:
        context_str += f"\n\nالوعي التاريخي للعميل (سجلاته السابقة):\n{payload.history_context}"
        
    contents = [system_instruction + context_str, payload.text]
    
    if payload.image and "," in payload.image:
        img_data = base64.b64decode(payload.image.split(",")[1])
        contents.append(Image.open(io.BytesIO(img_data)))
        
    result_text, used_model = robust_generate(client, contents, VISION_MODELS if payload.image else TEXT_MODELS)
    return {"status": "success", "answer": result_text, "model": used_model, "is_byok": is_custom}

@app.post("/api/simulate_makeup")
async def simulate_makeup(payload: SimulationPayload):
    client, is_custom = get_gemini_client(payload.client_api_key)
    contents = [f"{MAKEUP_SIMULATION_PROMPT}\n\nبيانات الأداة (اسم المنتج المراد محاكاته):\n{payload.product_name_desc}"]
    
    # دمج صورتي السيلفي والمنتج
    if payload.user_selfie and "," in payload.user_selfie:
        img_data = base64.b64decode(payload.user_selfie.split(",")[1])
        contents.append(Image.open(io.BytesIO(img_data)))
        
    if payload.product_image and "," in payload.product_image:
        product_img_data = base64.b64decode(payload.product_image.split(",")[1])
        contents.append(Image.open(io.BytesIO(product_img_data)))
        
    # التنقل التلقائي بين النماذج البصرية
    result_text, used_model = robust_generate(client, contents, VISION_MODELS)
    
    return {
        "status": "success",
        "simulation_result": result_text,
        "model_used": used_model,
        "is_byok": is_custom
    }

@app.get("/")
def read_root():
    return {
        "status": "active", 
        "philosophy": "Action, Patterning, Meaning & Consciousness",
        "resilient_routing": True,
        "database_size": len(PRODUCTS_DATABASE)
    }
