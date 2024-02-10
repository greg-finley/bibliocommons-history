import json
import os
from bibliocommons import BiblioCommonsProcessor, BiblioCommonsUser
from fivetran import Bib, to_fivetran_response
from flask import Response  # type: ignore

from libby import LibbyProcessor, LibbyUser

User = LibbyUser | BiblioCommonsUser


def main(request) -> Response:
    credentials: list[User] = json.loads(os.environ["LIBRARY_CREDENTIALS"])
    processed_data: list[Bib] = []
    for user in credentials:
        if user["type"] == "Libby":
            processed_data.extend(LibbyProcessor(user).process_user())
        elif user["type"] == "BiblioCommons":
            processed_data.extend(BiblioCommonsProcessor(user).process_user())

    fivetran_response = to_fivetran_response(processed_data)

    return Response(json.dumps(fivetran_response), mimetype="application/json")
