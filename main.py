from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import pandas as pd
import base64
import io
from PIL import Image

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash')
app = FastAPI()

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

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTo0x3S-adDNu2AukMjxcsRM_MRwh8lC3wqJmyjfm4k9skssdYA-pyb-YaksEvu53d444qPu5JgaHrb/pub?output=csv"

def get_total_context(query):
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        relevant_products = []
        for _, row in df.iterrows():
            search_text = f"{row.get('Product','')} {row.get('Category','')} {row.get('Mood','')} {row.get('Zodiac','')}"
            if any(word in query for word in search_text.split()):
                relevant_products.append(f"المنتج: {row.get('Product')} | السعر: {row.get('Price')} | الوصف: {row.get('Description')}")
        return "\n".join(relevant_products) if relevant_products else "لا يوجد منتج مطابق."
    except:
        return "قاعدة البيانات غير متاحة."

@app.get("/")
def read_root():
    return {"status": "Online"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key missing")
        
        context = get_total_context(query.text)
        system_prompt = (
            "أنت 'RoyalMind'، خبير التجميل والعطور لعلامة Royal Elchim بالأقصر. "
            "اربط بين الجمال، العطر، الحالة النفسية، والأبراج. "
            "كن راقياً، ملهماً، ومقنعاً. "
            f"بيانات المنتجات الحالية: {context}"
        )

        content = [system_prompt, query.text]
        if query.image and "," in query.image:
            image_data = base64.b64decode(query.image.split(",")[1])
            content.append(Image.open(io.BytesIO(image_data)))

        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
