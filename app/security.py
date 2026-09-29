# app/security.py
import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db

load_dotenv()

# ========== FERNET (szyfrowanie haseł użytkowników) ==========
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError("Brak FERNET_KEY w .env")

FERNET_KEY = FERNET_KEY.strip()
if FERNET_KEY.startswith("b'") and FERNET_KEY.endswith("'"):
    FERNET_KEY = FERNET_KEY[2:-1]

try:
    _fernet = Fernet(FERNET_KEY.encode())
except Exception as e:
    raise RuntimeError(
        "FERNET_KEY ma zły format. Klucz musi być 32 bajty zakodowane base64 (44 znaki, zwykle kończy się '=')."
    ) from e

def encrypt_text(plain: str) -> str:
    return _fernet.encrypt(plain.encode()).decode()

def decrypt_text(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()

# ========== JWT (autentykacja użytkowników) ==========
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Verify JWT token and return current user"""
    from models.user import User
    
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credential_exception
    except jwt.InvalidTokenError:
        raise credential_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credential_exception
    return user

    return _fernet.decrypt(token.encode()).decode()
