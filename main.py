from dotenv import load_dotenv
import os
import requests
import csv
from typing import NamedTuple

load_dotenv()


class Login(NamedTuple):
    access_token: str
    session_id: str


def main():
    login_details = login()
    i = 1
    all_processed_data = []
    while True:
        data = get_data(i, login_details)
        processed_data, pagination = handle_response(data)
        all_processed_data.extend(processed_data)
        print(pagination)
        if pagination["page"] == pagination["pages"]:
            break
        i += 1

    write_to_csv(all_processed_data)


def handle_response(data):
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

    processed_data = []

    for k, bib in bibs.items():
        processed_data.append(
            {
                "title": bib["briefInfo"]["title"],
                "authors": "; ".join(bib["briefInfo"]["authors"]),
                "format": bib["briefInfo"]["format"],
                "checkedoutDate": checked_outs[k]["checkedoutDate"],
                "metadataId": checked_outs[k]["metadataId"],
                "id": checked_outs[k]["id"],
                "person": os.environ["PERSON"],
            }
        )

    return processed_data, pagination


def write_to_csv(processed_data):
    with open("data.csv", "w") as csvfile:
        fieldnames = [
            "title",
            "authors",
            "format",
            "checkedoutDate",
            "metadataId",
            "id",
            "person",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in processed_data:
            writer.writerow(row)


def get_data(page: int, login: Login) -> dict:
    headers = {
        "X-Access-Token": login.access_token,
        "X-Session-Id": login.session_id,
    }

    params = {
        "accountId": os.environ["ACCOUNT_ID"],
        "page": str(page),
        "locale": "en-US",
    }

    response = requests.get(
        "https://gateway.bibliocommons.com/v2/libraries/ssfpl/borrowinghistory",  # noqa E501
        params=params,
        headers=headers,
    )
    return response.json()


def login() -> Login:
    s = requests.Session()
    login_url = "https://ssfpl.bibliocommons.com/user/login"
    payload = {
        "utf8": "✓",
        "name": os.environ["USER_ID"],
        "user_pin": os.environ["USER_PIN"],
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
        raise Exception("Login failed")


if __name__ == "__main__":
    main()
