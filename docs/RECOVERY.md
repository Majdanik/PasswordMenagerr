# Model Odzyskiwania i Zagrożeń

Ten dokument opisuje wprost: co w tej aplikacji da się odzyskać po
zgubieniu, co nie da się odzyskać **z premedytacją**, i dlaczego. To nie
jest brak funkcji — to świadomy kompromis bezpieczeństwa typowy dla
menadżerów haseł zero-knowledge.

## Dwie niezależne warstwy

Aplikacja rozdziela dwie rzeczy, które łatwo pomylić:

1. **Konto** — kto się loguje do aplikacji (email + hasło).
2. **Sejf** — co odszyfrowuje zapisane hasła (PIN + klucz Fernet).

Te warstwy są **celowo niezależne**. Gdyby PIN był tym samym co hasło
logowania, konta zakładane przez Google (Krok 6, logowanie OAuth) nie
miałyby niczym liczyć klucza sejfu — Google nie zna hasła logowania w tej
aplikacji.

## Co jest odzyskiwalne: Konto

Jeśli zapomnisz hasła logowania:

1. `POST /auth/forgot-password` — podajesz email, dostajesz kod.
2. `POST /auth/reset-password` — kod + nowe hasło.

Odpowiedź `forgot-password` jest **identyczna** niezależnie czy podany
email istnieje w bazie (anty-enumeracja — atakujący nie dowie się, które
adresy są zarejestrowane).

To odzyskuje dostęp do **aplikacji**, nie do **haseł w sejfie** — logowanie
z nowym hasłem samo w sobie nic nie odszyfrowuje.

## Co NIE jest odzyskiwalne: Sejf (PIN + klucz Fernet)

Jeśli zgubisz PIN lub klucz Fernet (albo oba) — **zapisane hasła są
bezpowrotnie stracone.** Serwer nigdy ich nie widział w postaci jawnej,
więc nie ma czego przywrócić.

Powód: PIN + klucz Fernet + sól konta (`kdf_salt`, `GET /vault/salt`)
łączą się przez PBKDF2 (310 000 iteracji, SHA-256) w klucz AES-256-GCM,
**wyłącznie w przeglądarce**. Serwer przechowuje tylko wynikowy szyfrogram
(`base64(IV || ciphertext+tag)`) — nieprzejrzysty ciąg, z którego nie da
się odtworzyć ani PIN-u, ani klucza, ani hasła.

To jest **zero-knowledge**: nawet pełny dostęp do bazy danych i kodu
serwera nie wystarczy, żeby odszyfrować czyjekolwiek hasła bez PIN-u i
klucza Fernet tej osoby.

### Dlaczego nie ma "klucza awaryjnego"

Rozważaliśmy i świadomie odrzuciliśmy pomysł zapisania gdzieś (np. u
administratora, w bazie w innej formie) klucza umożliwiającego odzyskanie
sejfu w razie zgubienia PIN-u/klucza. To by przeniosło problem "co jeśli
zgubię PIN" na "co jeśli zgubię/skradną mi klucz awaryjny" — nie
rozwiązuje go, tylko przenosi na inny fizyczny/cyfrowy przedmiot, i przy
okazji łamie zero-knowledge (ktoś musiałby ten klucz awaryjny przechowywać
w formie odzyskiwalnej).

### Co robić, żeby nie stracić dostępu

- Zapisz klucz Fernet **fizycznie** (kartka, sejf, inny menedżer haseł) —
  wygenerowany raz, modal wymaga potwierdzenia że go zapisałeś.
- Zapamiętaj PIN — jak każde hasło, którego używasz regularnie.
- Nie ma trzeciej opcji. Zgubienie obu = reset sejfu od zera.

## Porównanie do innych menedżerów haseł

To nie jest unikalne podejście — to standard w branży dla narzędzi
faktycznie zero-knowledge:

| Narzędzie | Co jest odzyskiwalne | Co NIE jest odzyskiwalne |
|---|---|---|
| **Ten projekt** | Konto (email) | Sejf (PIN + klucz Fernet) |
| **1Password** | Konto (email), częściowo przez support | Secret Key + Master Password (razem) — utrata obu = utrata danych |
| **Bitwarden** | Konto (email) | Master Password — brak odzyskiwania po stronie serwera z założenia |
| **KeePass** | Nic po stronie "serwera" (brak serwera) | Plik bazy + hasło — zero odzyskiwania w ogóle, offline-only |

1Password dodatkowo wymaga **Secret Key** (analogicznie do naszego klucza
Fernet) obok Master Password — dokładnie ten sam pomysł: dwa niezależne
sekrety, z których żaden osobno nie wystarcza, i żaden nie jest znany
serwerowi. Bitwarden i KeePass idą dalej i nie mają żadnego mechanizmu
odzyskiwania danych sejfu w ogóle — nasz projekt jest w tym sensie
pośrodku: odzyskiwalne konto, nieodzyskiwalny sejf.
