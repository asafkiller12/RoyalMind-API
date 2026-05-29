# 1. استخدام بيئة بايثون رسمية وخفيفة
FROM python:3.12-slim

# 2. حقن نظام التشغيل بالمكتبات البصرية بالقوة (هذا هو الحل الجذري لـ libGL)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. تحديد مسار العمل داخل الخادم
WORKDIR /app

# 4. نسخ ملف المتطلبات وتثبيتها بشكل نظيف بدون ذاكرة مؤقتة
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. نسخ باقي ملفات المشروع (مثل main.py)
COPY . .

# 6. أمر التشغيل الخاص بمنصة Railway وتمرير منفذ الاتصال
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
