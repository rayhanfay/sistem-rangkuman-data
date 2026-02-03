import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Konfigurasi JWT
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# Konfigurasi Google & Gemini
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID")

# Google Custom Search API
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID")

# Database PostgreSQL
DB_USER: str = os.getenv("DB_USER")
DB_PASS: str = os.getenv("DB_PASS")
DB_HOST: str = os.getenv("DB_HOST")
DB_PORT: str = os.getenv("DB_PORT")
DB_NAME: str = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME, JWT_SECRET_KEY, GEMINI_API_KEY]):
    raise KeyError("Satu atau lebih variabel environment penting tidak ditemukan. Pastikan .env sudah benar.")

DATABASE_URL: str = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"