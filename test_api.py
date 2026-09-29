#!/usr/bin/env python3
"""
Test API przez faktyczne wywołania HTTP (stdlib urllib, zero zależności).
Symuluje pełny flow: rejestracja -> weryfikacja -> logowanie (cookie) ->
sól sejfu -> dodanie/lista/usunięcie hasła (opaque ciphertext, bez klucza).

Wymaga uruchomionego backendu na http://localhost:8000
(python -m uvicorn app.main:app --reload --reload-dir app, z korzenia repo).
"""

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request

# Windows console bywa w cp1250/cp1252 - bez tego emoji w printach wywalają się z UnicodeEncodeError
sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal
from app.models.user import User

API_URL = "http://localhost:8000"

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def request(method, path, json_body=None):
    data = json.dumps(json_body).encode() if json_body is not None else None
    req = urllib.request.Request(f"{API_URL}{path}", data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req) as resp:
            body = resp.read().decode()
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, (json.loads(body) if body else {})


def get_verification_code(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user.email_verification_code if user else None
    finally:
        db.close()


print("=" * 60)
print("TEST API - pełny flow (rejestracja -> sejf -> hasła)")
print("=" * 60)

test_email = f"test_{os.urandom(4).hex()}@example.com"
test_password = "Test123!ab"

print("\n1. Rejestracja użytkownika...")
status, body = request("POST", "/auth/register", {"email": test_email, "password": test_password})
assert status == 200, f"Rejestracja nieudana: {status} {body}"
print(f"   ✅ Zarejestrowano: {test_email}")

print("\n2. Weryfikacja email...")
code = get_verification_code(test_email)
assert code, "Brak kodu weryfikacyjnego w bazie"
status, body = request("POST", "/auth/verify-email", {"email": test_email, "code": code})
assert status == 200, f"Weryfikacja nieudana: {status} {body}"
print(f"   ✅ Email zweryfikowany (kod: {code})")

print("\n3. Logowanie...")
status, body = request("POST", "/auth/login", {"email": test_email, "password": test_password})
assert status == 200, f"Logowanie nieudane: {status} {body}"
print("   ✅ Zalogowano (cookie ustawione)")

print("\n4. Pobranie soli sejfu...")
status, body = request("GET", "/vault/salt")
assert status == 200 and "salt" in body, f"Brak soli: {status} {body}"
print(f"   ✅ Sól: {body['salt']} (is_new={body['is_new']})")

print("\n5. Dodanie hasła (opaque ciphertext, bez pola key)...")
fake_ciphertext = "dGVzdG93eS1jaXBoZXJ0ZXh0LW9wYXF1ZQ=="  # nie prawdziwe AES-GCM, tylko sprawdzenie kontraktu API
status, body = request("POST", "/passwords", {
    "service": "TestService",
    "login": "testuser",
    "password": fake_ciphertext,
})
assert status == 200, f"Dodanie hasła nieudane: {status} {body}"
password_id = body["id"]
assert body["password"] == fake_ciphertext, "Serwer nie powinien modyfikować ciphertextu"
print(f"   ✅ Dodano hasło, ID: {password_id}")

print("\n6. Lista haseł...")
status, body = request("GET", "/passwords")
assert status == 200 and any(p["id"] == password_id for p in body), f"Hasło nie widoczne na liście: {status} {body}"
print(f"   ✅ Hasło widoczne na liście ({len(body)} pozycji)")

print("\n7. Sprawdzenie że /passwords/decrypt nie istnieje (usunięty w Kroku 4)...")
status, _ = request("POST", "/passwords/decrypt", {"key": "x", "password": "y"})
assert status in (404, 405), f"Endpoint /passwords/decrypt wciąż odpowiada: {status}"
print(f"   ✅ Endpoint nie istnieje (status {status})")

print("\n8. Usunięcie hasła...")
status, body = request("DELETE", f"/passwords/{password_id}")
assert status == 200, f"Usunięcie nieudane: {status} {body}"
print("   ✅ Hasło usunięte")

print("\n" + "=" * 60)
print("TEST ZAKOŃCZONY POMYŚLNIE!")
print("=" * 60)
