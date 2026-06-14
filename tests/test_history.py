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

def test_popular_counts_and_sorts(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    (tmp_path / "logged.json").write_text(
        '{"1": {"name": "Mleko"}, "2": {"name": "mleko"}, "3": {"name": "Chleb"}}',
        encoding="utf-8")
    out = history.popular(top=5)
    assert out[0] == ("mleko", 2)
    assert ("chleb", 1) in out

def test_write_popular_note(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    (tmp_path / "logged.json").write_text('{"1": {"name": "Mleko"}}', encoding="utf-8")
    history.write_popular_note(vault=str(tmp_path))
    note = (tmp_path / "Google Keep" / "Zakupy" / "Popularne produkty.md").read_text(encoding="utf-8")
    assert "Mleko" in note

def test_stats_summary(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    (tmp_path / "logged.json").write_text(
        '{"1": {"name": "Mleko", "date": "2026-06-10"}, '
        '"2": {"name": "mleko", "date": "2026-06-14"}}', encoding="utf-8")
    s = history.stats()
    assert s["total"] == 2
    assert s["distinct"] == 1
    assert s["first"] == "2026-06-10" and s["last"] == "2026-06-14"
