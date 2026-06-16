> 🇬🇧 English version: [README.md](README.md)

# listonic-plugin

Plugin Claude Code do obsługi list zakupów [Listonic](https://listonic.com/) — prosto z
rozmowy z Claude. Daje skille do odczytu i edycji list, własną historię odhaczonych
zakupów zrzucaną do vaultu Obsidian oraz ranking najczęściej kupowanych produktów.

Pod spodem działa backend CLI w Pythonie (`listonic`), który rozmawia z API Listonic.

## Co potrafi

- **listonic-lists** — pokaż listy i pozycje (wszystko / do kupienia / odhaczone).
- **listonic-edit** — dodaj pozycję, odhacz, cofnij odhaczenie, usuń (z potwierdzeniem).
- **listonic-history** — zrzuć odhaczone do historii w vaultcie, pokaż statystyki i ranking.
- **listonic-setup** — instalacja CLI, logowanie, weryfikacja.

## Instalacja (dwa kroki)

Plugin to skille **oraz** backend CLI — zainstaluj oba.

```bash
# 1) Skille — marketplace Claude Code
/plugin marketplace add lutencjusz/listonic-plugin
/plugin install listonic-plugin@listonic-plugin

# 2) Backend CLI (binarka `listonic`)
uv tool install git+https://github.com/lutencjusz/listonic-plugin.git
```

Pominięcie kroku 2 to najczęstszy powód „zainstalowałem, a nie działa" — skille wołają CLI.

## Logowanie

```bash
listonic login        # zapyta o email i hasło interaktywnie
```

Tokeny lądują w `~/.listonic/config.json` — **poza repozytorium i vaultem**. Hasła nie
podawaj w argumentach (zostają w historii powłoki) — tylko interaktywnie.

Do użycia bezinteraktywnego (cron/CI) `login` czyta też `LISTONIC_EMAIL` i
`LISTONIC_PASSWORD` ze środowiska (gdy nieustawione — wraca do interaktywnych pytań).
Trzymaj je w pliku z ograniczonymi uprawnieniami (np. `chmod 600`), nigdy w repo:

```bash
set -a; . ./.listonic.env; set +a   # eksportuje LISTONIC_EMAIL / LISTONIC_PASSWORD
listonic login
```

**Konto „przez Google":** CLI używa wyłącznie logowania `email + hasło Listonic` (nie
OAuth Google). Jeśli zakładałeś konto przez Google, ustaw najpierw hasło Listonic w
aplikacji/web (ustawienia konta → ustaw/zmień hasło lub „nie pamiętam hasła" na ten sam
email), a potem zaloguj się emailem Google + tym hasłem Listonic.

## Historia zakupów (opcjonalne)

Skill `listonic-history` zapisuje odhaczone pozycje do vaultu Obsidian i generuje ranking
popularnych produktów. Wskaż vault raz w `~/.listonic/config.json`:

```json
{ "vault_path": "/sciezka/do/Vault" }
```

Bez `vault_path` komendy `sync-history`/`popular` zgłoszą brak ścieżki; zwykłe
`lists`/`add`/`check` działają bez niego. Domyślnie historia trafia do
`<vault>/Google Keep/Zakupy/` (katalog konfigurowalny przez `zakupy_dir`).

### Sync na serwerze (opcjonalne)

Jeśli masz serwer always-on, sync historii może biec tam (cron), a maszyna lokalna tylko
ściąga gotowe pliki: `listonic sync-history --pull-only`. Połączenie czytane jest z
`~/.mikrus/config.json`; gdy go nie ma, krok pull jest cicho pomijany.

## Komendy CLI

```bash
listonic lists [--checked|--unchecked] [--json]
listonic add    "<lista>" "<pozycja>"
listonic check  "<lista>" "<pozycja>" [--uncheck]
listonic remove "<lista>" "<pozycja>"
listonic sync-history [--prune] [--pull-only]
listonic popular [--top N] [--json]
listonic stats [--json]
```

## Bezpieczeństwo

- Poświadczenia i tokeny trzymane są wyłącznie w `~/.listonic/config.json`, **nigdy w repo**.
- Plugin nie zawiera Twoich kluczy. `CLIENT_ID`/`CLIENT_SECRET` w kodzie to stałe klienta
  OAuth aplikacji Listonic (wymagane, by API odpowiedziało) — nie są poświadczeniem konta.
- Operacje zapisu (`add`/`check`/`remove`, `--prune`) modyfikują realne listy — skill
  `listonic-edit` prosi o potwierdzenie przed zapisem.

## Licencja

MIT — patrz [LICENSE](LICENSE).
