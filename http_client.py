import requests

from requests.adapters import HTTPAdapter, Retry


class HttpClient:
    def __init__(self):
        self.s = requests.Session()
        retries = Retry(total=3, backoff_factor=2)
        self.s.mount("https://", HTTPAdapter(max_retries=retries))
        self.s.mount("http://", HTTPAdapter(max_retries=retries))

    def get(self, url: str, *, params=None, headers=None):
        return self.s.get(url, params=params, headers=headers)

    def post(self, url: str, *, params=None, data=None, headers=None):
        return self.s.post(url, data=data, headers=headers, params=params)
