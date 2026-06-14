import json
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from .config import load_config, LOGGED_ITEMS_FILE
from .client import normalize_item, ListonicError

MIKRUS_CONFIG = Path.home() / ".mikrus" / "config.json"
DEFAULT_MIKRUS_REMOTE = "/root/listonic-data"


def _resolve_vault(vault=None) -> str:
    """Ścieżka do vaultu Obsidian, do którego zrzucana jest historia zakupów.
    Brak twardego domyślnego — ustaw `vault_path` w ~/.listonic/config.json."""
    vault = vault or load_config().get("vault_path")
    if not vault:
        raise ListonicError(
            "Brak vault_path w ~/.listonic/config.json — ustaw ścieżkę do vaultu "
            'Obsidian, np. {"vault_path": "/sciezka/do/Vault"}.'
        )
    return vault


def _zakupy_dir(vault: str) -> Path:
    # Na Mikrusie nie ma vaultu — pozwalamy nadpisać katalog Zakupy płaską
    # ścieżką (config.zakupy_dir), żeby uniknąć spacji w ścieżkach przy scp.
    override = load_config().get("zakupy_dir")
    if override:
        return Path(override)
    return Path(vault) / "Google Keep" / "Zakupy"


def load_logged() -> dict:
    if LOGGED_ITEMS_FILE.exists():
        return json.loads(LOGGED_ITEMS_FILE.read_text(encoding="utf-8"))
    return {}


def save_logged(state: dict) -> None:
    LOGGED_ITEMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOGGED_ITEMS_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _write_daily(vault: str, day: str, names: list[str]) -> None:
    d = _zakupy_dir(vault) / "historia"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{day}.md"
    if f.exists():
        existing = f.read_text(encoding="utf-8")
    else:
        existing = (
            f"---\ndescription: Odhaczone pozycje zakupów {day}\n"
            f"tags:\n  - listonic\n  - zakupy\n---\n\n# Zakupy {day}\n\n"
        )
    body = "".join(f"- {n}\n" for n in names)
    f.write_text(existing + body, encoding="utf-8")


def popular(top: int = 20) -> list[tuple[str, int]]:
    logged = load_logged()
    counts: dict[str, int] = {}
    for entry in logged.values():
        name = entry.get("name", "").strip().lower()
        if name:
            counts[name] = counts.get(name, 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top]


_POPULAR_HEADER = "# Popularne produkty"


def _extract_intro(text: str) -> str:
    """Zachowaj ręczny akapit intro między nagłówkiem a pierwszą pozycją listy
    (np. wikilink do [[Plugin Listonic]]), żeby regeneracja go nie kasowała."""
    lines = text.splitlines()
    try:
        start = lines.index(_POPULAR_HEADER) + 1
    except ValueError:
        return ""
    intro: list[str] = []
    for ln in lines[start:]:
        if ln.startswith("- "):
            break
        intro.append(ln)
    return "\n".join(intro).strip()


def write_popular_note(vault=None, top: int = 20) -> Path:
    vault = _resolve_vault(vault)
    rows = popular(top=top)
    d = _zakupy_dir(vault)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "Popularne produkty.md"
    intro = _extract_intro(f.read_text(encoding="utf-8")) if f.exists() else ""
    lines = [
        "---", "description: Najczęściej kupowane produkty (z historii Listonic)",
        "tags:", "  - listonic", "  - zakupy", "---", "",
        _POPULAR_HEADER, "",
    ]
    if intro:
        lines += [intro, ""]
    for name, count in rows:
        lines.append(f"- {name.capitalize()} — {count}×")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f


def stats() -> dict:
    logged = load_logged()
    names = {e.get("name", "").strip().lower() for e in logged.values() if e.get("name")}
    dates = sorted(e["date"] for e in logged.values() if e.get("date"))
    return {
        "total": len(logged),
        "distinct": len(names),
        "first": dates[0] if dates else None,
        "last": dates[-1] if dates else None,
    }


DEFAULT_PRUNE_LIST = "Najbliższe zakupy"


