from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import base64
import io
from PIL import Image

# ==========================================
# ⚙️ إعدادات النظام والأمان
# ==========================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 

if not GOOGLE_API_KEY:
    print("⚠️ تحذير: مفتاح API غير موجود في إعدادات السيرفر!")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash')

app = FastAPI(title="RoyalMind Total Luxury API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

class Query(BaseModel):
    text: str
    image: str = None
    user_id: str = "guest"

# ==========================================
# 🧠 الذاكرة الشاملة (الجمال + العطور + الهوية)
# ==========================================
def get_total_context(query: str):
    knowledge_base = {
        "برج": "نحن نصمم عطوراً تتناغم مع طاقة الأبراج؛ فكل برج له نوتات تعزز جاذبيته الشخصية.",
        "حالة نفسية": "العطر علاج للنفس؛ نوفر نوتات للاسترخاء، أو الطاقة، أو الرومانسية بناءً على الحالة المزاجية.",
        "صباحي": "عطور صباحية منعشة (حمضيات، زهور خفيفة) تمنح الحيوية.",
        "مسائي": "عطور مسائية عميقة (أخشاب، مسك، عنبر) تليق بالسهرات والغموض.",
        "نيش": "مجموعة 'النيش' هي قطع فنية حصرية ونادرة لمن يبحث عن التميز المطلق.",
        "زيوت": "نوفر خدمة تركيب الزيوت العطرية الخام مع التحكم في نسبة المثبت لثبات (كاجوال أو مركز).",
        "عطر": "عطر Royal Hash Rooted: فتحة دخانية عشبية، قاعدة من الراتنج والمسك، يجسد الأناقة المظلمة.",
        "بشرة": "نقدم استشارات دقيقة لنوع البشرة (دهنية، جافة، مختلطة) لترشيح أفضل منتجات العناية.",
        "ميكب": "نساعد في اختيار ألوان المكياج التي تتناسب مع لون البشرة وتكمل الإطلالة العطرية.",
        "تجميل": "نعتمد على أحدث صيحات التجميل العالمية لضمان إطلالة ملكية تبرز ملامح الوجه.",
        "موقع": "علامتنا Royal Elchim تنطلق من قلب 'الأقصر' العريقة، حيث يلتقي سحر التاريخ بالفخامة العصرية.",
        "تواصل": "واتساب: +20 10 12935706 | الموقع: www.royalelchim.app | صنع في مصر بجودة عالمية.",
        "حجم": "زجاجاتنا تأتي بحجم 50 مل (1.7 fl. oz) بتصميم فاخر."
    }
    
    context = ""
    for key in knowledge_base:
        if key in query:
            context += f"\nمعلومة من Royal Elchim: {knowledge_base[key]}"
    return context

# ==========================================
# 🚀 نقطة الاتصال الذكية
# ==========================================

@app.get("/")
def read_root():
    return {"status": "Online", "message": "RoyalMind Total Luxury Expert is Active!"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key missing in server settings")
            
        context = get_total_context(query.text)
        
        system_prompt = (
            "أنت الآن 'RoyalMind'، المستشار الشامل للفخامة في Royal Elchim بالأقصر. "
            "أنت لست مجرد بائع، بل خبير يربط بين (الجمال، العطر، والحالة النفسية). \n\n"
            "مهمتك هي تقديم 'إطلالة متكاملة' (Total Look):\n"
            "1. إذا سأل العميل عن عطر: اربطه بحالته النفسية، برجه، وتوقيت اليوم.\n"
            "2. إذا أرسل العميل صورة: حلل ملامحه وبشرته، ثم اقترح (مكياج مناسب + عطر يكمل هذه الإطلالة).\n"
            "3. الربط الذكي: إذا كانت الحالة 'صباحية مبهجة'، اقترح (مكياج ناعم + عطر حمضيات منعش).\n"
            "4. إذا كانت الحالة 'مسائية غامضة'، اقترح (مكياج جريء + عطر نيش ثقيل).\n"
            "5. التخصيص: تحدث عن نسب الزيوت والمثبتات لضمان الثبات حسب رغبة العميل.\n\n"
            "أسلوبك: راقٍ، ملهم، يوحي بالفخامة والملكية، ويجعل العميل يشعر أنه يحصل على استشارة خاصة جداً. "
            f"استخدم هذه المعلومات كمرجع أساسي: {context}"
        )

        # بناء محتوى الطلب لـ Gemini
        content = [system_prompt, query.text]
        
        if query.image:
            image_data = base64.b64decode(query.image.split(",")[1])
            img = Image.open(io.BytesIO(image_data))
            content.append(img)

        response = model.generate_content(content)
        return {"status": "success", "answer": response.text, "model": "gemini-2.5-flash"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
