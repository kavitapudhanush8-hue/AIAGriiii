"""
Database configuration and session management.

Uses SQLite for lightweight, zero-dependency data management (< 10 MB).
The database file is created automatically in the backend directory.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# SQLite database — lightweight, no server required
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DB_PATH = os.path.abspath(os.path.join(DB_DIR, "agri_assistant.db"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
