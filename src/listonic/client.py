import base64
import requests

from . import const
from .config import load_config, save_config

_CLIENT_AUTH = base64.b64encode(
    f"{const.CLIENT_ID}:{const.CLIENT_SECRET}".encode()
).decode()


class ListonicError(Exception):
    pass


class ListonicClient:
    def __init__(self, config=None, persist=True):
        self._config = config if config is not None else load_config()
        self._persist = persist
        self._token = self._config.get("access_token")
        self._refresh_token = self._config.get("refresh_token")

    def _persist_tokens(self):
        self._config["access_token"] = self._token
        self._config["refresh_token"] = self._refresh_token
        if self._persist:
            save_config(self._config)

    def login(self, email: str, password: str) -> bool:
        url = const.API_BASE_URL + const.LOGIN_ENDPOINT
        params = {"provider": "password", "autoMerge": "1", "autoDestruct": "1"}
        data = {
            "username": email,
            "password": password,
            "client_id": const.CLIENT_ID,
            "client_secret": const.CLIENT_SECRET,
            "redirect_uri": const.REDIRECT_URI,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "clientauthorization": f"Bearer {_CLIENT_AUTH}",
        }
        resp = requests.post(url, params=params, data=data, headers=headers,
                             timeout=const.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise ListonicError(f"Logowanie nieudane (HTTP {resp.status_code})")
        body = resp.json()
        self._token = body.get("access_token")
        self._refresh_token = body.get("refresh_token")
        if not self._token:
            raise ListonicError("Brak access_token w odpowiedzi logowania")
        self._persist_tokens()
        return True

    def _refresh(self):
        if not self._refresh_token:
            raise ListonicError("Brak refresh_token — uruchom `listonic login`")
        url = const.API_BASE_URL + const.LOGIN_ENDPOINT
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": const.CLIENT_ID,
            "client_secret": const.CLIENT_SECRET,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "clientauthorization": f"Bearer {_CLIENT_AUTH}",
        }
        resp = requests.post(url, data=data, headers=headers,
                             timeout=const.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise ListonicError("Odświeżenie tokenu nieudane — uruchom `listonic login`")
        body = resp.json()
        self._token = body.get("access_token")
        if body.get("refresh_token"):
            self._refresh_token = body["refresh_token"]
        self._persist_tokens()

    def _headers(self):
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _request(self, method: str, path: str, _retried: bool = False, **kwargs):
        url = const.API_BASE_URL + path
        resp = requests.request(method, url, headers=self._headers(),
                                timeout=const.REQUEST_TIMEOUT, **kwargs)
        if resp.status_code == 401 and not _retried:
            self._refresh()
            return self._request(method, path, _retried=True, **kwargs)
        if resp.status_code not in (200, 201, 204):
            raise ListonicError(f"Błąd API {method} {path}: HTTP {resp.status_code}")
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()
