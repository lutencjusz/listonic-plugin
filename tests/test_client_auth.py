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
