# Instrukcja Migracji - v2.0 → v3.0

## ⚠️ Ważne - Breaking Changes

Wersja 3.0 przenosi **całe szyfrowanie haseł do przeglądarki** i usuwa
szyfrowanie Fernet po stronie serwera.

### Co się zmieniło?

**Wersja 2.0:**
- Serwer szyfrował/odszyfrowywał hasła Fernetem, znając klucz użytkownika
  (przesyłany przy każdym żądaniu)
- Endpoint `POST /passwords/decrypt` odszyfrowywał hasło na backendzie

**Wersja 3.0:**
- **Szyfrowanie i odszyfrowanie dzieje się wyłącznie w przeglądarce** (Web Crypto API)
- Klucz szyfrujący (AES-256-GCM) jest wyprowadzany z PIN-u + klucza Fernet + soli
  konta przez PBKDF2 (310 000 iteracji, SHA-256) i **nigdy nie opuszcza przeglądarki**
- Serwer przechowuje wyłącznie nieprzejrzysty ciąg base64 - nie widzi ani klucza,
  ani hasła w postaci jawnej
- Endpoint `POST /passwords/decrypt` **został usunięty** - już niepotrzebny

## 🔄 Migracja

### Jeśli masz stare hasła w bazie danych:

**OPCJA 1: Start od zera (zalecane, jedyna wspierana)**
```bash
# Usuń starą bazę danych
rm passwords.db  # Linux/Mac
Remove-Item passwords.db -Force  # Windows PowerShell

# Uruchom aplikację - nowa baza zostanie utworzona automatycznie
python -m uvicorn app.main:app --reload --reload-dir app
```

Stare hasła zaszyfrowane po stronie serwera (Fernetem) **nie da się** odszyfrować
nowym systemem - format ciphertextu jest inny, a klucz szyfrujący liczony jest
inaczej. Ten projekt jest we wczesnej fazie rozwoju, więc utrata testowych danych
jest akceptowalna - nie ma opcji eksportu/re-importu dla tej migracji.

### Jeśli zaczynasz od zera:

Po prostu uruchom aplikację - wszystko zadziała automatycznie! 🎉

## 📋 Checklist Aktualizacji

- [ ] Zaktualizuj kod (`git pull`)
- [ ] Usuń starą bazę danych `passwords.db`
- [ ] Przebuduj frontend: `cd frontend/frontend-app && npm run build`
- [ ] Uruchom aplikację: `python -m uvicorn app.main:app --reload --reload-dir app`
- [ ] Ustaw PIN sejfu i wygeneruj nowy klucz Fernet w aplikacji
- [ ] **ZAPISZ KLUCZ w bezpiecznym miejscu!**

## 🆘 Pomoc

### Problem: "Błąd odszyfrowania - sprawdź czy PIN i klucz Fernet są poprawne"
- Musisz podać **dokładnie tę samą kombinację** PIN + klucz Fernet, której użyłeś
  przy dodawaniu hasła
- AES-GCM nie rozróżnia "zły PIN" od "zły klucz" - błąd jest zawsze ten sam

### Problem: "Zgubiłem PIN lub klucz"
- Oba żyją tylko w pamięci sesji przeglądarki (nigdzie nie są zapisywane) -
  jeśli je zgubisz, hasła są bezpowrotnie stracone (to nie bug, to feature
  bezpieczeństwa!)

## 📞 Kontakt

W przypadku problemów otwórz Issue na GitHubie:
https://github.com/KaSzymaniak/PasswordManager/issues

---

**Data ostatniej aktualizacji**: 2026-09-28
**Wersja dokumentu**: 2.0

---

# Instrukcja Migracji - v1.0 → v2.0

## ⚠️ Ważne - Breaking Changes

Wersja 2.0 wprowadza **niezgodność wsteczną** z poprzednim systemem szyfrowania.

### Co się zmieniło?

**Wersja 1.0:**
- Jeden globalny klucz Fernet w pliku `.env`
- Wszystkie hasła szyfrowane tym samym kluczem
- Administrator serwera ma dostęp do klucza

**Wersja 2.0:**
- **Każdy użytkownik ma swój własny klucz**
- Klucze generowane w przeglądarce (bezpieczne)
- Administrator **NIE MA dostępu** do kluczy użytkowników
- System "zero-knowledge"

## 🔄 Migracja

### Jeśli masz stare hasła w bazie danych:

**OPCJA 1: Start od zera (zalecane)**
```bash
# Usuń starą bazę danych
rm passwords.db  # Linux/Mac
Remove-Item passwords.db -Force  # Windows PowerShell

# Uruchom aplikację - nowa baza zostanie utworzona automatycznie
python app/main.py
```

**OPCJA 2: Eksport i Re-import**
1. **Przed aktualizacją**: Wyeksportuj hasła z GUI (jeśli była taka funkcja)
2. Zaktualizuj kod
3. Usuń starą bazę: `rm passwords.db`
4. Wygeneruj nowy klucz w aplikacji
5. Ręcznie dodaj hasła ponownie

### Jeśli zaczynasz od zera:

Po prostu uruchom aplikację - wszystko zadziała automatycznie! 🎉

## 📋 Checklist Aktualizacji

- [ ] Zrób backup bazy danych (jeśli masz ważne dane)
- [ ] Wyeksportuj hasła (jeśli potrzebujesz ich zachować)
- [ ] Zaktualizuj kod (`git pull`)
- [ ] Usuń plik `app/.env` (lub usuń linię `FERNET_KEY=...`)
- [ ] Usuń starą bazę danych `passwords.db`
- [ ] Przebuduj frontend: `cd frontend/frontend-app && npm run build`
- [ ] Uruchom aplikację: `python app/main.py`
- [ ] Wygeneruj nowy klucz Fernet w aplikacji
- [ ] **ZAPISZ KLUCZ w bezpiecznym miejscu!**

## 🆘 Pomoc

### Problem: "Nieprawidłowy klucz"
- Sprawdź czy używasz **tego samego klucza** którego użyłeś do szyfrowania
- Klucz musi mieć dokładnie 44 znaki
- Klucz jest case-sensitive (wielkie/małe litery mają znaczenie)

### Problem: "Nie widzę odszyfrowanego hasła"
- Upewnij się, że wpisałeś klucz w żółtej sekcji
- Kliknij przycisk "Pokaż"
- Sprawdź konsolę przeglądarki (F12) w celu zobaczyć logi

### Problem: "Zgubiłem klucz"
- Jeśli klucz był zapisany w localStorage przeglądarki - sprawdź:
  - `F12` → `Application` → `Local Storage` → `http://localhost:8000` → `fernetKey`
- Jeśli nie - niestety hasła są bezpowrotnie stracone (to nie bug, to feature bezpieczeństwa!)

## 📞 Kontakt

W przypadku problemów otwórz Issue na GitHubie:
https://github.com/KaSzymaniak/PasswordManager/issues

---

**Data ostatniej aktualizacji**: 2026-03-02  
**Wersja dokumentu**: 1.0
