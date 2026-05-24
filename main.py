from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

# ==========================================
# ⚙️ إعدادات النظام
# ==========================================
GOOGLE_API_KEY = "AIzaSyCWPe5tU8YZB3T0v6o0jBtcI6QhzunQEfE" 
genai.configure(api_key=GOOGLE_API_KEY)

# ✅ التعديل هنا: استخدام الموديل الذي نجح في تجربتك السابقة
model = genai.GenerativeModel('models/gemini-2.5-flash')

app = FastAPI(title="RoyalMind Business API")

class Query(BaseModel):
    text: str
    user_id: str = "guest"

# ==========================================
# 🧠 منطق الذاكرة الممتدة (نسخة تجريبية)
# ==========================================
def get_showroom_context(query: str):
    knowledge_base = {
        "سعر": "أسعارنا تبدأ من 5000 ج.م وتختلف حسب الموديل. لدينا خصومات 10% حالياً.",
        "مواعيد": "نحن نعمل يومياً من الساعة 10 صباحاً وحتى 10 مساءً.",
        "عنوان": "معرضنا يقع في قلب المدينة، يمكنك الوصول إلينا عبر خرائط جوجل.",
        "توصيل": "نوفر خدمة التوصيل والتركيب المجاني داخل القاهرة والجيزة."
    }
    
    context = ""
    for key in knowledge_base:
        if key in query:
            context += f"\nمعلومة من المعرض: {knowledge_base[key]}"
            
    return context

# ==========================================
# 🚀 نقاط الاتصال (API Endpoints)
# ==========================================

@app.get("/")
def read_root():
    return {
        "status": "Online", 
        "message": "Welcome to RoyalMind Intelligent Server", 
        "version": "1.1-Beta"
    }

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        context = get_showroom_context(query.text)
        
        system_prompt = (
            "أنت الآن 'RoyalMind'، المساعد الذكي الرسمي لمعرض أثاث راقٍ. "
            "وظيفتك هي مساعدة العملاء بلباقة، تقديم معلومات دقيقة، "
            "وجذب العميل لزيارة المعرض. "
            f"استخدم هذه المعلومات إذا كانت ذات صلة: {context}"
        )
        
        full_prompt = f"{system_prompt}\n\nالعميل: {query.text}"
        
        # توليد الإجابة
        response = model.generate_content(full_prompt)
        
        return {
            "status": "success",
            "answer": response.text,
            "model": "gemini-2.5-flash"
        }
    except Exception as e:
        # طباعة الخطأ في الـ Terminal لكي نراه إذا حدثت مشكلة
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
