TS Data Aggregator

Follow here: https://developers.google.com/sheets/api/quickstart/python Until reaching the part about credentials.json. Copy that into this folder.

Then create a config.json with:

{
    "google_sheet_id": "Last part of URL before #edir",
    "maint_multiplier": 1.03
}


Run using python3 main.py. On first run, you'll need to authorize the application, and you'll need to ensure port 12580 reaches the app (eg when using SSH use -L12580:127.0.0.1:12580). This only needs to be done when the token expires, which on a "test" app is every 7 days. If moved to production, the timeline should be longer, but I am unsure of that.
