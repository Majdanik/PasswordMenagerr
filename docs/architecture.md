# Password Manager - Dokumentacja Architektury

Ten plik opisuje **aktualny stan** systemu. Historia zmian (co i kiedy się
zmieniło) jest w `docs/CHANGELOG.md` — nie duplikujemy jej tutaj.

## Przegląd Systemu

Password Manager to aplikacja webowa do bezpiecznego przechowywania i
zarządzania hasłami, z szyfrowaniem end-to-end wykonywanym w całości w
przeglądarce (model zero-knowledge — serwer nigdy nie widzi PIN-u, klucza
Fernet ani hasła w postaci jawnej).

### Technologie
- **Backend**: FastAPI (Python 3.13+)
- **Frontend**: Vue 3 + Vite
- **Baza danych**: SQLite
- **Szyfrowanie**: Web Crypto API w przeglądarce — PBKDF2-HMAC-SHA256
  (310 000 iteracji) z PIN + klucz Fernet + sól konta → AES-256-GCM.
  Backend nie wykonuje żadnej kryptografii haseł, tylko przechowuje
  gotowy szyfrogram (opaque string).
- **Autentykacja**: JWT w HttpOnly cookies

---

## Model bezpieczeństwa — dwie niezależne warstwy

- **Konto** (kto się loguje): email + hasło, weryfikacja emailem po
  rejestracji, reset hasła przez kod mailem. Odzyskiwalne.
- **Sejf** (co odszyfrowuje hasła): PIN + klucz Fernet + sól. Żyją tylko w
  pamięci sesji przeglądarki, nigdy nie są zapisywane ani wysyłane do
  serwera. Nieodzyskiwalne z premedytacją (zero-knowledge).

Pełny model zagrożeń i uzasadnienie: `docs/RECOVERY.md`.

---

## Architektura Aplikacji

### Backend Structure
```
app/
├── main.py              # FastAPI app, CORS, middleware, security headers
├── database.py          # SQLAlchemy setup, lekka migracja kolumn (ALTER TABLE)
├── security.py           # JWT, hashowanie haseł (bcrypt)
├── email_utils.py        # Wysyłka kodów mailem (SMTP), fallback do logu
├── models/
│   ├── user.py          # User ORM model
│   └── password.py       # PasswordEntry ORM model
├── routes/
│   ├── auth.py           # /auth/* endpoints
│   ├── password.py       # /passwords/* endpoints
│   └── vault.py           # /vault/* endpoints (sól KDF)
└── schemas/
    ├── user.py
    └── password.py
```

### Frontend Structure
```
frontend/frontend-app/
├── src/
│   ├── App.vue           # Główny komponent (Options API, bez routera)
│   ├── crypto.js          # PBKDF2 + AES-GCM (Web Crypto API)
│   ├── main.js
│   └── style.css
├── dist/                  # Production build (serwowany przez backend)
└── vite.config.js
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE,
    hashed_password VARCHAR,
    fernet_key_hash VARCHAR,              -- martwe pole od Kroku 4 (patrz niżej)
    email_verified BOOLEAN DEFAULT 0,
    email_verification_code VARCHAR,
    email_verification_expires DATETIME,
    password_reset_code VARCHAR,
    password_reset_expires DATETIME,
    kdf_salt VARCHAR                        -- sól do PBKDF2 (Web Crypto, frontend)
);

-- Passwords table
CREATE TABLE passwords (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    service VARCHAR,
    login VARCHAR,
    password VARCHAR,                       -- opaque ciphertext: base64(IV || AES-GCM)
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

`fernet_key_hash`/`has_fernet_key` (kolumna + property w `User`) nie są już
używane — od Kroku 4 backend nigdy nie widzi klucza Fernet, więc nie ma
czego hashować. Zostawione jako nieużywane pole (sprzątanie odłożone),
frontend liczy sygnał "czy masz już zapisane hasła" z `passwords.length`.

---

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` — rejestracja (konto tworzone jako niezweryfikowane)
- `POST /auth/login` — logowanie (ustawia HttpOnly cookie), blokuje
  niezweryfikowane konta (403)
- `POST /auth/logout` — wylogowanie (usuwa cookie)
- `GET /auth/me` — dane zalogowanego użytkownika
- `POST /auth/verify-email` — potwierdzenie kodu wysłanego przy rejestracji
- `POST /auth/resend-verification` — nowy kod weryfikacyjny
- `POST /auth/forgot-password` — wysyła kod resetu (generyczna odpowiedź
  niezależnie czy email istnieje — anty-enumeracja)
- `POST /auth/reset-password` — ustawia nowe hasło kodem z maila

### Vault (`/vault`)
- `GET /vault/salt` — zwraca/generuje sól KDF dla zalogowanego użytkownika
  (`is_new` mówi frontendowi czy to pierwsze wywołanie)

### Password Management (`/passwords`)
- `GET /passwords` — lista haseł (opaque ciphertext, klient odszyfrowuje
  lokalnie)
- `POST /passwords` — dodaj hasło (ciphertext gotowy z przeglądarki)
- `PUT /passwords/{id}` — edytuj hasło (ciphertext gotowy z przeglądarki)
- `DELETE /passwords/{id}` — usuń hasło

Brak `POST /passwords/decrypt` — usunięty w Kroku 4, odszyfrowanie w 100%
po stronie klienta.

---

## Deployment

### Development
```bash
# Backend (z korzenia repo)
python -m uvicorn app.main:app --reload --reload-dir app

# Frontend build
cd frontend/frontend-app
npm run build
```

### Production Considerations
1. Ustaw `COOKIE_SECURE=true` w `.env`
2. Użyj HTTPS (nginx/Apache reverse proxy)
3. Zmienna `SECRET_KEY` z bezpiecznego źródła
4. Skonfiguruj realne SMTP (`SMTP_HOST`/`PORT`/`USERNAME`/`PASSWORD`/`FROM`)
   z zaufanej, "rozgrzanej" domeny/konta — nowe konta bywają blokowane
5. Backup bazy danych regularnie
6. Rate limiting na poziomie reverse proxy (patrz Roadmap niżej)

---

## Roadmap Bezpieczeństwa

### ✅ Zrobione
- HttpOnly cookies + CORS hardening
- Security headers + CSP
- Email verification + reset hasła
- PIN sejfu + PBKDF2/AES-GCM zamiast serwerowego Fernet (docelowo planowano
  Argon2id — zrealizowano PBKDF2 z Web Crypto API; klucz Fernet nadal jest
  jednym ze składników wejściowych KDF, nie został w pełni zastąpiony
  hasłem głównym — to świadoma decyzja z modelu bezpieczeństwa, nie
  niedopatrzenie)

### 🔜 Pending
- **Rate Limiting + Account Lockouts** — limit prób logowania, blokada
  konta po nieudanych próbach. Istotne też dla kodów weryfikacyjnych/
  resetu (6 cyfr, brak dziś limitu prób zgadywania)
- **2FA TOTP** — pyotp, QR code, weryfikacja przy logowaniu
- **Audit Logs** — logowanie zdarzeń bezpieczeństwa (logowania, nieudane
  próby), runbooki operacyjne
- **Logowanie przez Google** (Krok 6, opcjonalne) — patrz `CLAUDE.md`
