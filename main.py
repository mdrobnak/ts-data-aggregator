import json
import operator
import os
import time

import av
import co
import gs
import sts
import tsbs
import tsp
import tug
import utils

# Load config
with open("config.json") as js_file:
    config = json.load(js_file)

if not config.get("max_pr_per_point"):
    max_pr_per_point = 0.75
else:
    max_pr_per_point = config["max_pr_per_point"]

# Choose between using CSV or Google Sheets
if not config.get("google_sheet_id"):
    print("Outputting to CSV.")
    output_type = "csv"
else:
    print("Outputting to Google Sheets.")
    google_spreadsheet_id = config["google_sheet_id"]
    output_type = "gs"
    service = gs.init_gs()
    if not gs.create_gs(service, google_spreadsheet_id):
        print("Error creating sheet.")
        os.exit(1)

# Get headers
headers = utils.get_headers()

listings = []
results = []
sts_listings = sts.get_listings()
av_listings = av.get_listings()
print("---")
# Iterate through sources
with open("full.json") as json_file:
    data = json.load(json_file)
    for item in data:
        if not data.get("max_pr_per_point"):
            data[item]["max_pr_per_point"] = max_pr_per_point
        data[item]["hilton_fees"] = 790.00
        data[item]["maint_multiplier"] = config["maint_multiplier"]
        print("Processing " + item)
        listings = tug.process_listings(data[item])
        listings = sts.process_listings(sts_listings, data[item])
        listings += tsp.process_listings(data[item])
        listings += av.process_listings(av_listings, data[item])
        listings += tsbs.process_listings(data[item])
        results += utils.minimize(listings, data[item]["max_points"])
        time.sleep(0.25)

results = utils.get_maint(results, config)
results.sort(key=operator.itemgetter(8, 7))

print("---")
if output_type == "gs":
    print("Updating Google Sheets")
    gs.update_gs(service, google_spreadsheet_id, headers, results)
else:
    co.output_csv(results)
print("Complete.")
