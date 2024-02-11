import json
import os
from bibliocommons import BiblioCommonsProcessor, BiblioCommonsUser
from fivetran import Bib, State, to_fivetran_response
from flask import Response  # type: ignore

from libby import LibbyProcessor, LibbyUser

User = LibbyUser | BiblioCommonsUser


def main(request) -> Response:
    credentials: list[User] = json.loads(os.environ["LIBRARY_CREDENTIALS"])
    processed_data: list[Bib] = []
    state: State = {"Libby": {}, "BiblioCommons": {}}
    for user in credentials:
        if user["type"] == "Libby":
            data, count = LibbyProcessor(user).process_user()
            processed_data.extend(data)
            state[user["type"]][user["name"]] = count
        elif user["type"] == "BiblioCommons":
            data, count = BiblioCommonsProcessor(user).process_user()
            processed_data.extend(data)

    fivetran_response = to_fivetran_response(processed_data, state)

    return Response(json.dumps(fivetran_response), mimetype="application/json")
