import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".listonic"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOGGED_ITEMS_FILE = CONFIG_DIR / "logged_items.json"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )
