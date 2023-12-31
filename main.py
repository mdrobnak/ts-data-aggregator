import json
import operator
import os
import time

import av
import gs
import sts
import tsbs
import tsp
import tug
import utils
import pprint

# Load config
with open("config.json") as js_file:
    config = json.load(js_file)

google_spreadsheet_id = config["google_sheet_id"]
# Test the Google Sheets stuff early, I hope...
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
# Iterate through sources
with open("full.json") as json_file:
    data = json.load(json_file)
    for item in data:
        print("Processing " + item)
        #        print("Judy:")
        #        print(listings)

        listings = tug.process_listings(data[item])
        listings += sts.process_listings(sts_listings, data[item])
        #        print("Tug:")
        #        print(listings)
        listings += tsp.process_listings(data[item])

        #        print(av_listings)
        listings += av.process_listings(av_listings, data[item])
        listings += tsbs.process_listings(data[item])

        results += utils.minimize(listings, data[item]["max_points"])
        # print("Minimized:")
        # print(results)
        time.sleep(0.25)

# print("Final results:")
# pprint.pprint(results)
# Get the lowest cost for each point value
results = sts.get_maint(results)
results = tsp.get_maint(results)
results = tsbs.get_maint(results)
results.sort(key=operator.itemgetter(9, 8))
print("Updating Google Sheets")
gs.update_gs(service, google_spreadsheet_id, headers, results)
print("Complete.")
