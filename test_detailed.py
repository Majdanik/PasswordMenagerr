#!/usr/bin/env python3
"""
Szczegółowy test API - drukuje pełne odpowiedzi na każdym kroku (stdlib
urllib, zero zależności). Wymaga uruchomionego backendu na
http://localhost:8000 (python -m uvicorn app.main:app --reload --reload-dir app).
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


print("=" * 70)
print("TEST SZCZEGÓŁOWY: rejestracja -> weryfikacja -> sejf -> hasła")
print("=" * 70)

email = f"user_{os.urandom(4).hex()}@test.com"
password = "Test123!ab"

print("\n[1] Rejestracja użytkownika...")
print(f"    Email: {email}")
status, body = request("POST", "/auth/register", {"email": email, "password": password})
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
if status != 200:
    print("    ❌ BŁĄD rejestracji")
    exit(1)
print("    ✅ Zarejestrowano")

print("\n[2] Odczyt kodu weryfikacyjnego z bazy...")
code = get_verification_code(email)
print(f"    Kod: {code}")
if not code:
    print("    ❌ Brak kodu w bazie")
    exit(1)

print("\n[3] Weryfikacja email...")
status, body = request("POST", "/auth/verify-email", {"email": email, "code": code})
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
if status != 200:
    print("    ❌ BŁĄD weryfikacji")
    exit(1)
print("    ✅ Email zweryfikowany")

print("\n[4] Logowanie...")
status, body = request("POST", "/auth/login", {"email": email, "password": password})
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
print(f"    Cookies: {[c.name for c in cookie_jar]}")
if status != 200:
    print("    ❌ BŁĄD logowania")
    exit(1)
print("    ✅ Zalogowano")

print("\n[5] Pobranie soli sejfu (GET /vault/salt)...")
status, body = request("GET", "/vault/salt")
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
if status != 200:
    print("    ❌ BŁĄD pobierania soli")
    exit(1)
print(f"    ✅ Sól: {body['salt']} (is_new={body['is_new']})")

print("\n[6] Dodawanie hasła (opaque ciphertext - serwer nie zna klucza)...")
test_plaintext_note = "MojeHaslo123!"
fake_ciphertext = "dGVzdG93eS1jaXBoZXJ0ZXh0LW9wYXF1ZQ=="
print(f"    Hasło jawne (tylko do celów testu, nigdy nie wysyłane): {test_plaintext_note}")
print(f"    Ciphertext wysyłany do API: {fake_ciphertext}")
status, body = request("POST", "/passwords", {
    "service": "Test Service",
    "login": "testuser",
    "password": fake_ciphertext,
})
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
if status != 200:
    print("    ❌ BŁĄD dodawania hasła")
    exit(1)
password_id = body["id"]
print(f"    ✅ Dodano hasło, ID: {password_id}")

print("\n[7] Lista haseł...")
status, body = request("GET", "/passwords")
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
found = next((p for p in body if p["id"] == password_id), None)
if status != 200 or not found:
    print("    ❌ Hasło nie widoczne na liście")
    exit(1)
print(f"    ✅ Hasło na liście, ciphertext zgodny: {found['password'] == fake_ciphertext}")

print("\n[8] Sprawdzenie że POST /passwords/decrypt nie istnieje...")
status, body = request("POST", "/passwords/decrypt", {"key": "x", "password": "y"})
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
if status not in (404, 405):
    print("    ❌ PROBLEM: endpoint nadal odpowiada, powinien być usunięty w Kroku 4")
else:
    print("    ✅ Endpoint poprawnie usunięty")

print("\n[9] Usunięcie hasła...")
status, body = request("DELETE", f"/passwords/{password_id}")
print(f"    Status: {status}")
print(f"    Odpowiedź: {body}")
if status != 200:
    print("    ❌ BŁĄD usuwania")
    exit(1)
print("    ✅ Usunięto")

print(f"\n{'=' * 70}")
print("✅✅✅ TEST ZAKOŃCZONY SUKCESEM! ✅✅✅")
print(f"{'=' * 70}")
