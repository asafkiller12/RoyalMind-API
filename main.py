from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import pandas as pd
import base64
import io
from PIL import Image
from typing import Optional

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
    image: Optional[str] = None
    user_id: str = "guest"

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTo0x3S-adDNu2AukMjxcsRM_MRwh8lC3wqJmyjfm4k9skssdYA-pyb-YaksEvu53d444qPu5JgaHrb/pub?output=csv"

def get_total_context(query):
    brand_signatures = {
        "Royal Black": "شرقي-خشبي فاخر. افتتاحية أكوا دي جيو، قلب من روز فانيلا وعنبر وقنب، قاعدة عود أصفهان.",
        "Royal Shine": "فاكهي-زهري-فانيليا. افتتاحية Fantasy، قلب ياسمين، قاعدة عنبر وفانيليا.",
        "Royal Shadow": "غامق-دخاني-خشبي. يمزج بين Black Afgano وسوفاج والسيجار. ملك الليل.",
        "Royal Horizon": "صيفي منعش. سوفاج وأكوا دي جيو مع لمسات La Vie Est Belle.",
        "Royal Rose Noir": "وردي-عودي-فانيليا. روز فانيلا وياسمين مع قاعدة عود وعنبر.",
        "Royal Glow": "زهري-فاكهي-دافئ. La Vie Est Belle وFantasy مع لمسة عود.",
        "Royal Luna": "أنوثة القمر. روز فانيلا، بكرات روج، وأكوا دي جيو. مكمل لـ Royal Eclipse.",
        "بصمة البراند": "Royal Elchim Accord: مزيج من القنب، عنبر وايت، ياسمين، ودور سوفاج."
    }
    brand_logic = {
        "برج": "نحن نصمم عطوراً تتناغم مع طاقة الأبراج.",
        "حالة نفسية": "العطر علاج للنفس؛ نوفر نوتات للاسترخاء أو الطاقة.",
        "صباحي": "عطور صباحية منعشة.",
        "مسائي": "عطور مسائية عميقة.",
        "نيش": "مجموعة 'النيش' هي قطع فنية حصرية ونادرة.",
        "زيوت": "نوفر تركيبات مخصصة بنسب زيت ومثبت."
    }
    context = ""
    for name, desc in brand_// signatures.items(): # تصحيح: brand_signatures.items()
        if name.lower() in query.lower() or any(word in query for word in desc.split()):
            context += f"\n- {name}: {desc}"
    for key, val in brand_logic.items():
        if any(word in query for word in key.split()):
            context += f"\n- {key}: {val}"
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        relevant = []
        for _, row in df.iterrows():
            search_text = f"{row.get('Product','')} {row.get('Category','')} {row.get('Mood','')} {row.get('Zodiac','')}"
            if any(word in query for word in search_text.split()):
                relevant.append(f"المنتج: {row.get('Product')} | السعر: {row.get('Price')} | الوصف: {row.get('Description')}")
        if relevant: context += "\n\nالمنتجات المتاحة: \n" + "\n".join(relevant)
    except: pass
    return context

@app.get("/")
def read_root():
    return {"status": "Online"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY: raise HTTPException(status_code=500, detail="API Key missing")
        context = get_total_context(query.text)
        system_prompt = (
            "أنت 'RoyalMind'، المستشار الشامل للفخامة في Royal Elchim بالأقصر. "
            "اربط بين الجمال، العطر، الحالة النفسية، والأبراج. "
            "كن راقياً، ملهماً، ومقنعاً جداً. "
            f"المرجع المعرفي: {context}"
        )
        content = [system_prompt, query.text]
        if query.image and "," in query.image:
            image_data = base64.b64decode(query.image.split(",")[1])
            content.append(Image.open(io.BytesIO(image_data)))
        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

