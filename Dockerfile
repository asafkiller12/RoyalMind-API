# 1. استخدام الإصدار الذهبي من بايثون للذكاء الاصطناعي
FROM python:3.11-slim

# 2. حقن نظام التشغيل بالثالوث البصري الكامل (تم إضافة libegl1)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgles2 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# 3. تحديد مسار العمل داخل الخادم
WORKDIR /app

# 4. نسخ ملف المتطلبات وتثبيتها بشكل نظيف
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. نسخ باقي ملفات الجسد البرمجي
COPY . .

# 6. أمر التشغيل بالصيغة القياسية
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
