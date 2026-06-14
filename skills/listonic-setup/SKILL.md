---
name: listonic-setup
description: 'Instalacja i konfiguracja pluginu Listonic — instaluje CLI przez uv tool, zapisuje credentials i weryfikuje logowanie. Wyzwalacze: "skonfiguruj listonic", "zaloguj do listonic", "instalacja listonic".'
---

# listonic-setup

1. Zainstaluj CLI: `uv tool install git+https://github.com/lutencjusz/listonic-plugin.git`
2. Zaloguj: `listonic login` (poda email + hasło interaktywnie).
3. Weryfikacja: `listonic lists --unchecked --json` — powinno zwrócić listy.

## Vault dla historii (opcjonalne)
Skill `listonic-history` zrzuca odhaczone pozycje do vaultu Obsidian. Wskaż go raz w
`~/.listonic/config.json`: `{"vault_path": "/sciezka/do/Vault"}`. Bez tego komendy
`sync-history`/`popular` zgłoszą brak `vault_path`; zwykłe `lists`/`add`/`check` działają bez niego.

## Logowanie przez Google
CLI używa wyłącznie `provider=password` (email + wewnętrzne hasło Listonic) — **nie obsługuje OAuth Google**. Jeśli użytkownik loguje się do Listonic „przez Google":
- Login to **email Google**, ale potrzebne jest **osobne hasło Listonic** (NIE hasło Google — ono się nie uwierzytelni).
- Rozwiązanie: w Listonic (apka/web) → ustawienia konta → ustaw/zmień hasło (lub „nie pamiętam hasła" na ten sam email), potem `listonic login` z emailem Google + nowym hasłem Listonic.

## Zasady
- Credentials/tokeny trafiają do `~/.listonic/config.json` — **poza vaultem**, nigdy nie commitować ani nie wypisywać.
- Hasła nie podawaj w argumentach (zostaje w historii powłoki) — tylko interaktywnie.
