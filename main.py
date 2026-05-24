from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os

# ==========================================
# ⚙️ إعدادات النظام والأمان
# ==========================================
# جلب المفتاح من "خزنة" Railway لضمان الأمان وعدم تسريبه في GitHub
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 

if not GOOGLE_API_KEY:
    print("⚠️ تحذير: مفتاح API غير موجود في إعدادات السيرفر (Variables)!")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# استخدام الموديل المتطور والسرع Gemini 2.5 Flash
model = genai.GenerativeModel('models/gemini-2.5-flash')

app = FastAPI(title="RoyalMind Business API")

# ✅ السماح للمتصفحات بالاتصال بالسيرفر (حل مشكلة CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# نموذج استقبال البيانات من العميل
class Query(BaseModel):
    text: str
    user_id: str = "guest"

# ==========================================
# 🧠 الذاكرة الممتدة لـ Royal Elchim (قاعدة المعرفة)
# ==========================================
def get_showroom_context(query: str):
    """
    تحويل استفسارات العميل إلى معلومات دقيقة مستمدة من هوية Royal Elchim
    """
    knowledge_base = {
        # معلومات عن العطر الرئيسي (من الصورة)
        "ريحة": "عطر Royal Hash Rooted يتميز بفتحة عطرية من الدخان العشبي الحاد (sharp herbal smoke)، ثم يستقر على قاعدة من الراتنج الترابي والمسك (earthy resin and musk). إنه عطر جريء يجسد الأناقة المظلمة والحضور الطاغي.",
        "مكونات": "يتكون Royal Hash Rooted من مزيج من الدخان العشبي، الراتنج الترابي، والمسك، مما يمنحه طابعاً من الفخامة والغموض والعمق.",
        "استخدام": "لأفضل نتيجة وثبات، يُنصح برش العطر على نقاط النبض في الجسم: الرقبة، المعصمين، وخلف الأذنين.",
        "حجم": "الزجاجة تأتي بحجم 50 مل (1.7 fl. oz)، وهي مصممة لتكون رفيقك في كل المناسبات الفاخرة.",
        
        # معلومات الهوية والموقع (من حساب الشركة)
        "موقع": "نحن فخورون بأن علامتنا التجارية Royal Elchim تنطلق من مدينة السحر والتاريخ 'الأقصر' (Luxor)، لننقل عبق الحضارة بلمسة عصرية فاخرة.",
        "تواصل": "يمكنكم التواصل معنا مباشرة عبر واتساب على الرقم: +20 10 12935706 أو زيارة موقعنا الرسمي www.royalelchim.app",
        "صنع": "منتجاتنا صُنعت في مصر (Made in Egypt) وبأعلى معايير الجودة العالمية لتناسب أصحاب الذوق الرفيع.",
        "تحذير": "للاستخدام الخارجي فقط. يُحفظ بعيداً عن متناول الأطفال، وبعيداً عن الحرارة وأشعة الشمس المباشرة."
    }
    
    context = ""
    # البحث عن الكلمات المفتاحية في سؤال العميل لتقديم الإجابة الأدق
    for key in knowledge_base:
        if key in query:
            context += f"\nمعلومة من Royal Elchim: {knowledge_base[key]}"
            
    return context

# ==========================================
# 🚀 نقاط الاتصال (API Endpoints)
# ==========================================

@app.get("/")
def read_root():
    return {
        "status": "Online", 
        "message": "Welcome to RoyalMind Intelligent Server - Luxury Fragrance Expert", 
        "location": "Luxor, Egypt"
    }

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key missing in server settings")
            
        # 1. جلب المعلومات ذات الصلة من قاعدة المعرفة
        context = get_showroom_context(query.text)
        
        # 2. صياغة شخصية المساعد (The Persona)
        system_prompt = (
            "أنت الآن 'RoyalMind'، السفير الرقمي والخبير التجميلي لعلامة 'Royal Elchim' الفاخرة للعطور والمستحضرات. "
            "علامتكم التجارية تنطلق من مدينة الأقصر العريقة، مما يمنحكم مزيجاً من التاريخ والفخامة. "
            "أسلوبك في الحديث يجب أن يكون: راقياً، لبقاً جداً، واثقاً، ويوحي بالفخامة (Luxury Tone). "
            "أنت لا تبيع مجرد منتج، بل تبيع 'تجربة من الأناقة والتميز'. "
            "اجعل إجاباتك قصيرة، مركزة، ومحفزة للعميل على تجربة المنتجات. "
            f"استخدم هذه المعلومات التقنية بدقة إذا كانت ذات صلة: {context}"
        )
        
        full_prompt = f"{system_prompt}\n\nالعميل: {query.text}"
        
        # 3. توليد الإجابة باستخدام Gemini 2.5 Flash
        response = model.generate_content(full_prompt)
        
        return {
            "status": "success",
            "answer": response.text,
            "model": "gemini-2.5-flash"
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
