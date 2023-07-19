import json

with open("/Users/gregoryfinley/Desktop/response.json") as json_file:
    data = json.load(json_file)

entities = data["entities"]
bibs = entities["bibs"]
borrowing_history = entities["borrowingHistory"]
checked_outs = {}
for b in borrowing_history.values():
    checked_outs[b["metadataId"]] = b["checkedoutDate"]
pagination = data["borrowing"]["borrowingHistory"]["pagination"]

for k, bib in bibs.items():
    print(
        {
            "title": bib["briefInfo"]["title"],
            "authors": "; ".join(bib["briefInfo"]["authors"]),
            "format": bib["briefInfo"]["format"],
            "checkedOut": checked_outs[k],
        }
    )

print(pagination)
