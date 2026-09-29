from sqlalchemy.orm import Session
from database import SessionLocal
from models.password import PasswordEntry
from security import encrypt_text, decrypt_text

db: Session = SessionLocal()
rows = db.query(PasswordEntry).all()

for r in rows:
    # sprawdź, czy już zaszyfrowane (Fernet token kończy się zwykle '=' i ma kropki/+/)
    try:
        # jeśli to już ciphertext, decrypt przejdzie bez wyjątku – więc pomiń
        decrypt_text(r.password)
        continue
    except Exception:
        pass

    # jeśli tu doszliśmy – najpewniej plaintext: zaszyfruj
    r.password = encrypt_text(r.password)
    db.add(r)

db.commit()
db.close()
print("Migracja zakończona")
