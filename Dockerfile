FROM python:3.11-slim

# Install system dependencies: Tesseract OCR and Poppler for pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CG_COOKIE_SECURE=1 \
    CG_COOKIE_SAMESITE=lax

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

# Create upload directory for file storage
RUN mkdir -p /data/uploads

EXPOSE 8000

# Use Gunicorn with Uvicorn workers for production
CMD ["bash", "-lc", "exec gunicorn -k uvicorn.workers.UvicornWorker --timeout 120 -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-8000} app.main:app"]


