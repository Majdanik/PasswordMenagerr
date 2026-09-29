from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from database import get_db
from models.password import PasswordEntry
from models.user import User
from schemas.password import PasswordCreate, PasswordOut
from security import encrypt_text, decrypt_text, get_current_user
from cryptography.fernet import Fernet, InvalidToken

router = APIRouter(prefix="/passwords", tags=["passwords"])


def get_user_passwords(user_id: int, db: Session):
    """Helper to get only current user's passwords"""
    return db.query(PasswordEntry).filter(PasswordEntry.user_id == user_id).all()


# 🔹 Pobierz wszystkie hasła użytkownika (domyślnie zaszyfrowane)
@router.get("", response_model=list[PasswordOut])
def get_passwords(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = get_user_passwords(current_user.id, db)
    return [
        PasswordOut(
            id=it.id,
            service=it.service,
            login=it.login,
            password=it.password  # zwracamy ZASZYFROWANE
        )
        for it in items
    ]


# 🔹 Dodaj nowe hasło
@router.post("", response_model=PasswordOut)
def add_password(
    password: PasswordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    encrypted_password = encrypt_text(password.password)
    new_entry = PasswordEntry(
        user_id=current_user.id,
        service=password.service,
        login=password.login,
        password=encrypted_password
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return PasswordOut(
        id=new_entry.id,
        service=new_entry.service,
        login=new_entry.login,
        password=new_entry.password
    )


# 🔹 Edytuj hasło
@router.put("/{password_id}", response_model=PasswordOut)
def update_password(
    password_id: int,
    updated: PasswordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(PasswordEntry).filter(
        PasswordEntry.id == password_id,
        PasswordEntry.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Hasło nie istnieje")

    item.service = updated.service
    item.login = updated.login
    item.password = encrypt_text(updated.password)

    db.commit()
    db.refresh(item)

    return PasswordOut(
        id=item.id,
        service=item.service,
        login=item.login,
        password=item.password
    )


# 🔹 Usuń hasło
@router.delete("/{password_id}")
def delete_password(
    password_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(PasswordEntry).filter(
        PasswordEntry.id == password_id,
        PasswordEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Hasło nie znalezione")
    
    db.delete(entry)
    db.commit()
    return {"message": "Password deleted"}


# 🔹 Odszyfruj hasło (na podstawie klucza)
@router.post("/decrypt", response_model=dict)
def decrypt_via_key(
    current_user: User = Depends(get_current_user),
    payload: dict = Body(...)
):
    key = (payload.get("key") or "").strip()
    encrypted = (payload.get("password") or "").strip()
    
    if not key or not encrypted:
        raise HTTPException(status_code=400, detail="Brak klucza lub hasła")

    # walidacja formatu klucza
    try:
        f = Fernet(key.encode())
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Zły format klucza (musi być 32B base64, 44 znaki, zwykle kończy się '=')"
        )

    # próba odszyfrowania
    try:
        plain = f.decrypt(encrypted.encode()).decode()
        return {"decrypted": plain}
    except InvalidToken:
        raise HTTPException(status_code=400, detail="Klucz nie pasuje do tego zaszyfrowanego hasła")
    except Exception:
        raise HTTPException(status_code=400, detail="Niepowodzenie odszyfrowania")
