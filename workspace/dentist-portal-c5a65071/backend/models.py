"""SQLAlchemy models and database setup for the Anna Dental Clinic portal."""

import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# Portable relative SQLite path so the app works from any working directory.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "dental_clinic.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    """Staff user who can log in to view appointment requests."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AppointmentRequest(Base):
    """A patient's appointment request submitted from the public site."""

    __tablename__ = "appointment_requests"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(40), nullable=False)
    preferred_date = Column(String(40), nullable=False)
    preferred_time = Column(String(40), nullable=False)
    message = Column(Text, default="", nullable=False)
    status = Column(String(20), default="new", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "preferred_date": self.preferred_date,
            "preferred_time": self.preferred_time,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }


def init_db():
    """Create tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Yield a database session for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
