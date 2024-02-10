import datetime
from typing import TypedDict


class Bib(TypedDict):
    title: str
    authors: str
    format: str
    checkedout_date: str
    metadata_id: str
    id: str
    person: str


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
