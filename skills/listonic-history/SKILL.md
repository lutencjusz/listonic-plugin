---
name: listonic-history
description: 'Historia i statystyki zakupów Listonic — zrzuca odhaczone pozycje do vaultu i pokazuje popularne produkty. Wyzwalacze: "zsynchronizuj historię zakupów", "co kupuję najczęściej", "popularne produkty", "statystyki zakupów".'
---

# listonic-history

- Sync historii + odśwież popularne: `listonic sync-history`
- Sync + czyszczenie listy „Najbliższe zakupy": `listonic sync-history --prune`
- Tylko pobranie historii z serwera do vaultu (bez API): `listonic sync-history --pull-only`
- Popularne (top N): `listonic popular --top 20 --json`
- Statystyki (suma, unikalne, zakres dat): `listonic stats --json`

Każde `sync-history` **najpierw** próbuje ściągnąć zaległą historię z serwera (jeśli jest
`~/.mikrus/config.json`), potem robi lokalny sync.

Zrzuty trafiają do `<vault>/Google Keep/Zakupy/` (`historia/` + `Popularne produkty.md`);
katalog konfigurowalny przez `zakupy_dir`. Vault wskazuje `vault_path` w `~/.listonic/config.json`.

## Automatyzacja (opcjonalne)
Sync można zautomatyzować: na serwerze always-on cron uruchamia `listonic sync-history --prune`
(serwer jest wtedy jedynym klientem API i odświeża tokeny), a maszyna lokalna tylko ściąga
gotowe pliki przez `listonic sync-history --pull-only` (np. z harmonogramu systemowego).
Połączenie do serwera czytane jest z `~/.mikrus/config.json`; bez niego krok pull jest
cicho pomijany.

## Zasady
- Data pozycji = **data synchronizacji** (API Listonic nie zwraca daty odhaczenia — jest tylko `CreationDate` = data dodania, świadomie nieużywana, bo myli).
- `--prune` usuwa odhaczone **tylko** z listy „Najbliższe zakupy" (konfigurowalna: `prune_list` w `~/.listonic/config.json`), i dopiero **po** zapisaniu do historii. Inne listy nietknięte. Ręczny `sync-history` bez `--prune` nic nie kasuje.
- Dedup po ID pozycji (`~/.listonic/logged_items.json`) — ta sama odhaczona pozycja nie liczy się dwa razy.
- **Plik dnia już istnieje** (np. wcześniejszy sync tego dnia): nowe pozycje są **dopisywane** na koniec, frontmatter i wcześniejsze wpisy zostają nietknięte. Plik jest zapisywany tylko gdy są nowe pozycje — w przeciwnym razie nietknięty. Dzięki dedupowi wielokrotny sync tego samego dnia **nie duplikuje** wpisów. `Popularne produkty.md` jest regenerowany (nadpisywany) za każdym razem.
