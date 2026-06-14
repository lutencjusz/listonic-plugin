> 🇵🇱 Wersja polska: [README_PL.md](README_PL.md)

# listonic-plugin

A Claude Code plugin for managing [Listonic](https://listonic.com/) shopping lists —
straight from a conversation with Claude. It provides skills to read and edit lists,
builds your own history of checked-off purchases dumped into an Obsidian vault, and ranks
your most frequently bought products.

Under the hood it runs a Python CLI backend (`listonic`) that talks to the Listonic API.

## What it does

- **listonic-lists** — show lists and items (all / to-buy / checked off).
- **listonic-edit** — add an item, check off, uncheck, remove (with confirmation).
- **listonic-history** — dump checked items into vault history, show stats and a ranking.
- **listonic-setup** — install the CLI, log in, verify.

## Installation (two steps)

The plugin is skills **and** a CLI backend — install both.

```bash
# 1) Skills — Claude Code marketplace
/plugin marketplace add lutencjusz/listonic-plugin
/plugin install listonic-plugin@listonic-plugin

# 2) CLI backend (the `listonic` binary)
uv tool install git+https://github.com/lutencjusz/listonic-plugin.git
```

Skipping step 2 is the most common cause of "I installed it but it doesn't work" — the
skills call the CLI.

## Logging in

```bash
listonic login        # prompts for email and password interactively
```

Tokens are stored in `~/.listonic/config.json` — **outside the repository and the vault**.
Don't pass passwords as arguments (they stay in shell history) — interactively only.

**"Sign in with Google" accounts:** the CLI uses `email + Listonic password` login only
(not Google OAuth). If you created your account through Google, first set a Listonic
password in the app/web (account settings → set/change password, or "forgot password" for
the same email), then log in with your Google email + that Listonic password.

## Purchase history (optional)

The `listonic-history` skill writes checked-off items into an Obsidian vault and generates
a ranking of popular products. Point it at your vault once in `~/.listonic/config.json`:

```json
{ "vault_path": "/path/to/Vault" }
```

Without `vault_path`, the `sync-history`/`popular` commands report a missing path; plain
`lists`/`add`/`check` work without it. By default history goes to
`<vault>/Google Keep/Zakupy/` (directory configurable via `zakupy_dir`).

### Server-side sync (optional)

If you have an always-on server, history sync can run there (cron) while the local machine
only pulls the ready files: `listonic sync-history --pull-only`. The connection is read
from `~/.mikrus/config.json`; when it's missing, the pull step is silently skipped.

## CLI commands

```bash
listonic lists [--checked|--unchecked] [--json]
listonic add    "<list>" "<item>"
listonic check  "<list>" "<item>" [--uncheck]
listonic remove "<list>" "<item>"
listonic sync-history [--prune] [--pull-only]
listonic popular [--top N] [--json]
listonic stats [--json]
```

## Security

- Credentials and tokens are kept only in `~/.listonic/config.json`, **never in the repo**.
- The plugin contains none of your keys. `CLIENT_ID`/`CLIENT_SECRET` in the code are the
  Listonic app's OAuth client constants (required for the API to respond) — they are not
  account credentials.
- Write operations (`add`/`check`/`remove`, `--prune`) modify real lists — the
  `listonic-edit` skill asks for confirmation before writing.

## License

MIT — see [LICENSE](LICENSE).
