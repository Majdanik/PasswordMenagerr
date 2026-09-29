Aplikacja menadżera haseł umożliwiająca bezpieczne generowanie, przechowywanie i zarządzanie hasłami użytkownika.

## � Bezpieczeństwo

- **Szyfrowanie end-to-end**: PIN + klucz Fernet + sól konta łączą się w przeglądarce (PBKDF2 → AES-GCM) w klucz sejfu
- **Zero-knowledge**: Serwer NIE ma dostępu do PIN-u, klucza Fernet ani haseł w postaci jawnej
- **Brak trwałego zapisu**: PIN i klucz Fernet żyją tylko w pamięci sesji przeglądarki - wpisujesz je po każdym zalogowaniu
- **Konto odzyskiwalne, sejf nie**: hasło logowania możesz zresetować mailem; PIN i klucz Fernet - nie (zero-knowledge, patrz `docs/RECOVERY.md`)
- ⚠️ **Ważne**: Zapisz klucz Fernet w bezpiecznym miejscu - bez niego (i bez PIN-u) nie odzyskasz haseł!

## 🛠️ Technologie

- **Frontend:** Vue 3, Vite
- **Backend:** FastAPI (Python)
- **Baza danych:** SQLite
- **Szyfrowanie:** Fernet (cryptography)
- **Autentykacja:** JWT, bcrypt
- **Inne:** SQLAlchemy, Pydantic

## 🚀 Uruchomienie aplikacji

### Szybki start (lokalnie)

1. Zainstaluj backend (z korzenia repo):
   - Komenda: `pip install -r requirements.txt`
2. Zbuduj frontend:
   - Wejdź do folderu `frontend/frontend-app/`, zainstaluj zależności i wykonaj build.
   - Komendy: `cd frontend/frontend-app` → `npm install` → `npm run build`
3. Uruchom backend (z korzenia repo, nie z `app/`):
   - Importy w kodzie mają postać `from app.database import ...`, więc `app` musi być pakietem widocznym z korzenia repo — `python app/main.py` tego nie zapewni.
   - Komenda: `python -m uvicorn app.main:app --reload --reload-dir app`
   - Backend serwuje zbudowany frontend z `frontend/frontend-app/dist`.
4. Otwórz w przeglądarce:
   - `http://localhost:8000`

### Uruchomienie na Replit

1. Zainstaluj zależności backendu z korzenia repo.
   - Komenda: `pip install -r requirements.txt`
2. Zbuduj frontend w `frontend/frontend-app/` (powstaje `dist/`).
   - Komendy: `cd frontend/frontend-app` → `npm install` → `npm run build`
3. W ustawieniach Replit uruchamiaj komendę (z korzenia repo):
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Otwórz publiczny URL replita.

## 📖 Jak używać

### Pierwsze uruchomienie

1. **Zarejestruj się** - utwórz konto podając email i hasło
2. **Zaloguj się** - wprowadź swoje dane logowania
3. **Wygeneruj klucz Fernet** - kliknij przycisk "🔑 Generuj nowy klucz"
4. **ZAPISZ KLUCZ!** - skopiuj i zapisz klucz w bezpiecznym miejscu (np. w innym menedżerze haseł)
   - ⚠️ Bez tego klucza NIE ODSZYFRUJESZ swoich haseł!
   - Klucz wygląda np. tak: `wRs7fzBk1FQMskeg+wBu8GEo88onobj+xB4jnNBEw67Ss=`

### Dodawanie haseł

1. Upewnij się, że **klucz Fernet jest wpisany** w żółtej sekcji
2. Wypełnij formularz:
   - **Serwis**: Nazwa serwisu (np. "Facebook", "Gmail")
   - **Login**: Nazwa użytkownika lub email
   - **Hasło**: Hasło do tego serwisu
3. Kliknij **"Dodaj"**
4. Hasło zostanie **zaszyfrowane** Twoim kluczem i zapisane w bazie

### Wyświetlanie haseł

1. Upewnij się, że **klucz Fernet jest wpisany** (ten sam, którego użyłeś do szyfrowania)
2. Kliknij **"Pokaż"** przy wybranym haśle
3. Hasło zostanie odszyfrowane i wyświetlone zamiast `***`

### Usuwanie haseł

1. Kliknij **"Usuń"** przy wybranym haśle
2. Potwierdź usunięcie

## ⚠️ Ważne Informacje o Bezpieczeństwie

### PIN i Klucz Fernet

- **Dwa niezależne sekrety**: PIN (pamiętasz) + klucz Fernet (zapisujesz fizycznie) - oba potrzebne do odszyfrowania sejfu
- **Przechowywanie**: Oba żyją tylko w pamięci sesji przeglądarki - nigdzie nie są trwale zapisywane
- **Backup**: **KONIECZNIE** zapisz klucz Fernet poza przeglądarką (kartka, inny menedżer haseł); PIN zapamiętaj
- **Utrata**: Jeśli zgubisz PIN lub klucz, **hasła są bezpowrotnie stracone** - to celowy kompromis bezpieczeństwa, nie da się tego obejść (szczegóły: `docs/RECOVERY.md`)
- **Każde logowanie**: Oba trzeba wpisać ponownie po każdym zalogowaniu/odświeżeniu strony

### Co się dzieje z Twoimi danymi?

- **Hasła**: Przechowywane **zaszyfrowane** (AES-GCM) w bazie SQLite na serwerze - serwer widzi tylko nieprzejrzysty ciąg znaków
- **PIN i klucz Fernet**: **NIE** są przechowywane na serwerze, tylko w Twojej przeglądarce, tylko na czas sesji
- **Konto** (login/hasło): odzyskiwalne mailem (`docs/RECOVERY.md`) - to inna warstwa niż sejf
- **Administrator serwera**: **NIE MOŻE** odszyfrować Twoich haseł bez PIN-u i klucza
- **Bezpieczeństwo**: System typu "zero-knowledge" - tylko Ty znasz swój PIN i klucz

## 📁 Struktura Projektu

```
PasswordManager/
├── app/                        # Backend (FastAPI)
│   ├── main.py                 # Punkt wejścia, CORS, middleware bezpieczeństwa
│   ├── database.py             # Konfiguracja SQLAlchemy, migracje kolumn
│   ├── security.py             # JWT, hashowanie, szyfrowanie Fernet
│   ├── models/                 # Modele ORM (User, PasswordEntry)
│   ├── routes/                 # Endpointy /auth i /passwords
│   ├── schemas/                # Modele Pydantic
│   └── requirements.txt
├── frontend/
│   └── frontend-app/           # Frontend (Vue 3 + Vite)
│       ├── src/                # Komponenty, logika aplikacji
│       ├── public/
│       └── dist/               # Zbudowany frontend serwowany przez backend
├── docs/
│   ├── architecture.md         # Dokumentacja architektury i bezpieczeństwa
│   ├── RECOVERY.md             # Model zagrożeń: co odzyskiwalne, co nie
│   ├── CHANGELOG.md
│   └── MIGRATION.md
├── requirements.txt             # Zależności backendu (korzeń repo)
└── README.md
```