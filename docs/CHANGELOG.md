# Changelog - Historia Zmian

## [3.0.0] - 2026-09-28

### 🔐 Główne Zmiany - Szyfrowanie w Przeglądarce

#### Zmieniono
- **Szyfrowanie haseł**: Przeniesione w całości do przeglądarki (Web Crypto API,
  AES-256-GCM) - serwer nigdy nie widzi klucza ani hasła w postaci jawnej
- **Wyprowadzanie klucza**: PBKDF2-HMAC-SHA256 (310 000 iteracji) z PIN-u,
  klucza Fernet i soli konta (`/vault/salt`)
- **Backend**: `app/security.py` i `app/routes/password.py` nie zawierają już
  żadnego kodu szyfrującego

#### Usunięto
- **Endpoint `POST /passwords/decrypt`**: niepotrzebny - odszyfrowanie jest
  teraz w 100% po stronie klienta
- **`encrypt_text()` / `decrypt_text()`** (`app/security.py`) i zależność od
  `cryptography.fernet` w warstwie API
- **Pole `key` w `PasswordCreate`**: klient nie wysyła już żadnego klucza do serwera

#### Dodano
- **`frontend/frontend-app/src/crypto.js`**: moduł `deriveVaultKey()` /
  `encryptText()` / `decryptText()` oparty na natywnym Web Crypto API

### 📁 Zmiany w Plikach

#### Backend (`app/`)
- **security.py**: usunięto `encrypt_text()`, `decrypt_text()`, import `Fernet`
- **routes/password.py**: usunięto `ensure_user_fernet_key()`, `_hash_key()`,
  endpoint `POST /passwords/decrypt`; `add_password`/`update_password` to
  proste zapisy bez szyfrowania
- **schemas/password.py**: usunięto pole `key: str` z `PasswordCreate`

#### Frontend (`frontend/frontend-app/src/`)
- **crypto.js** (nowy plik): `deriveVaultKey()`, `encryptText()`, `decryptText()`
- **App.vue**:
  - `addPassword()`/`decryptPassword()`: szyfrują/odszyfrowują lokalnie
    przed/po wywołaniu API
  - Usunięto `fetchUserInfo()` i pole `hasFernetKey`
  - Dodano `computed: hasExistingPasswords` (`passwords.length > 0`) jako
    zamiennik sygnału adaptacyjnego UI klucza Fernet

### ⚠️ Breaking Changes
- **Stare hasła są niekompatybilne**: wymagany reset bazy danych `passwords.db`
- **Format zaszyfrowanych danych**: `base64(IV || ciphertext+tag)` zamiast
  tokenu Fernet

### 📊 Statystyki

- Pliki zmienione: 5
- Pliki dodane: 1 (`crypto.js`)
- Endpoint usunięty: 1 (`POST /passwords/decrypt`)

---

## [2.3.0] - 2026-09-24

### 🔑 Główne Zmiany - UI Klucza Fernet

#### Dodano
- **Modal generowania klucza**: Wyświetla nowy klucz z ostrzeżeniem "to
  jedyna kopia" i checkboxem "Zapisałem klucz w bezpiecznym miejscu"
  blokującym zamknięcie do potwierdzenia
- **Ekran adaptacyjny**: Jeśli konto ma już zapisane hasła, sekcja klucza
  pokazuje tylko pole do wpisania istniejącego klucza (nie przycisk
  generowania nowego)

#### Usunięto
- **Auto-zapis klucza w `localStorage`**: Klucz Fernet żyje odtąd tylko w
  pamięci sesji przeglądarki, tak jak PIN — sprzeczne z modelem
  zero-knowledge wcześniejsze zachowanie usunięte całkowicie

### 📁 Zmiany w Plikach

#### Frontend (`frontend/frontend-app/src/`)
- **App.vue**: modal generowania klucza, `hasFernetKey`/`fetchUserInfo()`
  (sygnał adaptacyjny UI), usunięcie `watch: fernetKey` i odczytu/zapisu
  `localStorage`

---

## [2.2.0] - 2026-09-18

### 🔒 Główne Zmiany - PIN do Sejfu

#### Dodano
- **Kolumna `kdf_salt`** (`User`) — losowa sól, niesekretna, tylko do KDF
- **`GET /vault/salt`**: generuje/zwraca sól dla zalogowanego użytkownika,
  `is_new` informuje frontend czy to pierwsze wywołanie
- **Ekran PIN-u** w `App.vue`: PIN żyje wyłącznie w pamięci sesji, nigdy
  nie jest zapisywany ani wysyłany do serwera w jawnej postaci

### 📁 Zmiany w Plikach

#### Backend (`app/`)
- **models/user.py**: kolumna `kdf_salt`
- **database.py**: migracja dodająca `kdf_salt`
- **routes/vault.py** (nowy plik): `GET /vault/salt`

#### Frontend (`frontend/frontend-app/src/`)
- **App.vue**: ekran ustawiania/wpisywania PIN-u, stan sesji

---

## [2.1.0] - 2026-09-16

### 📧 Główne Zmiany - Weryfikacja Email i Reset Hasła

#### Dodano
- **Weryfikacja email po rejestracji**: konto tworzone jako niezweryfikowane,
  6-cyfrowy kod wysyłany mailem (fallback do logu serwera bez konfiguracji SMTP)
- **Reset hasła**: `POST /auth/forgot-password` + `POST /auth/reset-password`,
  generyczna odpowiedź niezależnie czy email istnieje (anty-enumeracja)
- **Walidacja siły hasła**: min. 8 znaków, mała/wielka litera, cyfra, znak
  specjalny — przy rejestracji i reset-password, z żywą checklistą w UI
