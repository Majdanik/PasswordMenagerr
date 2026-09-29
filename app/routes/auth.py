import secrets
from datetime import timedelta, datetime
import os
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserOut,
    EmailVerifyRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
)
from app.email_utils import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _generate_code() -> str:
    """Generate a 6-digit numeric one-time code."""
    return f"{secrets.randbelow(1_000_000):06d}"


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (unverified until email is confirmed)
    hashed_password = hash_password(user.password)
    code = _generate_code()
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        email_verified=False,
        email_verification_code=code,
        email_verification_expires=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_verification_email(new_user.email, code)

    return new_user


@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login user and set JWT token in HttpOnly cookie"""
    # Find user
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not db_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    is_secure_cookie = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure_cookie,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"message": "Login successful"}


@router.post("/logout")
def logout(response: Response):
    """Logout user by clearing auth cookie"""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.post("/verify-email")
def verify_email(payload: EmailVerifyRequest, db: Session = Depends(get_db)):
    """Confirm a user's email using the code sent at registration/resend"""
    db_user = db.query(User).filter(User.email == payload.email).first()

    invalid = (
        not db_user
        or not db_user.email_verification_code
        or db_user.email_verification_code != payload.code
        or db_user.email_verification_expires is None
        or db_user.email_verification_expires < datetime.utcnow()
    )
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )

    db_user.email_verified = True
    db_user.email_verification_code = None
    db_user.email_verification_expires = None
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Issue a fresh verification code, invalidating any previous one"""
    db_user = db.query(User).filter(User.email == payload.email).first()

    if db_user and not db_user.email_verified:
        code = _generate_code()
        db_user.email_verification_code = code
        db_user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        db.commit()
        send_verification_email(db_user.email, code)

    return {"message": "If the account exists and is not verified, a new verification code has been sent"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Issue a password reset code; response is identical whether or not the email exists"""
    db_user = db.query(User).filter(User.email == payload.email).first()

    if db_user:
        code = _generate_code()
        db_user.password_reset_code = code
        db_user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        send_password_reset_email(db_user.email, code)

    return {"message": "If an account with that email exists, a password reset code has been sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Set a new password using the code issued by /forgot-password"""
    db_user = db.query(User).filter(User.email == payload.email).first()

    invalid = (
        not db_user
        or not db_user.password_reset_code
        or db_user.password_reset_code != payload.code
        or db_user.password_reset_expires is None
        or db_user.password_reset_expires < datetime.utcnow()
    )
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )

    db_user.hashed_password = hash_password(payload.new_password)
    db_user.password_reset_code = None
    db_user.password_reset_expires = None
    db.commit()

    return {"message": "Password reset successfully"}
