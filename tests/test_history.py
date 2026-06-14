from listonic import history, config

class FakeClient:
    def __init__(self, lists):
        self._lists = lists
    def get_lists(self, include_items=True):
        return self._lists

def _patch_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOGGED_ITEMS_FILE", tmp_path / "logged.json")
    monkeypatch.setattr(history, "LOGGED_ITEMS_FILE", tmp_path / "logged.json")

def test_sync_logs_only_checked(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    client = FakeClient([{"Name": "Spożywcze", "Items": [
        {"Id": "1", "Name": "Mleko", "Checked": 1},
        {"Id": "2", "Name": "Chleb", "Checked": 0},
    ]}])
    new = history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    assert new == ["Mleko"]
    daily = (tmp_path / "Google Keep" / "Zakupy" / "historia" / "2026-06-14.md").read_text(encoding="utf-8")
    assert "- Mleko" in daily

def test_sync_dedup_same_item(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    client = FakeClient([{"Name": "L", "Items": [{"Id": "1", "Name": "Mleko", "Checked": 1}]}])
    history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    second = history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    assert second == []