def sync_history(client, vault=None, today=None, prune=False, prune_list=None) -> dict:
    vault = _resolve_vault(vault)
    today = today or date.today().isoformat()
    lists = client.get_lists()
    logged = load_logged()
    new_names = []
    for lst in lists:
        list_name = lst.get("Name", "")
        items = lst.get("Items") or lst.get("items") or []
        for raw in items:
            item = normalize_item(raw)
            if item["checked"] and item["id"] and item["id"] not in logged:
                logged[item["id"]] = {
                    "name": item["name"], "date": today, "list": list_name,
                }
                new_names.append(item["name"])
    # Historię zapisujemy PRZED usuwaniem — żaden zakup nie ginie, jeśli prune padnie.
    if new_names:
        _write_daily(vault, today, new_names)
        save_logged(logged)

    pruned = []
    if prune:
        if prune_list is None:
            prune_list = load_config().get("prune_list", DEFAULT_PRUNE_LIST)
        target = prune_list.strip().lower()
        for lst in lists:
            if lst.get("Name", "").strip().lower() != target:
                continue
            list_id = str(lst.get("Id", lst.get("IdAsNumber", "")))
            for raw in (lst.get("Items") or lst.get("items") or []):
                item = normalize_item(raw)
                # Usuwamy tylko to, co jest już bezpiecznie w historii.
                if item["checked"] and item["id"] and item["id"] in logged:
                    client.remove_item(list_id, item["id"])
                    pruned.append(item["name"])

    return {"logged": new_names, "pruned": pruned}


# --- Pull z Mikrusa -------------------------------------------------------
# Sync historii biegnie na Mikrusie (always-on). Tu ściągamy gotowe pliki
# dzienne do vaultu na Windows. Połączenie bierzemy z ~/.mikrus/config.json.


def merge_daily_content(existing, incoming: str) -> str:
    """Scal dwie wersje pliku dziennego: zachowaj nagłówek istniejącego,
    dołącz brakujące pozycje (linie ``- ...``). Bez duplikatów."""
    def bullets(text: str) -> list[str]:
        return [ln for ln in text.splitlines() if ln.startswith("- ")]

    if not existing:
        return incoming if incoming.endswith("\n") else incoming + "\n"
    have = set(bullets(existing))
    add = [ln for ln in bullets(incoming) if ln not in have]
    base = existing if existing.endswith("\n") else existing + "\n"
    if not add:
        return base
    return base + "".join(ln + "\n" for ln in add)


def _mikrus_conn():
    if not MIKRUS_CONFIG.exists():
        return None
    try:
        cfg = json.loads(MIKRUS_CONFIG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if all(cfg.get(k) for k in ("host", "sshPort", "user", "identityFile")):
        return cfg
    return None


def pull_from_mikrus(vault=None, remote_dir=None) -> dict:
    """Ściągnij pliki historii wygenerowane na Mikrusie do vaultu.

    Zwraca {"available": bool, "files": [...], "items": int}. Gdy brak
    konfiguracji Mikrusa (np. uruchomione NA Mikrusie) — cicho pomija.
    """
    conn = _mikrus_conn()
    if conn is None:
        return {"available": False, "files": [], "items": 0}
    vault = _resolve_vault(vault)
    remote_dir = remote_dir or load_config().get("mikrus_remote_dir", DEFAULT_MIKRUS_REMOTE)
    target = f"{conn['user']}@{conn['host']}"
    port = str(conn["sshPort"])
    key = conn["identityFile"]
    ssh_base = ["ssh", "-p", port, "-i", key, "-o", "BatchMode=yes", target]
    scp_base = ["scp", "-P", port, "-i", key, "-o", "BatchMode=yes"]

    r = subprocess.run(
        ssh_base + [f"ls -1 {remote_dir}/historia/*.md 2>/dev/null"],
        capture_output=True, text=True, timeout=60,
    )
    remote_files = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    if not remote_files:
        return {"available": True, "files": [], "items": 0}

    pulled: list[str] = []
    new_items = 0
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            scp_base + ["-r", f"{target}:{remote_dir}/historia", tmp],
            capture_output=True, text=True, timeout=120, check=True,
        )
        local_hist = _zakupy_dir(vault) / "historia"
        local_hist.mkdir(parents=True, exist_ok=True)
        for f in sorted(Path(tmp, "historia").glob("*.md")):
            incoming = f.read_text(encoding="utf-8")
            dest = local_hist / f.name
            existing = dest.read_text(encoding="utf-8") if dest.exists() else None
            dest.write_text(merge_daily_content(existing, incoming), encoding="utf-8")
            pulled.append(f.name)

        li = Path(tmp, "logged_items.json")
        rc = subprocess.run(
            scp_base + [f"{target}:/root/.listonic/logged_items.json", str(li)],
            capture_output=True, text=True, timeout=60,
        )
        if rc.returncode == 0 and li.exists():
            try:
                remote_logged = json.loads(li.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                remote_logged = {}
            local_logged = load_logged()
            before = len(local_logged)
            for k, v in remote_logged.items():
                local_logged.setdefault(k, v)
            new_items = len(local_logged) - before
            save_logged(local_logged)

    write_popular_note(vault)
    subprocess.run(
        ssh_base + [f"rm -f {remote_dir}/historia/*.md"],
        capture_output=True, text=True, timeout=60,
    )
    return {"available": True, "files": pulled, "items": new_items}
