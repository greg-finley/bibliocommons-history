Go to some link like https://ssfpl.bibliocommons.com/v2/holds

Grab the tokens and put them in .env

Load the CSV to some temporary table and reconcile it with
`greg-finley.books.borrowing_history`

https://docs.google.com/spreadsheets/d/1V3PDjjV75I80yJvZyi0SLrPhGDAx9hvsfGTtI7BzrAk/edit#gid=358378540

Secret is like this

```
LIBRARY_CREDENTIALS=[{"name": "Greg", "account_id": "1234", "user_id": "my_user", "user_pin": "my_pin"}]
```
