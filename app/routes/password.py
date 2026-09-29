from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.password import PasswordEntry
from app.models.user import User
from app.schemas.password import PasswordCreate, PasswordOut
from app.security import get_current_user

router = APIRouter(prefix="/passwords", tags=["passwords"])


def get_user_passwords(user_id: int, db: Session):
    """Helper to get only current user's passwords"""
    return db.query(PasswordEntry).filter(PasswordEntry.user_id == user_id).all()


# 🔹 Pobierz wszystkie hasła użytkownika (opaque ciphertext)
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
            password=it.password
        )
        for it in items
    ]


# 🔹 Dodaj nowe hasło (ciphertext gotowy z przeglądarki)
@router.post("", response_model=PasswordOut)
def add_password(
    password: PasswordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_entry = PasswordEntry(
        user_id=current_user.id,
        service=password.service,
        login=password.login,
        password=password.password
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


# 🔹 Edytuj hasło (ciphertext gotowy z przeglądarki)
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
    item.password = updated.password

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
