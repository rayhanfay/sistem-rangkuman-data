# Gunakan image Python yang ringan
FROM python:3.11-slim

# Install library sistem yang dibutuhkan untuk psycopg2 dan enkripsi
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements dan install library
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code
COPY . .

# Expose port 8000 (sesuai uvicorn)
EXPOSE 8000

# Jalankan perintah startup
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]