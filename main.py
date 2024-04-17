import json
import os
from bibliocommons import BiblioCommonsProcessor, BiblioCommonsUser
from fivetran import Bib, State, to_fivetran_response
from flask import Response  # type: ignore

from libby import LibbyProcessor, LibbyUser

User = LibbyUser | BiblioCommonsUser


def main(request) -> Response:
    request_json = request.get_json(silent=True)
    old_state = (
        request_json.get("state", {})
        if request_json and "state" in request_json
        else {}
    )
    print(f"Old state: {old_state}")
    credentials: list[User] = json.loads(os.environ["LIBRARY_CREDENTIALS"])
    processed_data: list[Bib] = []
    state: State = {"Libby": {}, "BiblioCommons": {}}
    for user in credentials:
        if user["type"] == "Libby":
            pass
            # old_count = old_state.get("Libby", {}).get(user["name"], 0)
            # data, count = LibbyProcessor(user, old_count).process_user()
            # processed_data.extend(data)
            # state["Libby"][user["name"]] = count
        elif user["type"] == "BiblioCommons":
            old_count = old_state.get("BiblioCommons", {}).get(user["name"], 0)
            data, count = BiblioCommonsProcessor(user, old_count).process_user()
            processed_data.extend(data)
            state["BiblioCommons"][user["name"]] = count

    print(f"New state: {state}")
    print(f"Number of processed records: {len(processed_data)}")
    fivetran_response = to_fivetran_response(processed_data, state)

    return Response(json.dumps(fivetran_response), mimetype="application/json")
