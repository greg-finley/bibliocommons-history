import json
import os
import requests
import datetime
from flask import Response  # type: ignore
from typing import Literal, NamedTuple, TypedDict


class Login(NamedTuple):
    access_token: str
    session_id: str


class LibbyUser(TypedDict):
    user_id: str
    type: Literal["Libby"]


class BiblioCommonsUser(TypedDict):
    name: str
    user_id: str
    user_pin: str
    account_id: str
    type: Literal["BiblioCommons"]


User = LibbyUser | BiblioCommonsUser


class Bib(TypedDict):
    title: str
    authors: str
    format: str
    checkedout_date: str
    metadata_id: str
    id: str
    person: str


def main(request) -> Response:
    credentials: list[User] = json.loads(os.environ["LIBRARY_CREDENTIALS"])
    processed_data: list[Bib] = []
    for user in credentials:
        if user["type"] == "Libby":
            processed_data.extend(process_libby_user(user))
        elif user["type"] == "BiblioCommons":
            processed_data.extend(process_bibliocommons_user(user))

    fivetran_response = to_fivetran_response(processed_data)

    return Response(json.dumps(fivetran_response), mimetype="application/json")


def process_bibliocommons_user(user: BiblioCommonsUser) -> list[Bib]:
    login_details = login(user)
    i = 1
    all_processed_data: list[Bib] = []
    while True:
        data = get_data(i, login_details, user)
        processed_data, pagination = handle_response(data, user)
        all_processed_data.extend(processed_data)
        print(pagination)
        if pagination["page"] == pagination["pages"]:
            break
        i += 1

    return all_processed_data


def process_libby_user(user: LibbyUser) -> list[Bib]:
    response = requests.get(
        f"https://share.libbyapp.com/data/{user['user_id']}/libbytimeline-all-loans.json"
    )
    if not response.ok:
        raise Exception("Libby API request failed")
    return [
        Bib(
            title=i["title"]["text"],
            authors=i["author"],
            format=i["cover"]["format"],
            # like 1707508484000 but needs to be like "2024-02-04"
            checkedout_date=datetime.datetime.fromtimestamp(
                i["timestamp"] / 1000
            ).isoformat(),
            metadata_id=i["isbn"],
            id=i["isbn"] + str(i["timestamp"]),
            person=user["user_id"],
        )
        for i in response.json()["timeline"]
    ]


def handle_response(data, user: BiblioCommonsUser) -> tuple[list[Bib], dict]:
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
                "person": user["name"],
            }
        )

    return processed_data, pagination


def get_data(page: int, login: Login, user: BiblioCommonsUser) -> dict:
    headers = {
        "X-Access-Token": login.access_token,
        "X-Session-Id": login.session_id,
    }

    params = {
        "accountId": user["account_id"],
        "page": str(page),
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


def login(user: BiblioCommonsUser) -> Login:
    s = requests.Session()
    login_url = "https://ssfpl.bibliocommons.com/user/login"
    payload = {
        "utf8": "✓",
        "name": user["user_id"],
        "user_pin": user["user_pin"],
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


def to_fivetran_response(bibs: list[Bib]) -> dict:
    # https://fivetran.com/docs/functions/google-cloud-functions#responseformat
    return {
        "state": {
            "borrowing": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "insert": {
            "borrowing": bibs,
        },
        "hasMore": False,
        "schema": {"borrowing": {"primary_key": ["id"]}},
    }
