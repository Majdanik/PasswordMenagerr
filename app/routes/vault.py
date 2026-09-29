import secrets
import base64
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.security import get_current_user

router = APIRouter(prefix="/vault", tags=["vault"])


@router.get("/salt")
def get_salt(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return this user's KDF salt, generating it on first call. Not secret - only PIN + Fernet key are."""
    is_new = not current_user.kdf_salt
    if is_new:
        current_user.kdf_salt = base64.b64encode(secrets.token_bytes(16)).decode()
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

    return {"salt": current_user.kdf_salt, "is_new": is_new}