- **`app/email_utils.py`** (nowy plik): wysyłka SMTP (stdlib `smtplib`),
  fallback do logu

#### Zmieniono
- **`login`**: blokuje logowanie niezweryfikowanym kontom (403)

### 📁 Zmiany w Plikach

#### Backend (`app/`)
- **models/user.py**: `email_verified`, kody i daty wygaśnięcia weryfikacji/resetu
- **database.py**: migracja z grandfatheringiem (`email_verified=1` dla
  istniejących kont)
- **email_utils.py** (nowy plik)
- **routes/auth.py**: `verify-email`, `resend-verification`,
  `forgot-password`, `reset-password`
- **schemas/user.py**: nowe schematy żądań + walidator siły hasła

#### Frontend (`frontend/frontend-app/src/`)
- **App.vue**: ekrany weryfikacji kodu i resetu hasła, checklista wymagań
  hasła, toggle pokaż/ukryj

---

## [2.0.0] - 2026-03-02

### 🔐 Główne Zmiany - System Szyfrowania

#### Zmieniono
- **System szyfrowania haseł**: Przejście z globalnego klucza Fernet do kluczy generowanych przez użytkowników
- **Bezpieczeństwo**: Każdy użytkownik teraz generuje i przechowuje swój własny klucz Fernet
- **Backend**: Usunięto wymaganie FERNET_KEY z pliku `.env`

#### Dodano
- **Generator kluczy Fernet w przeglądarce**: Przycisk "🔑 Generuj nowy klucz"
- **localStorage**: Automatyczne zapisywanie klucza w przeglądarce
- **Szczegółowe logowanie**: Backend i frontend teraz logują operacje szyfrowania/odszyfrowania
- **Walidacja kluczy**: Sprawdzanie formatu klucza przed operacjami

#### Naprawiono
- **Generowanie klucza w JavaScript**: Poprawiono konwersję bajtów do base64
- **Vue 3 kompatybilność**: Zamieniono `this.$set()` na zwykłe przypisanie
- **Szyfrowanie**: Klucz Fernet jest teraz przekazywany przy każdej operacji

### 📁 Zmiany w Plikach

#### Backend (`app/`)
- **security.py**:
  - Usunięto globalny klucz Fernet z `.env`
  - `encrypt_text()` teraz przyjmuje klucz jako parametr
  - `decrypt_text()` teraz przyjmuje klucz jako parametr

- **routes/password.py**:
  - Endpoint `POST /passwords`: wymaga klucza w payload
  - Endpoint `POST /passwords/decrypt`: używa klucza z payload
  - Endpoint `PUT /passwords/{id}`: wymaga klucza do reszyfrowania
  - Dodano szczegółowe logowanie wszystkich operacji

- **schemas/password.py**:
  - Dodano pole `key: str` do `PasswordCreate`

- **.env**:
  - Usunięto `FERNET_KEY` (nie jest już potrzebny)

#### Frontend (`frontend/frontend-app/src/`)
- **App.vue**:
  - Dodano funkcję `generateFernetKey()` - generuje klucz w przeglądarce
  - Dodano pole input dla klucza Fernet (z żółtym tłem)
  - `addPassword()`: wysyła klucz wraz z hasłem
  - `decryptPassword()`: używa klucza do odszyfrowania
  - Klucz jest zapisywany w `localStorage`
  - Naprawiono `this.$set()` → `this.decrypted[id] = ...` (Vue 3)
  - Dodano szczegółowe `console.log()` dla debugowania

### 🔬 Pliki Testowe (dodane)
- `test_fernet.py` - Test generowania kluczy Fernet
- `test_e2e.py` - Test end-to-end szyfrowania
- `test_api.py` - Test API przez HTTP
- `test_detailed.py` - Szczegółowy test flow użytkownika
- `check_db.py` - Narzędzie do inspekcji bazy danych

### ⚠️ Breaking Changes
- **Stare hasła są niekompatybilne**: Hasła zaszyfrowane starym systemem NIE MOGĄ być odszyfrowane nowym systemem
- **Wymagany reset bazy**: Należy usunąć starą bazę danych `passwords.db`
- **Użytkownicy muszą wygenerować nowy klucz**: Stary klucz z `.env` nie działa

### 🚀 Jak Używać (Nowa Wersja)

1. Otwórz aplikację w przeglądarce
2. Zaloguj się lub zarejestruj
3. Kliknij "🔑 Generuj nowy klucz" w żółtej sekcji
4. **ZAPISZ KLUCZ W BEZPIECZNYM MIEJSCU** (np. w menedżerze haseł)
5. Dodawaj hasła - będą szyfrowane Twoim kluczem
6. Kliknij "Pokaż" aby odszyfrować hasło

### 🔒 Bezpieczeństwo

**Zalety nowego systemu:**
- ✅ Każdy użytkownik ma swój własny klucz szyfrujący
- ✅ Klucz NIE jest przechowywany na serwerze
- ✅ Bez klucza hasła są bezpowrotnie zaszyfrowane
- ✅ Administrator serwera NIE MOŻE odszyfrować haseł użytkowników

**Ważne ostrzeżenia:**
- ⚠️ **Utrata klucza = utrata dostępu do haseł**
- ⚠️ Klucz jest przechowywany w `localStorage` przeglądarki
- ⚠️ Po wyczyszczeniu danych przeglądarki klucz zostanie usunięty
- ⚠️ **KONIECZNIE zapisz klucz poza przeglądarką**

### 📊 Statystyki

- Pliki zmienione: 5
- Dodane linie: ~150
- Usunięte linie: ~50
- Nowe funkcje: 1 (generator kluczy)
- Naprawione błędy: 2 (konwersja base64, Vue 3 reaktywność)
