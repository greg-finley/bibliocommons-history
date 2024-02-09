import json
import os
import aiohttp
import asyncio
from flask import Response  # type: ignore
from typing import NamedTuple, TypedDict


class Login(NamedTuple):
    access_token: str
    session_id: str


class User(TypedDict):
    name: str
    user_id: str
    user_pin: str
    account_id: str


def main(request) -> Response:
    return asyncio.run(async_main(request))


async def async_main(request) -> Response:
    credentials: list[User] = json.loads(os.environ["LIBRARY_CREDENTIALS"])
    tasks = [process_user(user) for user in credentials]
    processed_data = await asyncio.gather(*tasks)

    return Response(json.dumps(processed_data), mimetype="application/json")


async def process_user(user: User):
    login_details = await login(user)
    i = 1
    all_processed_data = []
    while True:
        data = await get_data(i, login_details, user)
        processed_data, pagination = handle_response(
            data, user
        )  # Assume handle_response is now async or its logic is adapted
        all_processed_data.extend(processed_data)
        if pagination["page"] == pagination["pages"]:
            break
        i += 1
    return all_processed_data


def handle_response(data, user: User):
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
                "person": user["name"],
            }
        )

    return processed_data, pagination


async def get_data(page: int, login: Login, user: User) -> dict:
    headers = {
        "X-Access-Token": login.access_token,
        "X-Session-Id": login.session_id,
    }
    params = {
        "accountId": user["account_id"],
        "page": str(page),
        "locale": "en-US",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://gateway.bibliocommons.com/v2/libraries/ssfpl/borrowinghistory",
            params=params,
            headers=headers,
        ) as response:
            return await response.json()


async def login(user: User) -> Login:
    async with aiohttp.ClientSession() as session:
        login_url = "https://ssfpl.bibliocommons.com/user/login"
        payload = {
            "utf8": "✓",
            "name": user["user_id"],
            "user_pin": user["user_pin"],
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with session.post(login_url, data=payload, headers=headers) as response:
            if response.status == 200:
                cookies = response.cookies
                return Login(
                    access_token=cookies["bc_access_token"].value,
                    session_id=cookies["session_id"].value,
                )
            else:
                raise Exception("Login failed")
