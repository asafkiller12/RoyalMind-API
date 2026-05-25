
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import google.generativeai as genai
import pandas as pd

import os
import io
import base64
import logging

from functools import lru_cache
from PIL import Image

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("RoyalMind")

# =========================================================
# GEMINI CONFIG
# =========================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY environment variable is missing"
    )

genai.configure(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-1.5-flash"

model = genai.GenerativeModel(MODEL_NAME)

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="RoyalMind Enterprise API",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# REQUEST MODEL
# =========================================================

class Query(BaseModel):
    text: str
    image: Optional[str] = None
    user_id: str = "guest"

# =========================================================
# CLOUD DATA SOURCES
# =========================================================

DATA_SOURCES = {
    "products":
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTo0x3S-adDNu2AukMjxcsRM_MRwh8lC3wqJmyjfm4k9skssdYA-pyb-YaksEvu53d444qPu5JgaHrb/pub?output=csv",

    "inventory":
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTbpoHzQ3v55MnMHR7KyoYY4EmG4dNKNMr8q4MUA0KobTX3mLoYmZuQvJgio3kA8xGQ_pXoUt6nTmvl/pub?output=csv"
}

# =========================================================
# BRAND KNOWLEDGE
# =========================================================

BRAND_SIGNATURES = {
    "Royal Black":
        "شرقي خشبي فاخر. أكوا دي جيو، روز فانيلا، عنبر، قنب، عود أصفهان.",

    "Royal Shine":
        "فاكهي زهري فانيليا. أنوثة شبابية مبهجة.",

    "Royal Shadow":
        "غامق دخاني خشبي. سوفاج + بلاك أفغانو + سيجار.",

    "Royal Horizon":
        "صيفي منعش. سوفاج وأكوا دي جيو.",

    "Royal Rose Noir":
        "وردي عودي فانيليا للمناسبات الراقية.",

    "Royal Glow":
        "زهري فاكهي دافئ بلمسة عود.",

    "Royal Luna":
        "أنوثة ناعمة غامضة.",

    "Royal Base No.7":
        "قاعدة أنثوية راقية بمسك وعنبر وفانتزي.",

    "Royal Elchim Accord":
        "القنب + العنبر الأبيض + الياسمين + سوفاج."
}

BRAND_LOGIC = {
    "صباحي":
        "عطور حمضية وزهور خفيفة تمنح النشاط.",

    "مسائي":
        "عطور عنبر وأخشاب ومسك لهيبة أعمق.",

    "برج":
        "العطر مرتبط بطاقة الأبراج والجاذبية.",

    "حالة نفسية":
        "العطر يعكس المزاج والطاقة.",

    "نيش":
        "قطع فنية نادرة وفاخرة.",

    "زيوت":
        "إمكانية التحكم في نسب التركيز والثبات."
}

# =========================================================
# CACHE GOOGLE SHEETS
# =========================================================

@lru_cache(maxsize=10)
def load_sheet(url: str):

    try:

        df = pd.read_csv(url).fillna("")

        logger.info(f"Loaded sheet: {url}")

        return df

    except Exception as e:

        logger.error(f"Sheet loading failed: {e}")

        return pd.DataFrame()

# =========================================================
# BRAND SEARCH
# =========================================================

def search_brand_knowledge(query: str):

    results = []

    query_lower = query.lower()

    for name, desc in BRAND_SIGNATURES.items():

        if (
            name.lower() in query_lower
            or any(
                word.lower() in query_lower
                for word in desc.split()
            )
        ):

            results.append(f"{name}: {desc}")

    for key, value in BRAND_LOGIC.items():

        if key.lower() in query_lower:

            results.append(f"{key}: {value}")

    return results

# =========================================================
# GOOGLE SHEETS SEARCH
# =========================================================

def search_cloud_data(query: str):

    matches = []

    query_words = query.lower().split()

    for source_name, url in DATA_SOURCES.items():

        df = load_sheet(url)

        if df.empty:
            continue

        for _, row in df.iterrows():

            row_text = " ".join(
                map(str, row.values)
            )

            row_lower = row_text.lower()

            if any(
                word in row_lower
                for word in query_words
            ):

                matches.append(
                    f"[{source_name}] {row_text}"
                )

        matches = matches[:5]

    return matches

# =========================================================
# CONTEXT BUILDER
# =========================================================

def build_context(query: str):

    context_parts = []

    context_parts.extend(
        search_brand_knowledge(query)
    )

    context_parts.extend(
        search_cloud_data(query)
    )

    return "\n".join(context_parts)

# =========================================================
# IMAGE PROCESSOR
# =========================================================

def process_image(image_base64: Optional[str]):

    try:

        if not image_base64:
            return None

        if image_base64 == "string":
            return None

        if len(image_base64) < 100:
            return None

        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]

        image_data = base64.b64decode(
            image_base64,
            validate=True
        )

        image = Image.open(
            io.BytesIO(image_data)
        )

        image.verify()

        image = Image.open(
            io.BytesIO(image_data)
        )

        return image

    except Exception as e:

        logger.error(f"Invalid image: {e}")

        return None

# =========================================================
# PROMPT ENGINE
# =========================================================

def build_system_prompt(context: str):

    return f"""
أنت RoyalMind.

مستشار فاخر متخصص في:
- العطور النيش
- الجمال
- الطاقة النفسية
- الفخامة الراقية

قواعدك:

1. اربط العطر بالحالة النفسية.
2. اربط العطر بتوقيت اليوم.
3. وضّح الفوحان والثبات.
4. تحدث بأسلوب راقٍ ومقنع.
5. إذا وُجدت صورة:
   - حلل الملامح والبشرة
   - اقترح عطر وميكب مناسب
6. لا تعطِ إجابات سطحية.
7. كن احترافياً ومفصلاً.

المرجع المعرفي:
{context}
"""

# =========================================================
# ROOT ROUTE
# =========================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "api": "RoyalMind Enterprise",
        "model": MODEL_NAME
    }

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }

# =========================================================
# CHAT ENDPOINT
# =========================================================

@app.post("/chat")
async def chat(query: Query):

    try:

        logger.info(
            f"New request from user: {query.user_id}"
        )

        context = build_context(query.text)

        system_prompt = build_system_prompt(
            context
        )

        content = [
            system_prompt,
            query.text
        ]

        image = process_image(query.image)

        if image:
            content.append(image)

        response = model.generate_content(
            content
        )

        answer = response.text.strip()

        return {
            "status": "success",
            "answer": answer,
            "model": MODEL_NAME
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.exception(
            "Chat endpoint failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================================================
# STARTUP LOG
# =========================================================

logger.info("RoyalMind API Started")
