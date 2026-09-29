import re
from pydantic import BaseModel, EmailStr, field_validator


def _validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Hasło musi mieć minimum 8 znaków")
    if not re.search(r"[a-z]", password):
        raise ValueError("Hasło musi zawierać małą literę")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Hasło musi zawierać wielką literę")
    if not re.search(r"[0-9]", password):
        raise ValueError("Hasło musi zawierać cyfrę")
    if not re.search(r"[^a-zA-Z0-9]", password):
        raise ValueError("Hasło musi zawierać znak specjalny")
    return password


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _validate_password_strength(value)
