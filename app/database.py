import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite dla Replit (domyślnie) lub PostgreSQL jeśli dostępny
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./passwords.db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 🔑 Funkcja get_db - tego Ci brakuje!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
