import json
from datetime import date
from pathlib import Path

from .config import load_config, LOGGED_ITEMS_FILE, DEFAULT_VAULT
from .client import normalize_item


def _zakupy_dir(vault: str) -> Path:
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


def sync_history(client, vault=None, today=None) -> list[str]:
    vault = vault or load_config().get("vault_path", DEFAULT_VAULT)
    today = today or date.today().isoformat()
    logged = load_logged()
    new_names = []
    for lst in client.get_lists():
        list_name = lst.get("Name", "")
        items = lst.get("Items") or lst.get("items") or []
        for raw in items:
            item = normalize_item(raw)
            if item["checked"] and item["id"] and item["id"] not in logged:
                logged[item["id"]] = {
                    "name": item["name"], "date": today, "list": list_name,
                }
                new_names.append(item["name"])
    if new_names:
        _write_daily(vault, today, new_names)
        save_logged(logged)
    return new_names
