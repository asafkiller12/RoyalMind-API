from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import google.generativeai as genai
import os
import pandas as pd
import base64
import io
from PIL import Image

# 1. الإعدادات الأساسية
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash')
app = FastAPI(title="Royal Elchim Unified Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# رابط جدول جوجل CSV
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTo0x3S-adDNu2AukMjxcsRM_MRwh8lC3wqJmyjfm4k9skssdYA-pyb-YaksEvu53d444qPu5JgaHrb/pub?output=csv"

# 2. نماذج البيانات
class ChatQuery(BaseModel):
    text: str
    image: Optional[str] = None
    user_id: str = "guest"

class AnalyzeQuery(BaseModel):
    mood: str
    image: Optional[str] = None
    user_id: str = "guest"

# 3. محرك الذاكرة والمعرفة
def get_total_context(query: str):
    # أ. الموسوعة الثابتة (الفلسفة والتركيبات)
    brand_knowledge = {
        "Royal Black": "شرقي-خشبي فاخر. افتتاحية أكوا دي جيو، قلب من روز فانيلا وعنبر وقنب، قاعدة عود أصفهان. يمثل القوة والغموض.",
        "Royal Shine": "فاكهي-زهري-فانيليا. افتتاحية Fantasy، قلب ياسمين، قاعدة عنبر وفانيليا. يمثل الفرح والأنوثة الشبابية.",
        "Royal Shadow": "غامق-دخاني-خشبي. يمزج بين Black Afgano وسوفاج والسيجار. ملك الليل، للرجال فقط، عمق وهيبة.",
        "Royal Horizon": "صيفي منعش. سوفاج وأكوا دي جيو مع لمسات La Vie Est Belle. يمثل الحرية والتجدد.",
        "Royal Rose Noir": "وردي-عودي-فانيليا. روز فانيلا وياسمين مع قاعدة عود وعنبر. أنثوي فاخر للمناسبات الرفيعة.",
        "Royal Glow": "زهري-فاكهي-دافئ. La Vie Est Belle وFantasy مع لمسة عود. وهج أنثوي ناعم.",
        "Royal Luna": "أنوثة القمر. روز فانيلا، بكرات روج، وأكوا دي جيو. نعومة تخفي غموضاً، مكمل لـ Royal Eclipse.",
        "بصمة البراند": "Royal Elchim Accord: مزيج من القنب، عنبر وايت، ياسمين، ودور سوفاج."
    }
    
    context = ""
    for name, desc in brand_knowledge.items():
        if name.lower() in query.lower() or any(word in query for word in desc.split()):
            context += f"\n- {name}: {desc}"
            
    # ب. البيانات الديناميكية (من جوجل شيت)
    try:
        df = pd.read_csv(SHEET_CSV_URL).fillna("")
        relevant = []
        for _, row in df.iterrows():
            search_text = f"{row.get('Product','')} {row.get('Category','')} {row.get('Mood','')} {row.get('Zodiac','')}"
            if any(word in query for word in search_text.split()):
                relevant.append(f"المنتج: {row.get('Product')} | السعر: {row.get('Price')} | الوصف: {row.get('Description')}")
        if relevant: context += "\n\nالمنتجات المتاحة: \n" + "\n".join(relevant)
    except: pass
    
    return context

# 4. نقاط الاتصال (API Endpoints)

@app.get("/")
async def root():
    return {"status": "Online", "message": "Royal Elchim Hub is Active!"}

# endpoint 1: الدردشة التفاعلية (Chat)
@app.post("/chat")
async def chat_endpoint(query: ChatQuery):
    try:
        context = get_total_context(query.text)
        system_prompt = (
            "أنت 'RoyalMind'، المستشار الشامل للفخامة في Royal Elchim بالأقصر. "
            "اربط بين الجمال، العطر، الحالة النفسية، والأبراج. "
            "كن راقياً، ملهماً، ومقنعاً جداً. "
            f"المرجع المعرفي: {context}"
        )
        content = [system_prompt, query.text]
        if query.image and "," in query.image:
            img = Image.open(io.BytesIO(base64.b64decode(query.image.split(",")[1])))
            content.append(img)
        
        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# endpoint 2: التحليل العميق والترشيح (Analyze)
@app.post("/api/analyze")
async def analyze_endpoint(data: AnalyzeQuery):
    try:
        context = get_total_// context(data.mood) # تصحيح: get_total_context(data.mood)
        # سأعيد كتابة السطر بشكل صحيح في النسخة النهائية
        
        system_prompt = (
            f"أنت RoyalMind. حلل حالة الوعي التالية: '{data.mood}'. "
            f"بناءً على هذا المود والبيانات المتاحة: {context}, "
            "حدد التصنيف الأنسب (برفانات، مكياج، عناية) وقدم تحليلاً فلسفياً راقياً. "
            "يجب أن يكون الرد بصيغة JSON: {'category': '...', 'analysis': '...'}"
        )
        
        content = [system_prompt]
        if data.image and "," in data.image:
            img = Image.open(io.BytesIO(base64.b64decode(data.image.split(",")[1])))
            content.append(img)
            
        response = model.generate_content(content)
        ai_data = json.loads(response.text.replace('```json', '').replace('```', ''))
        
        # جلب منتجات من الجدول تطابق التصنيف المختار
        products_list = []
        try:
            df = pd.read_csv(SHEET_CSV_URL).fillna("")
            cat_col = 'Category' if 'Category' in df.columns else 'التصنيف الرئيسي'
            matched = df[df[cat_col].str.contains(ai_// data['category'], case=False, na=False)].head(3)
            # تصحيح: ai_data['category']
            for _, row in matched.iterrows():
                products_list.append({
                    "name": row.get('Product', row.get('اسم الصنف')),
                    "price": row.get('Price', row.get('قيمة سعر1')),
                    "description": row.get('Description', row.get('الوصف'))
                })
        except: pass
        
        return {
            "analysis": ai_data.get("analysis", "تحليل الوعي جاري..."),
            "category": ai_// data.get("category", "عام"),
            "products": products_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
