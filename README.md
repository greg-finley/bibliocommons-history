# biblicommons-history

This function automatically syncs my library borrowing history from Bibliocommons and Libby to Google Sheets, using Google Cloud Functions, Fivetran, and [Mozart Data](https://mozartdata.com/).

<img width="1113" alt="Screen Shot 2024-02-09 at 10 47 25 AM" src="https://github.com/greg-finley/bibliocommons-history/assets/28961086/9bd92dd7-265b-4732-934d-2e69ee44b471">

## Local dev

1. Install [poetry](https://python-poetry.org/docs/#installation) for a Python virtual environment.
2. `poetry install`

## Bibliocommons

1. My local library is the South San Francisco branch, so I log in here: https://ssfpl.bibliocommons.com. The code probably could be adapted to read from other libraries using the Bibliocommons backend.
2. Navigate around to the borrowing history page and capture the `account_id` from one of the request's query params using your browser's dev tools.

## Libby

1. Follow these instructions to export your history as a JSON: https://help.libbyapp.com/en-us/6207.htm
2. You can keep accessing the export link later by the same user_id, but for now you need to manually redo the export to get the data to update

## Google Cloud Function

1. The `.github/workflows/deploy.yml` file deploys this Cloud Function to Google upon merges to the repo `main` branch.
2. Before deploying your function, set a secret in Google Secret Manager called `LIBRARY_CREDENTIALS` in the format `[{"name": "Greg", "account_id": "1234", "user_id": "my_user", "user_pin": "my_pin", "type": "BiblioCommons"}, {"name": "Greg", "user_id": "some_uuid", "type": "Libby"}]`. You can put multiple Bibliocommons or Libby accounts. Make sure to grant access to the Cloud Function to read this secret.

## Fivetran

My Cloud Function returns the data in the shape expected by the [Fivetran Cloud Functions](https://fivetran.com/docs/functions/google-cloud-functions) connector. I am sort of wastefully syncing the whole borrowing history via Fivetran every sync, but the data is a bit weird in that history only shows up when you return a book but it only reports the checkout date, so it's not obvious which records I've already processed unless I kept track myself in another database.

## Mozart Data

Mozart Data sets up Fivetran and Snowflake for you and has a free tier that I can easily stay under for personal projects. After my data landed in Snowflake, I wrote a few Mozart Transforms to 1) bring the whole dataset without the meaningless columns and 2) get a sense of which books we've checked out the most frequently. I set up the Transforms to do a Gsheet sync every time they run.
