import responses, pytest
from listonic import const
from listonic.client import ListonicClient, ListonicError, normalize_item

LISTS_URL = const.API_BASE_URL + const.LISTS_ENDPOINT

def test_normalize_item_checked_int():
    out = normalize_item({"Id": "9", "Name": "Mleko", "Checked": 1, "Amount": "2", "Unit": "l"})
    assert out == {"id": "9", "name": "Mleko", "checked": True, "amount": "2", "unit": "l"}

def test_normalize_item_unchecked_default():
    out = normalize_item({"IdAsNumber": 3, "Name": "Chleb"})
    assert out["id"] == "3" and out["checked"] is False

@responses.activate
def test_get_lists_returns_payload():
    responses.add(responses.GET, LISTS_URL, json=[{"Id": "1", "Name": "Spożywcze"}], status=200)
    client = ListonicClient(config={"access_token": "t"}, persist=False)
    assert client.get_lists()[0]["Name"] == "Spożywcze"

@responses.activate
def test_find_list_case_insensitive():
    responses.add(responses.GET, LISTS_URL, json=[{"Id": "7", "Name": "Spożywcze"}], status=200)
    client = ListonicClient(config={"access_token": "t"}, persist=False)
    assert client.find_list("spożywcze")["Id"] == "7"

@responses.activate
def test_find_list_missing_raises():
    responses.add(responses.GET, LISTS_URL, json=[], status=200)
    client = ListonicClient(config={"access_token": "t"}, persist=False)
    with pytest.raises(ListonicError):
        client.find_list("Brak")
