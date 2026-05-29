# 1. التراجع التكتيكي إلى بايثون 3.11 (الإصدار الذهبي لمكتبات الذكاء الاصطناعي)
FROM python:3.11-slim

# 2. حقن نظام التشغيل بالمكتبات البصرية بالقوة (حل مشكلة libGL للأبد)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. تحديد مسار العمل
WORKDIR /app

# 4. نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. نسخ باقي ملفات المشروع
COPY . .

# 6. أمر التشغيل
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
