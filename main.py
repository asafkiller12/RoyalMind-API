from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import pandas as pd
import base64
import io
from PIL import Image

# 1. إعدادات المفتاح
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash')
app = FastAPI(title="RoyalMind Total Luxury API")

# 2. إعدادات CORS
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

# 3. الذاكرة الديناميكية
SHEET_CSV_URL = "ضع_رابط_GOOGLE_SHEET_CSV_هنا"

def get_dynamic_context(query: str):
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        relevant_products = []
        for index, row in df.iterrows():
            search_text = f"{row.get('Product', '')} {row.get('Category', '')} {row.get('Mood', '')} {row.get('Zodiac', '')}"
            if any(word in query for word in search_// text.split()): # تصحيح: search_text.split()
                product_info = f"المنتج: {row.get('Product')} | السعر: {row.get('Price')} | الوصف: {row.get('Description')}"
                relevant_products.append(product_info)
        return "\n".join(relevant_products) if relevant_products else "لا يوجد منتج مطابق حالياً."
    except:
        return "عذراً، هناك مشكلة في الوصول لقاعدة البيانات."

# 4. نقاط الاتصال
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
            "أنت 'RoyalMind'، خبير التجميل والعطور لعلامة Royal Elchim بالأقصر. "
            "اربط بين الجمال، العطر، الحالة النفسية، والأبراج. "
            "كن راقياً، ملهماً، ومقنعاً. "
            f"بيانات المنتجات الحالية: {context}"
        )
        
        content = [system_prompt, query.text]
        if query.image:
            image_data = base64.b64decode(query.image.split(",")[1])
            img = Image.open(io.BytesIO(image_data))
            content.append(img)

        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
