import responses
from listonic import const
from listonic.client import ListonicClient

BASE = const.API_BASE_URL + const.LISTS_ENDPOINT

@responses.activate
def test_add_item_posts_name():
    responses.add(responses.POST, BASE + "/3/items", json={"Id": "11", "Name": "Jajka"}, status=201)
    client = ListonicClient(config={"access_token": "t"}, persist=False)
    out = client.add_item("3", "Jajka")
    assert out["Name"] == "Jajka"
    import json as _j
    assert _j.loads(responses.calls[0].request.body)["Name"] == "Jajka"

@responses.activate
def test_set_checked_patches_flag():
    responses.add(responses.PATCH, BASE + "/3/items/11", json={"Id": "11", "Checked": 1}, status=200)
    client = ListonicClient(config={"access_token": "t"}, persist=False)
    client.set_checked("3", "11", True)
    import json as _j
    assert _j.loads(responses.calls[0].request.body)["Checked"] == 1

@responses.activate
def test_remove_item_deletes():
    responses.add(responses.DELETE, BASE + "/3/items/11", status=204)
    client = ListonicClient(config={"access_token": "t"}, persist=False)
    assert client.remove_item("3", "11") is None
