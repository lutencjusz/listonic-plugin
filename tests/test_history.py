from listonic import history, config

class FakeClient:
    def __init__(self, lists):
        self._lists = lists
        self.removed = []
    def get_lists(self, include_items=True):
        return self._lists
    def remove_item(self, list_id, item_id):
        self.removed.append((list_id, item_id))

def _patch_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOGGED_ITEMS_FILE", tmp_path / "logged.json")
    monkeypatch.setattr(history, "LOGGED_ITEMS_FILE", tmp_path / "logged.json")

def test_sync_logs_only_checked(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    client = FakeClient([{"Name": "Spożywcze", "Items": [
        {"Id": "1", "Name": "Mleko", "Checked": 1},
        {"Id": "2", "Name": "Chleb", "Checked": 0},
    ]}])
    res = history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    assert res["logged"] == ["Mleko"]
    daily = (tmp_path / "Google Keep" / "Zakupy" / "historia" / "2026-06-14.md").read_text(encoding="utf-8")
    assert "- Mleko" in daily

def test_sync_dedup_same_item(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    client = FakeClient([{"Name": "L", "Items": [{"Id": "1", "Name": "Mleko", "Checked": 1}]}])
    history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    second = history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    assert second["logged"] == []

def test_prune_deletes_only_target_list(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    client = FakeClient([
        {"Id": "10", "Name": "Najbliższe zakupy", "Items": [
            {"Id": "1", "Name": "Mleko", "Checked": 1},
            {"Id": "2", "Name": "Chleb", "Checked": 0},
        ]},
        {"Id": "20", "Name": "Prezenty", "Items": [
            {"Id": "3", "Name": "Książka", "Checked": 1},
        ]},
    ])
    res = history.sync_history(client, vault=str(tmp_path), today="2026-06-14",
                              prune=True, prune_list="Najbliższe zakupy")
    assert client.removed == [("10", "1")]      # tylko odhaczona z listy docelowej
    assert res["pruned"] == ["Mleko"]
    assert set(res["logged"]) == {"Mleko", "Książka"}

def test_no_prune_does_not_delete(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    client = FakeClient([{"Id": "10", "Name": "Najbliższe zakupy", "Items": [
        {"Id": "1", "Name": "Mleko", "Checked": 1}]}])
    res = history.sync_history(client, vault=str(tmp_path), today="2026-06-14")
    assert client.removed == []
    assert res["pruned"] == []

def test_prune_retries_already_logged(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    (tmp_path / "logged.json").write_text(
        '{"1": {"name": "Mleko", "date": "2026-06-10", "list": "Najbliższe zakupy"}}',
        encoding="utf-8")
    client = FakeClient([{"Id": "10", "Name": "Najbliższe zakupy", "Items": [
        {"Id": "1", "Name": "Mleko", "Checked": 1}]}])
    res = history.sync_history(client, vault=str(tmp_path), today="2026-06-14",
                              prune=True, prune_list="Najbliższe zakupy")
    assert res["logged"] == []                  # już zalogowane, bez ponownego logu
    assert client.removed == [("10", "1")]      # ale i tak usunięte (retry)
    assert res["pruned"] == ["Mleko"]

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

def test_merge_daily_new_file():
    incoming = "# Zakupy\n\n- Mleko\n- Chleb\n"
    assert history.merge_daily_content(None, incoming) == incoming

def test_merge_daily_appends_missing_bullets():
    existing = "---\ndesc\n---\n\n# Zakupy\n\n- Mleko\n"
    incoming = "# Zakupy\n\n- Mleko\n- Chleb\n"
    merged = history.merge_daily_content(existing, incoming)
    assert merged.count("- Mleko") == 1          # bez duplikatu
    assert "- Chleb" in merged
    assert merged.startswith("---")              # nagłówek istniejącego zachowany

def test_merge_daily_no_new_is_noop():
    existing = "# Zakupy\n\n- Mleko\n- Chleb\n"
    incoming = "# Zakupy\n\n- Mleko\n"
    assert history.merge_daily_content(existing, incoming) == existing

def test_write_popular_preserves_intro(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    (tmp_path / "logged.json").write_text('{"1": {"name": "Mleko"}}', encoding="utf-8")
    d = tmp_path / "Google Keep" / "Zakupy"
    d.mkdir(parents=True)
    (d / "Popularne produkty.md").write_text(
        "---\ntags:\n---\n\n# Popularne produkty\n\n"
        "Ranking z [[Plugin Listonic]].\n\n- Stare — 9×\n", encoding="utf-8")
    history.write_popular_note(vault=str(tmp_path))
    note = (d / "Popularne produkty.md").read_text(encoding="utf-8")
    assert "[[Plugin Listonic]]" in note          # intro zachowane
    assert "- Mleko — 1×" in note                 # lista przeliczona
    assert "- Stare — 9×" not in note             # stara lista zastąpiona

def test_stats_summary(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    (tmp_path / "logged.json").write_text(
        '{"1": {"name": "Mleko", "date": "2026-06-10"}, '
        '"2": {"name": "mleko", "date": "2026-06-14"}}', encoding="utf-8")
    s = history.stats()
    assert s["total"] == 2
    assert s["distinct"] == 1
    assert s["first"] == "2026-06-10" and s["last"] == "2026-06-14"
