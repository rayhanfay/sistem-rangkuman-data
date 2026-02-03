from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, func
from app.infrastructure.database.database import Base
from app.domain.entities.user import UserRole

class User(Base):
    """Model ORM SQLAlchemy untuk tabel 'users'."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False, default=UserRole.user.value)
    created_at = Column(DateTime(timezone=True), default=func.now())

class History(Base):
    """Model ORM SQLAlchemy untuk tabel 'history'."""
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    summary = Column(Text)
    timestamp = Column(String, unique=True)
    upload_date = Column(DateTime(timezone=True), default=func.now())
    cycle_assets = Column(JSON, nullable=True)
    user_email = Column(String, nullable=True)
    sheet_name = Column(String, nullable=True) 

class File(Base):
    """Model ORM SQLAlchemy untuk tabel 'files'."""
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_type = Column(String)
    json_content = Column(Text, nullable=True)
    upload_date = Column(DateTime(timezone=True), default=func.now())