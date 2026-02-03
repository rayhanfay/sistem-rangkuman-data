from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency function untuk FastAPI yang menyediakan sesi database per request.
    Ini memastikan sesi ditutup dengan benar setelah request selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()