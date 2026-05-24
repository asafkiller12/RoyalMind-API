from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # ✅ إضافة هذه المكتبة
from pydantic import BaseModel
import google.generativeai as genai
import os

# ==========================================
# ⚙️ إعدادات النظام
# ==========================================
GOOGLE_API_KEY = "AIzaSyCWPe5tU8YZB3T0v6o0jBtcI6QhzunQEfE" 
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash')

app = FastAPI(title="RoyalMind Business API")

# ✅ إضافة تصريح CORS لكي يعمل الشات من أي مكان في العالم
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # السماح لجميع المواقع بالاتصال بالسيرفر
    allow_credentials=True,
    allow_methods=["*"], # السماح بجميع أنواع الطلبات (POST, GET, etc)
    allow_headers=["*"], # السماح بجميع أنواع الرؤوس (Headers)
)

class Query(BaseModel):
    text: str
    user_id: str = "guest"

def get_showroom_context(query: str):
    knowledge_base = {
        "سعر": "أسعارنا تبدأ من 10 ج.م لدينا خصومات 30% حالياً.",
        "مواعيد": "نحن نعمل يومياً من الساعة 10 صباحاً وحتى 10 مساءً.",
        "عنوان": "معارضنا يقع في قلب مدينه الاقصر ويضا في قلب محافظه البحر الاحمر.",
        "توصيل": "نوفر خدمة التوصيل لجميع انحاء الجمهوريه."
    }
    context = ""
    for key in knowledge_base:
        if key in query:
            context += f"\nمعلومة من المعرض: {knowledge_base[key]}"
    return context

@app.get("/")
def read_root():
    return {"status": "Online", "message": "Welcome to RoyalMind Intelligent Server"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        context = get_showroom_context(query.text)
        system_prompt = (
            "أنت الآن 'RoyalMind'، الخبير التجميلي والمساعد الذكي لموقع Royal Elchim. "
            "أنت خبير في العناية بالبشرة، المكياج، والعطور. "
            "وظيفتك هي مساعدة العملاء في اختيار المنتجات المناسبة لبشرتهم، "
            "الإجابة على استفساراتهم بلباقة مفرطة وأسلوب راقٍ، وتحفيزهم على تجربة منتجات Royal Elchim. "
            f"استخدم هذه المعلومات إذا كانت ذات صلة: {context}"
        )
        full_prompt = f"{system_prompt}\n\nالعميل: {query.text}"
        response = model.generate_content(full_prompt)
        return {"status": "success", "answer": response.text, "model": "gemini-2.5-flash"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
