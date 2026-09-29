from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    email_verified = Column(Boolean, default=False, nullable=False, server_default="0")
    email_verification_code = Column(String, nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)
    password_reset_code = Column(String, nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    kdf_salt = Column(String, nullable=True)
