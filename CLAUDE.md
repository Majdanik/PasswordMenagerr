# CLAUDE.md — PasswordManager (praca inżynierska)

Ten plik jest automatycznie wczytywany przez Claude Code przy starcie w tym
folderze. Zawiera pełny kontekst ustalony wcześniej w rozmowie z Claude
(Cowork) — żeby nie trzeba było niczego tłumaczyć od nowa.

## Co to za projekt

Menadżer haseł — praca inżynierska. Stack: FastAPI (Python) w `app/`,
Vue 3 + Vite w `frontend/frontend-app/`, SQLite. Repo:
`github.com/KaSzymaniak/PasswordManager`. Projekt zaczęty kiedyś jako
dwuosobowa inicjatywa na etapie szkicu, od dawna rozwijany samodzielnie.
Termin: przed startem roku akademickiego — napięty, priorytet ma rdzeń
bezpieczeństwa (sejf), nie funkcje poboczne.

## Zasady pracy — WAŻNE, przeczytaj zanim zaczniesz kodować

1. **Nie zaczynaj implementować kroku bez wyraźnego "tak, rób" od
   użytkownika.** Raz już doszło do sytuacji, gdzie asystent napisał cały
   kod bez pytania, mimo że jeszcze nie było ustalone jak dokładnie ma to
   działać — użytkownik wyraźnie zaznaczył, że tego nie chce.
2. Każdy krok poniżej = osobny branch, mały i testowalny osobno. Nie łącz
   kroków w jeden wielki branch.
3. Odpowiadaj zwięźle, prostym językiem — bez rozwlekania.
4. Zanim zmienisz coś związanego z bezpieczeństwem/kryptografią, upewnij
   się że rozumiesz model opisany niżej — nie zmieniaj go samodzielnie.
5. Commity robi użytkownik sam (`git commit`) — Claude edytuje/staguje
   pliki, ale nie commituje bez wyraźnej prośby.
6. Merge do `main` i zakładanie nowego brancha następuje dopiero po
   przetestowaniu i zacommitowaniu bieżącego kroku ("merge-then-branch") —
   nie stackować branchy bez potrzeby.

## Ustalony model bezpieczeństwa (nie zmieniać bez rozmowy z użytkownikiem)

Dwie niezależne warstwy:

- **Konto** (kto się loguje) — email + hasło, docelowo też logowanie
  Google (patrz Krok 6 — odłożone na koniec). Odzyskiwalne przez kod
  wysłany na zweryfikowany email.
