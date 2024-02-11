from typing import TypedDict


class Bib(TypedDict):
    title: str
    authors: str
    format: str
    checkedout_date: str
    metadata_id: str
    id: str
    person: str


State = dict[str, dict[str, int]]


def to_fivetran_response(bibs: list[Bib], state: State) -> dict:
    # https://fivetran.com/docs/functions/google-cloud-functions#responseformat
    return {
        "state": state,
        "insert": {
            "borrowing": bibs,
        },
        "hasMore": False,
        "schema": {"borrowing": {"primary_key": ["id"]}},
    }
