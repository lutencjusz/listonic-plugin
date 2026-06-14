import responses
from listonic import const
from listonic.client import ListonicClient, ListonicError
import pytest

LOGIN_URL = const.API_BASE_URL + const.LOGIN_ENDPOINT

@responses.activate
def test_login_stores_tokens():
    responses.add(responses.POST, LOGIN_URL,
                  json={"access_token": "tok", "refresh_token": "ref"}, status=200)
    cfg = {}
    client = ListonicClient(config=cfg, persist=False)
    assert client.login("a@b.pl", "secret") is True
    assert cfg["access_token"] == "tok"
    assert cfg["refresh_token"] == "ref"
    sent = responses.calls[0].request
    assert "clientauthorization" in {k.lower() for k in sent.headers}

@responses.activate
def test_login_bad_credentials_raises():
    responses.add(responses.POST, LOGIN_URL, json={"error": "invalid"}, status=400)
    with pytest.raises(ListonicError):
        ListonicClient(config={}, persist=False).login("a@b.pl", "x")

# dopisz do tests/test_client_auth.py
from listonic import const as _c
ITEMS_URL = _c.API_BASE_URL + _c.LISTS_ENDPOINT + "/5/items"

@responses.activate
def test_request_retries_after_refresh_on_401():
    responses.add(responses.GET, ITEMS_URL, json={"error": "expired"}, status=401)
    responses.add(responses.POST, LOGIN_URL, json={"access_token": "new"}, status=200)
    responses.add(responses.GET, ITEMS_URL, json=[{"Id": "1"}], status=200)
    client = ListonicClient(config={"access_token": "old", "refresh_token": "ref"},
                            persist=False)
    out = client._request("GET", _c.LISTS_ENDPOINT + "/5/items")
    assert out == [{"Id": "1"}]
    assert client._token == "new"

@responses.activate
def test_refresh_without_token_raises():
    client = ListonicClient(config={}, persist=False)
    with pytest.raises(ListonicError):
        client._refresh()
