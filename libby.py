import datetime
from typing import Literal, TypedDict

import requests

from fivetran import Bib
from utils import chunkList


class LibbyUser(TypedDict):
    name: str
    card_id: str
    token: str
    type: Literal["Libby"]


class LibbyProcessor:
    def __init__(self, user: LibbyUser, old_count: int):
        self.user = user
        self.page = 1
        self.has_more = True
        self.acts: list[dict] = []
        self.bibs: list[Bib] = []
        self.count = 0
        self.old_count = old_count
        print(f"Processing {self.user['name']} {self.user['type']} ...")

    def process_user(self) -> tuple[list[Bib], int]:
        while self.has_more:
            self._get_acts()

        chunked_acts = list(chunkList(self.acts, 50))
        for chunk in chunked_acts:
            self._process_act_chunk(chunk)

        return self.bibs, self.count

    def _get_acts(self) -> None:
        response = requests.get(
            f'https://sentry-read.svc.overdrive.com/chip/migrating/{self.user["card_id"]}/history?page={self.page}',
            headers={
                "Authorization": f"Bearer {self.user['token']}",
                "Accept": "application/json",
            },
        )
        if not response.ok:
            print(response.text)
            raise Exception("Libby API acts request failed")
        data = response.json()
        print(
            "page: ",
            data["page"],
            "pages: ",
            data["pages"],
            "total: ",
            data["total"],
        )
        self.count = data["total"]
        if self.old_count == data["total"]:
            self.has_more = False
            print("No new data")
            return
        self.acts.extend(data["acts"])
        if data["pages"] == self.page:
            self.has_more = False
        self.page += 1

    def _process_act_chunk(self, chunk: list[dict]) -> None:
        # curl 'https://thunder.api.overdrive.com/v2/media/bulk?titleIds=3940089,9598953,6133422,301511,1272309,4729922,9476284,1154606&x-client-id=dewey'
        response = requests.get(
            f"https://thunder.api.overdrive.com/v2/media/bulk?titleIds={','.join([str(i['titleId']) for i in chunk])}&x-client-id=dewey",
        )
        if not response.ok:
            print(response.text)
            raise Exception("Libby API bulk request failed")
        for i in response.json():
            checkedout_date = None
            for act in chunk:
                if act["titleId"] == i["id"]:
                    # i.e. 1685200993000
                    checkedout_date = act["createTime"]
                    break
            if not checkedout_date:
                raise Exception("Libby API cannot find act for title")
            self.bibs.append(
                Bib(
                    title=i["title"],
                    authors=(
                        i["creators"][0]["name"]
                        if i["creators"] and len(i["creators"])
                        else ""
                    ),
                    format=i["type"]["id"],
                    checkedout_date=datetime.datetime.fromtimestamp(
                        checkedout_date / 1000
                    )
                    .date()
                    .isoformat(),
                    metadata_id=i["id"],
                    id=i["id"] + "_" + str(checkedout_date),
                    person=self.user["name"],
                )
            )
