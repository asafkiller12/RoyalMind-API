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
app = FastAPI(title="RoyalMind Luxury Enterprise API")

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

# 3. الذاكرة العميقة لبراند Royal Elchim
def get_total_context(query: str):
    # قاعدة بيانات المنتجات والتركيبات (مستمدة من ملفاتك)
    perfume_library = {
        "Royal Black": "شرقي-خشبي فاخر. افتتاحية أكوا دي جيو، قلب من روز فانيلا وعنبر وقنب، قاعدة عود أصفهان. يمثل القوة والغموض.",
        "Royal Shine": "فاكهي-زهري-فانيليا. افتتاحية Fantasy، قلب ياسمين، قاعدة عنبر وفانيليا. يمثل الفرح والأنوثة الشبابية.",
        "Royal Shadow": "غامق-دخاني-خشبي. يمزج بين Black Afgano وسوفاج والسيجار. ملك الليل، للرجال فقط، عمق وهيبة.",
        "Royal Horizon": "صيفي منعش. سوفاج وأكوا دي جيو مع لمسات La Vie Est Belle. يمثل الحرية والتجدد.",
        "Royal Rose Noir": "وردي-عودي-فانيليا. روز فانيلا وياسمين مع قاعدة عود وعنبر. أنثوي فاخر للمناسبات الرفيعة.",
        "Royal Glow": "زهري-فاكهي-دافئ. La Vie Est Belle وFantasy مع لمسة عود. وهج أنثوي ناعم.",
        "Royal Luna": "أنوثة القمر. روز فانيليا، بكرات روج، وأكوا دي جيو. نعومة تخفي غموضاً، مكمل لـ Royal Eclipse.",
        "Royal Base No.7": "قاعدة أنثوية راقية: مسك أسود، عنبر وايت، أكوا دي جيو، لافيستا بيل وفانتزي.",
        "بصمة البراند": "Royal Elchim Accord: مزيج من القنب، عنبر وايت، ياسمين، ودور سوفاج. تعطي غموض وقوة ودفع.",
        "Superman": "تركيبة رجولية حارة خشبية (هوجو، سكلبشر، اوبن، مسك حنوط). اقتصادية وتناسب محبي العود."
    }
    
    # البحث عن المنتجات ذات الصلة بالطلب
    context = ""
    for name, desc in perfume_library.items():
        if name.lower() in query.lower() or any(word in query for word in desc.split()):
            context += f"\n- {name}: {desc}"
    
    # إضافة معلومات عامة عن البراند (الأقصر، النسب)
    context += "\n\nمعلومات عامة: العلامة تنطلق من الأقصر. التركيز القياسي: 25% زيت، 5% مثبت، 70% كحول."
    return context

# 4. نقاط الاتصال
@app.get("/")
def read_root():
    return {"status": "Online", "message": "RoyalMind Enterprise AI is Active!"}

@app.post("/chat")
async def chat_with_royalmind(query: Query):
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key missing")
        
       context = get_total_context(query.text) # تصحيح: get_total_context(query.text)
        # سأقوم بتصحيح السطر أدناه في النسخة النهائية
        
        system_prompt = (
            "أنت 'RoyalMind'، كبير مصممي العطور في Royal Elchim بالأقصر. "
            "أنت خبير في الكيمياء العطرية، الأبراج، والحالات النفسية. \n\n"
            "قواعدك المهنية:\n"
            "1. للعملاء: كن سفيراً للفخامة. صف العطور بلغة عاطفية (نور، ظل، غموض، إشراق). "
            "اربط العطر ببرج العميل أو حالته النفسية (مثلاً: الحزن يحتاج نوتات دافئة، التوتر يحتاج حمضيات).\n"
            "2. لصاحب العمل (معمار): كن تقنياً دقيقاً. تحدث عن نسب الزيوت، المثبتات، ونوع الكحول.\n"
            "3. التوصية الشاملة: إذا سأل العميل عن مظهر، اقترح له (عطر + ميكب) يكملان بعضهما.\n"
            f"مرجع المنتجات: {context}"
        )

        content = [system_prompt, query.text]
        if query.image:
            image_data = base64.b64decode(query.image.split(",")[1])
            content.append(Image.open(io.BytesIO(image_data)))

        response = model.generate_content(content)
        return {"status": "success", "answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


