import json
import os
from bibliocommons import BiblioCommonsProcessor, BiblioCommonsUser
from fivetran import Bib, to_fivetran_response
from flask import Response  # type: ignore

from libby import LibbyProcessor, LibbyUser
from mysql import MySQLClient

User = LibbyUser | BiblioCommonsUser


def main(request) -> Response:
    credentials: list[User] = json.loads(os.environ["LIBRARY_CREDENTIALS"])
    mysql_client = MySQLClient()
    latest_counts = mysql_client.get_latest_counts()
    processed_data: list[Bib] = []
    for user in credentials:
        if user["type"] == "Libby":
            data, new_count = LibbyProcessor(user, latest_counts).process_user()
            processed_data.extend(data)
            mysql_client.upsert_count(user, new_count)
        elif user["type"] == "BiblioCommons":
            data, new_count = BiblioCommonsProcessor(user, latest_counts).process_user()
            processed_data.extend(data)
            mysql_client.upsert_count(user, new_count)

    fivetran_response = to_fivetran_response(processed_data)
    mysql_client.close()

    return Response(json.dumps(fivetran_response), mimetype="application/json")
