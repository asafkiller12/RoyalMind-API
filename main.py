from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from google import genai
from google.genai import types

from PIL import Image

import pandas as pd

import os
import io
import base64
import logging

from cachetools import TTLCache

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("RoyalMind")

# =========================================================
# GEMINI CLIENT
# =========================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is missing"
    )

client = genai.Client(
    api_key=GOOGLE_API_KEY
)

MODEL_NAME = "gemini-2.5-flash"

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="RoyalMind Enterprise",
    version="5.0"
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
# DATA SOURCES
# =========================================================

DATA_SOURCES = {
    "products":
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTo0x3S-adDNu2AukMjxcsRM_MRwh8lC3wqJmyjfm4k9skssdYA-pyb-YaksEvu53d444qPu5JgaHrb/pub?output=csv",

    "inventory":
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTbpoHzQ3v55MnMHR7KyoYY4EmG4dNKNMr8q4MUA0KobTX3mLoYmZuQvJgio3kA8xGQ_pXoUt6nTmvl/pub?output=csv"
}

# =========================================================
# CACHE
# =========================================================

sheet_cache = TTLCache(
    maxsize=10,
    ttl=300
)

# =========================================================
# BRAND KNOWLEDGE
# =========================================================

BRAND_SIGNATURES = {
    "Royal Black":
        "شرقي خشبي فاخر بعنبر وعود وقنب.",

    "Royal Shadow":
        "دخاني غامق وهيبة ليلية.",

    "Royal Luna":
        "أنوثة ناعمة وغموض قمري.",

    "Royal Horizon":
        "انتعاش صيفي فاخر."
}

# =========================================================
# LOAD SHEET
# =========================================================

def load_sheet(url: str):

    if url in sheet_cache:
        return sheet_cache[url]

    try:

        df = pd.read_csv(url).fillna("")

        sheet_cache[url] = df

        logger.info(f"Loaded sheet: {url}")

        return df

    except Exception as e:

        logger.error(f"Sheet Error: {e}")

        return pd.DataFrame()

# =========================================================
# CONTEXT ENGINE
# =========================================================

def build_context(query: str):

    results = []

    query_lower = query.lower()

    # brand knowledge
    for name, desc in BRAND_SIGNATURES.items():

        if (
            name.lower() in query_lower
            or any(
                word.lower() in query_lower
                for word in desc.split()
            )
        ):

            results.append(
                f"{name}: {desc}"
            )

    # sheets
    for source_name, url in DATA_SOURCES.items():

        df = load_sheet(url)

        if df.empty:
            continue

        for _, row in df.iterrows():

            row_text = " ".join(
                map(str, row.values)
            )

            if any(
                word.lower() in row_text.lower()
                for word in query.split()
            ):

                results.append(
                    f"[{source_name}] {row_text}"
                )

    return "\n".join(results[:10])

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

        image_bytes = base64.b64decode(
            image_base64
        )

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        return image

    except Exception as e:

        logger.error(f"Image Error: {e}")

        return None

# =========================================================
# SYSTEM PROMPT
# =========================================================

def build_prompt(context: str):

    return f"""
أنت RoyalMind.

مستشار فاخر متخصص في:
- العطور النيش
- تحليل الشخصية
- الجمال والطاقة
- الفخامة الراقية

قواعدك:

- اربط العطر بالحالة النفسية
- اربط العطر بتوقيت اليوم
- اشرح الثبات والفوحان
- تحدث بأسلوب فاخر ومقنع
- لا تكن سطحياً

المرجع:
{context}
"""

# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():

    return {
        "status": "online",
        "model": MODEL_NAME,
        "api": "RoyalMind Enterprise"
    }

# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
async def chat(query: Query):

    try:

        logger.info(
            f"Request From: {query.user_id}"
        )

        context = build_context(
            query.text
        )

        system_prompt = build_prompt(
            context
        )

        parts = [
            system_prompt,
            query.text
        ]

        image = process_image(
            query.image
        )

        if image:

            parts.append(image)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=parts,
            config=types.GenerateContentConfig(
                temperature=0.9,
                top_p=0.95,
                max_output_tokens=2048
            )
        )

        return {
            "status": "success",
            "answer": response.text,
            "model": MODEL_NAME
        }

    except Exception as e:

        logger.exception("Chat Failed")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================================================
# STARTUP
# =========================================================

logger.info(
    f"RoyalMind Started | Model: {MODEL_NAME}"
)
