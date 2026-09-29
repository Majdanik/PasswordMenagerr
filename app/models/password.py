from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base


class PasswordEntry(Base):
    __tablename__ = "passwords"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    service = Column(String, index=True)
    login = Column(String)
    password = Column(String)
