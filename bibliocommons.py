from typing import Literal, NamedTuple, TypedDict

import requests
from fivetran import Bib


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
    def __init__(self, user: BiblioCommonsUser):
        self.user = user
        self.login_details = self._login()
        self.page = 1
        self.bibs: list[Bib] = []

    def process_user(self) -> list[Bib]:
        while True:
            data = self._get_data()
            processed_data, pagination = self._handle_response(data)
            self.bibs.extend(processed_data)
            print(pagination)
            if pagination["page"] == pagination["pages"]:
                break
            self.page += 1

        return self.bibs

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

        response = requests.get(
            "https://gateway.bibliocommons.com/v2/libraries/ssfpl/borrowinghistory",  # noqa E501
            params=params,
            headers=headers,
        )
        if not response.ok:
            raise Exception("BiblioCommons API request failed")
        return response.json()

    def _login(self) -> Login:
        s = requests.Session()
        login_url = "https://ssfpl.bibliocommons.com/user/login"
        payload = {
            "utf8": "✓",
            "name": self.user["user_id"],
            "user_pin": self.user["user_pin"],
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = s.post(login_url, data=payload, headers=headers)

        if response.ok:
            return Login(
                access_token=s.cookies.get("bc_access_token"),
                session_id=s.cookies.get("session_id"),
            )
        else:
            raise Exception("Bibliocommons login failed")
