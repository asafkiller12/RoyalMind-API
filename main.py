from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import pandas as pd
import base64
import io
from PIL import Image

# ==========================================
# ⚙️ إعدادات النظام والأمان
# ==========================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 

if not GOOGLE_API_KEY:
    print("⚠️ Warning: GOOGLE_API_KEY not found in environment variables!")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash')

app = FastAPI(title="RoyalMind Total Luxury API")

# السماح بالاتصال من المتصفح (CORS)
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
# 🧠 نظام الذاكرة الديناميكية (Google Sheets)
# ==========================================
# 🚩 تأكد من وضع رابط الـ CSV الصحيح هنا
SHEET_CSV_URL = "ضع_رابط_GOOGLE_SHEET_CSV_هنا"

def get_dynamic_context(query: str):
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        relevant_products = []
        for index, row in df.iterrows():
            # البحث عن الكلمات المفتاحية في كافة الأعمدة
            search_text = f"{row.get('Product', '')} {row.get('Category', '')} {row.get('Mood', '')} {row.get('Zodiac', '')}"
            if any(word in query for word in search_text.split()):
                product_info = f"المنتج: {row.get('Product')} | السعر: {row.get('Price')} | الوصف: {row.get('Description')} | مناسب لـ: {row.get('Mood')} و {row.get('Zodiac')}"
                relevant_products.append(product_info)
        
        if relevant_products:
            return "\n".join(relevant_products)
        return "لا يوجد منتج مطابق تماماً حالياً، يرجى اقتراح بدائل فاخرة من مجموعتنا."
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return "عذراً، هناك مشكلة في الوصول لقاعدة بيانات المنتجات."

# ==========================================
# 🚀 نقاط الاتصال (API Endpoints)
# ==========================================

@app.get("/")
def read_root():
    return {"status": "Online", "message": "RoyalMind Total Luxury Expert is Active!"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key missing in server settings")
            
        # جلب السياق من جدول جوجل
        context = get_dynamic_context(query.text)
        
        system_prompt = (
            "أنت 'RoyalMind'، المستشار الشامل للفخامة في Royal Elchim بالأقصر. "
            "أنت خبير يربط بين (الجمال، العطر، والحالة النفسية، والأبراج). "
            "قواعدك: \n"
            "1. إذا وجدت منتجات في السياق تناسب طلب العميل، رشحها له بدقة مع ذكر السعر والوصف.\n"
            "2. إذا أرسل العميل صورة: حلل ملامحه وبشرته واقترح (ميكب + عطر) يكمل الإطلالة.\n"
            "3. حافظ على أسلوب ملكي، لبق، ومقنع جداً.\n"
            f"بيانات المنتجات الحالية: {context}"
        )

        content = [system_prompt, query.text]
        
        if query.image:
            # معالجة الصورة بشكل صحيح
            image_data = base64.b64decode(query.image.split(",")[1])
            img = Image.open(io.BytesIO(image_// data)) # تصحيح أخير
            # التصحيح النهائي للسطر أعلاه:
            # img = Image.open(io.BytesIO(image_data))
            content.append(img)

        # تصحيح نهائي: استبدل السطر السابق بـ img = Image.open(io.BytesIO(image_data))
        
        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