- **Sejf** (co odszyfrowuje hasła) — PIN (użytkownik pamięta) + klucz
  Fernet (zapisany fizycznie, np. na kartce — to NIE musi być plik z
  pendrive'a, wystarczy zapisany gdziekolwiek). Połączone przez KDF
  (PBKDF2 z Web Crypto API, natywne w przeglądarce) dają klucz do
  AES-GCM. Cała kryptografia dzieje się w przeglądarce — serwer nigdy
  nie widzi PIN-u, klucza Fernet ani hasła w postaci jawnej, tylko
  gotowy szyfrogram (opaque blob).

Zasady, które wynikają z tego modelu:

- PIN jest niezależny od hasła logowania (bo konta Google nie mają hasła
  w appce — gdyby PIN = hasło logowania, konta Google nie miałyby czym
  liczyć klucza).
- Odzyskiwalne: tylko konto (login+hasło) przez email. **Nieodzyskiwalne
  z premedytacją:** PIN i klucz Fernet — to świadomy kompromis
  (zero-knowledge), identyczny jak w 1Password/Bitwarden/KeePass. Nie
  proponuj "klucza awaryjnego" jako planu B — użytkownik świadomie to
  odrzucił (przenosi problem zgubienia na inny fizyczny przedmiot,
  zamiast go rozwiązywać). Pełny model zagrożeń: `docs/RECOVERY.md`.
- Bez SMS w odzyskiwaniu (tylko email, żeby nie dokładać zależności od
  płatnego dostawcy SMS).
- Bez sprzętowego klucza (Arduino/YubiKey) na tym etapie — to pomysł na
  ewentualną pracę magisterską, nie na tę pracę inżynierską. Nie sugeruj
  tego jako "łatwe do dodania teraz".
- Utrata istniejących danych testowych przy zmianach modelu jest
  akceptowalna (projekt w fazie rozwoju) — nie trzeba budować migracji
  zachowujących stare zaszyfrowane hasła przy zmianach schematu
  kryptografii, wystarczy `docs/MIGRATION.md` z instrukcją resetu bazy.

## Krok 0 — Porządki (branch: `chore/cleanup`) — ✅ ZROBIONE

Usunięto `app/pip`/`app/python`, osierocony `frontend/` w korzeniu,
zależność `fernet-ts`. Naprawiono literówkę w `.gitignore`, dopisano
`PUT /passwords/{id}` do dokumentacji, uzupełniono strukturę projektu i
instrukcję uruchomienia w README. `app/migrate_encrypt.py` usunięty.
`test_api.py`/`test_detailed.py` zostawione bez zmian wtedy (i tak miały
się zmienić ponownie po Kroku 4) — domknięte dopiero w Kroku 5.

## Krok 1 — Fundament kont: email + reset hasła (branch: `feature/email-verification`) — ✅ ZROBIONE

Zaimplementowane zgodnie z pierwotnym opisem: kolumny `User`
(`email_verified`, kody weryfikacji/resetu + wygasanie), migracja z
grandfatheringiem istniejących kont (`email_verified=1` wstecznie),
`app/email_utils.py` (stdlib `smtplib`, fallback do logu serwera gdy brak
SMTP w `.env`), 6 endpointów `/auth/*`. Dodatkowo: walidacja siły hasła
(min. 8 znaków, mała/wielka litera, cyfra, znak specjalny) na rejestracji i
reset-password, z minimalnym UI frontendowym (checklista wymagań, toggle
pokaż/ukryj, potwierdzenie hasła). Realna wysyłka SMTP nieprzetestowana
pomyślnie (blokady Google na nowych kontach) — fallback do logu w pełni
wystarczający i przetestowany.

## Krok 2 — PIN do sejfu (branch: `feature/vault-pin`) — ✅ ZROBIONE (zmienione względem pierwotnego opisu)

Backend zgodnie z planem: kolumna `kdf_salt`, `GET /vault/salt` (generuje
sól przy pierwszym wywołaniu, zwraca `is_new` żeby frontend wiedział czy to
pierwszy raz). **Frontend inaczej niż pierwotnie zaplanowano**: początkowo
zbudowano osobny ekran "Ustaw/Wpisz PIN do sejfu" jako bramkę przed
wejściem do głównego widoku — po testach okazało się to mylące (bramka nic
realnie nie waliduje, tylko sprawdza format), więc **PIN został scalony w
jedno pole w tej samej sekcji co klucz Fernet** w głównym widoku, bez
osobnej podstrony. PIN żyje wyłącznie w pamięci sesji (nigdy zapisywany),
tak jak klucz Fernet.

## Krok 3 — Generator klucza Fernet do zapisania (branch: `feature/fernet-key-ui`) — ✅ ZROBIONE

Ekran/modal przy generowaniu z checkboxem "Zapisałem klucz w bezpiecznym
miejscu" blokującym zamknięcie modala. Ekran adaptacyjny: jeśli konto ma
już zapisane hasła (`hasExistingPasswords`, liczone z `passwords.length`),
pokazuje tylko pole do wpisania istniejącego klucza, nie przycisk
generowania nowego. Auto-zapis klucza w `localStorage` **usunięty**
całkowicie (był z wcześniejszych wersji, sprzeczny z modelem
zero-knowledge) — klucz żyje tylko w pamięci sesji.

## Krok 4 — Szyfrowanie w przeglądarce (branch: `feature/client-side-crypto`) — ✅ ZROBIONE

Największy krok. `frontend/frontend-app/src/crypto.js` (nowy moduł):
PBKDF2-HMAC-SHA256 (310 000 iteracji) z PIN + klucz Fernet + sól →
AES-256-GCM. Format zapisu: `base64(IV || ciphertext+tag)`. Backend
uproszczony do magazynu opaque stringów — usunięto `ensure_user_fernet_key`,
`encrypt_text`/`decrypt_text`, endpoint `POST /passwords/decrypt` (zbędny,
odszyfrowanie w 100% po stronie klienta), pole `key` z `PasswordCreate`.
Stare hasła zresetowane (usunięcie `passwords.db`) zamiast migracji —
zgodnie z ustaleniem że utrata danych testowych jest akceptowalna.
`docs/MIGRATION.md` ma sekcję v2.0→v3.0 opisującą ten reset.

Świadomy kompromis: AES-GCM nie rozróżnia "zły PIN" od "zły klucz Fernet"
w komunikacie błędu — to celowe (osobna weryfikacja PIN-u osobno od klucza
otworzyłaby możliwość brute-force'owania samego PIN-u, 10 000 kombinacji).

## Krok 5 — Dokumentacja (branch: `docs/update-architecture`) — 🔄 W TRAKCIE

`docs/architecture.md` przepisany na aktualny stan (nie duplikuje historii
zmian — to rola `docs/CHANGELOG.md`). Dopisane retroaktywne wpisy
CHANGELOG dla Kroków 1-3. Nowy `docs/RECOVERY.md` — jawny model zagrożeń.
`test_api.py`/`test_detailed.py` przepisane pod cookie-auth + nowe API
(stdlib `urllib`, zero nowych zależności). `test_e2e.py`/`test_fernet.py`/
`app/decrypt_test.py` usunięte (testowały martwą koncepcję sam-Fernet).

## Krok 6 — Logowanie przez Google (branch: `feature/google-oauth`) — OPCJONALNE, na sam koniec, tylko jeśli starczy czasu

Nie jest to esencja pracy (tematem jest bezpieczeństwo sejfu, nie metoda
logowania) i wymaga zewnętrznej zależności (projekt w Google Cloud). Robić
tylko jeśli zostanie czas po Krokach 0-5.

- Nowy `app/oauth.py` — klient Google OAuth2 (Authlib), Authorization
  Code flow (przekierowanie, nie popup).
- `app/routes/auth.py` — `GET /auth/google/login`, `GET
  /auth/google/callback` (zakłada/łączy konto po emailu, `email_verified
  = True` automatycznie, bo Google już to zweryfikował).
- `app/main.py` — dodać `SessionMiddleware` (wymagane przez Authlib).
- `requirements.txt` + `app/requirements.txt` — dodać `authlib`, `httpx`,
  `itsdangerous`.
- Google Cloud: projekt w trybie "Testing" (lista dopuszczonych maili,
  bez pełnej weryfikacji Google) w zupełności wystarcza — nie trzeba nic
  publikować ani czekać na akceptację Google.
