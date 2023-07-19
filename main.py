from dotenv import load_dotenv
import os
import requests
import csv

load_dotenv()


def main():
    i = 1
    all_processed_data = []
    while True:
        data = get_data(i)
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


def get_data(page):
    url = f"https://gateway.bibliocommons.com/v2/libraries/ssfpl/borrowinghistory?accountId={os.environ['ACCOUNT_ID']}&page={page}&locale=en-US"  # noqa
    headers = {
        "X-Access-Token": os.environ["X_ACCESS_TOKEN"],
        "X-Session-Id": os.environ["X_SESSION_ID"],
    }
    response = requests.get(url, headers=headers)
    return response.json()


if __name__ == "__main__":
    main()
