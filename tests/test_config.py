from listonic import config

def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    config.save_config({"access_token": "abc", "vault_path": "X"})
    assert config.load_config()["access_token"] == "abc"

def test_load_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "nope.json")
    assert config.load_config() == {}
