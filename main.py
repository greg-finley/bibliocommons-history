import json

with open("/Users/gregoryfinley/Desktop/response.json") as json_file:
    data = json.load(json_file)


bibs = data["entities"]["bibs"]
for i, bib in enumerate(bibs.values()):
    print(
        {
            "title": bib["briefInfo"]["title"],
            "authors": bib["briefInfo"]["authors"],
            "format": bib["briefInfo"]["format"],
        }
    )
