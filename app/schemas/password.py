from pydantic import BaseModel

class PasswordCreate(BaseModel):
    service: str
    login: str
    password: str  # opaque ciphertext (base64 IV+AES-GCM) z przeglądarki

class PasswordOut(BaseModel):
    id: int
    service: str
    login: str
    password: str  # opaque ciphertext - odszyfrowanie dzieje się w przeglądarce

    model_config = {"from_attributes": True}
