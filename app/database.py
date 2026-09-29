import os
from sqlalchemy import create_engine, text
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


def ensure_user_security_columns():
    """Lightweight migration for SQLite: ensure security-related users columns exist."""
    if "sqlite" not in DATABASE_URL:
        return

    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(users)")).fetchall()
        column_names = {column[1] for column in columns}

        if "email_verified" not in column_names:
            # DEFAULT 0 dotyczy nowych wierszy od teraz; istniejące konta
            # (sprzed weryfikacji email) grandfatherujemy poniżej na 1.
            connection.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
            connection.execute(text("UPDATE users SET email_verified = 1"))

        if "email_verification_code" not in column_names:
            connection.execute(text("ALTER TABLE users ADD COLUMN email_verification_code VARCHAR"))

        if "email_verification_expires" not in column_names:
            connection.execute(text("ALTER TABLE users ADD COLUMN email_verification_expires DATETIME"))

        if "password_reset_code" not in column_names:
            connection.execute(text("ALTER TABLE users ADD COLUMN password_reset_code VARCHAR"))

        if "password_reset_expires" not in column_names:
            connection.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires DATETIME"))

        if "kdf_salt" not in column_names:
            connection.execute(text("ALTER TABLE users ADD COLUMN kdf_salt VARCHAR"))

# 🔑 Funkcja get_db - tego Ci brakuje!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
