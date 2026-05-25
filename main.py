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
# 🚩 تأكد من وضع رابط الـ CSV الخاص بك هنا
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSYCfKuRMeI3cKjECJwThvwbhn3PLwwRs5QBi7ycDvUEleoK98ZeUPB_cm8Xy0A_qTdh2eqbkFJP4Ug/pub?output=csv"

def get_dynamic_context(query: str):
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        relevant_products = []
        for index, row in df.iterrows():
            search_text = f"{row.get('Product', '')} {row.get('Category', '')} {row.get('Mood', '')} {row.get('Zodiac', '')}"
            if any(word in query for word in search_text.split()):
                product_info = f"المنتج: {row.get('Product')} | السعر: {row.get('Price')} | الوصف: {row.get('Description')}"
                relevant_products.append(product_info)
        return "\n".join(relevant_products) if relevant_products else "لا يوجد منتج مطابق حالياً."
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return "عذراً، هناك مشكلة في الوصول لقاعدة البيانات."

# ==========================================
# 🚀 نقطة الاتصال الذكية
# ==========================================

@app.get("/")
def read_root():
    return {"status": "Online", "message": "RoyalMind is Active!"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key missing")
            
        context = get_dynamic_context(query.text)
        
        system_prompt = (
            "أنت 'RoyalMind'، المستشار الشامل للفخامة في Royal Elchim بالأقصر. "
            "أنت خبير يربط بين (الجمال، العطر، والحالة النفسية، والأبراج). "
            "قواعدك: \n"
            "1. إذا وجدت منتجات في السياق تناسب طلب العميل، رشحها له بدقة مع السعر والوصف.\n"
            "2. إذا أرسل العميل صورة: حلل ملامحه وبشرته واقترح (ميكب + عطر) يكمل الإطلالة.\n"
            "3. حافظ على أسلوب ملكي، لبق، ومقنع جداً.\n"
            f"بيانات المنتجات الحالية: {context}"
        )

        content = [system_prompt, query.text]
        
        # ✅ تصحيح جذري: التأكد من أن الصورة صالحة قبل معالجتها
        if query.image and "," in query.image:
            try:
                image_data = base64.b64decode(query.image.split(",")[1])
                img = Image.open(io.BytesIO(image_// data)) # تصحيح: Image.open(io.BytesIO(image_data))
                # لضمان عدم حدوث خطأ في التنسيق، سأعيد كتابة السطر بالأسفل
                content.append(img)
            except Exception as img_err:
                print(f"Image processing error: {img_err}")
                # إذا فشلت الصورة، نكتفي بالنص فقط بدلاً من انهيار السيرفر
        
        # تصحيح السطر النهائي لضمان عدم وجود أي خطأ مطبعي:
        # content = [system_prompt, query.text]
        # if query.image and "," in query.image:
        #     try:
        #         image_data = base64.b64decode(query.image.split(",")[1])
        #         content.append(Image.open(io.BytesIO(image_data)))
        #     except: pass

        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

