from typing import Literal, NamedTuple, TypedDict

from fivetran import Bib
from http_client import HttpClient


class Login(NamedTuple):
    access_token: str
    session_id: str


class BiblioCommonsUser(TypedDict):
    name: str
    user_id: str
    user_pin: str
    account_id: str
    type: Literal["BiblioCommons"]


class BiblioCommonsProcessor:
    def __init__(self, user: BiblioCommonsUser, old_count: int):
        self.user = user
        self.login_details = self._login()
        self.page = 1
        self.bibs: list[Bib] = []
        self.count = 0
        self.old_count = old_count
        print(f"Processing {self.user['name']} {self.user['type']} ...")

    def process_user(self) -> tuple[list[Bib], int]:
        while True:
            data = self._get_data()
            processed_data, pagination = self._handle_response(data)
            self.count = pagination["count"]
            if pagination["count"] == self.old_count:
                print("No new data")
                break
            self.bibs.extend(processed_data)
            print(pagination)
            if pagination["page"] == pagination["pages"]:
                break
            self.page += 1

        return self.bibs, self.count

    def _handle_response(self, data) -> tuple[list[Bib], dict]:
        entities = data["entities"]
        bibs = entities["bibs"]
        borrowing_history = entities["borrowingHistory"]
        checked_outs = {}
        for b in borrowing_history.values():
            checked_outs[b["metadataId"]] = {
                "checkedoutDate": b["checkedoutDate"],
                "metadataId": b["metadataId"],
                "id": b["id"],
            }
        pagination = data["borrowing"]["borrowingHistory"]["pagination"]

        processed_data: list[Bib] = []

        for k, bib in bibs.items():
            processed_data.append(
                {
                    "title": bib["briefInfo"]["title"],
                    "authors": "; ".join(bib["briefInfo"]["authors"]),
                    "format": bib["briefInfo"]["format"],
                    "checkedout_date": checked_outs[k]["checkedoutDate"],
                    "metadata_id": checked_outs[k]["metadataId"],
                    "id": checked_outs[k]["id"],
                    "person": self.user["name"],
                }
            )

        return processed_data, pagination

    def _get_data(self) -> dict:
        headers = {
            "X-Access-Token": self.login_details.access_token,
            "X-Session-Id": self.login_details.session_id,
        }

        params = {
            "accountId": self.user["account_id"],
            "page": str(self.page),
            "locale": "en-US",
        }

        http_client = HttpClient()
        response = http_client.get(
            "https://gateway.bibliocommons.com/v2/libraries/ssfpl/borrowinghistory",  # noqa E501
            params=params,
            headers=headers,
        )
        if not response.ok:
            print(response.text)
            raise Exception("BiblioCommons API request failed")
        return response.json()

    def _login(self) -> Login:
        login_url = "https://ssfpl.bibliocommons.com/user/login"
        payload = {
            "utf8": "✓",
            "name": self.user["user_id"],
            "user_pin": self.user["user_pin"],
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        http_client = HttpClient()
        response = http_client.post(login_url, data=payload, headers=headers)

        if response.ok:
            return Login(
                access_token=http_client.s.cookies.get("bc_access_token"),
                session_id=http_client.s.cookies.get("session_id"),
            )
        else:
            print(response.text)
            raise Exception("Bibliocommons login failed")
