from bs4 import BeautifulSoup
import requests
import re
import pprint

import utils


def get_listings():
    url = "https://010.87c.myftpupload.com/hilton-listings-by-points/"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "lxml")
    # print(" -------------------------------------- ")
    table = soup.find("table")
    #    pprint.pprint(table)
    # python3 just use th.text
    if table is not None:
        rows = []
        for row in table.select("tr + tr"):
            #            pprint.pprint(row)
            # Sort through the name / price / maint first...
            td_array = []
            dup = row.find_all("td")
            resort = dup[0].p.a.text.strip()
            link = dup[0].p.a["href"]
            dup[0].p.find("a").decompose()
            if dup[0].find("br"):
                dup[0].find("br").decompose()
            price = round(
                float(dup[0].p.strong.text.replace("$", "").replace(",", "").strip())
            )
            dup[0].p.find("strong").decompose()
            maint = float(
                re.search("\(\$(\d+\.?\d+).*\)", dup[0].text.strip()).group(1)
            )
            #            print(resort+link+price+maint)
            season = dup[1].text.strip().replace("Plus ", "").split()[0]
            freq = dup[2].text.strip()
            beds = re.search(".*(\d+) [Bb]ed.*", dup[4].text.strip()).group(1)
            baths = re.search(".*(\d+) [Bb]ath.*", dup[4].text.strip()).group(1)
            points = dup[6].text.strip()
            #            print(resort + link)
            # p = dup[0].find("p")
            # p.find("br").decompose()
            # p.find("strong").decompose()
            # print(p.text.strip())
            #            pprint.pprint(dup[0].p.a.text.strip())
            #            pprint.pprint(dup[1])
            rows.append(
                [
                    0,
                    resort,
                    price,
                    freq,
                    beds,
                    baths,
                    points,
                    link,
                    float(price) / float(points),
                    float(maint) / float(points),
                    maint,
                ]
            )
        return rows
    else:
        return []


def process_listings(listings, data):
    max_price = int(data["price_factor"] * data["max_points"])
    rows = []
    if data["names"].get("av"):
        tgt_resort = data["names"]["av"]
    else:
        tgt_resort = data["names"]["display"]

    resort = 1
    price = 2
    freq = 3
    beds = 5
    baths = 5
    points = 6
    link = 7
    pr_per_point = 8
    mf_per_point_loc = 9
    maint = 10

    for row in listings:
        if re.search(".*(even).*", row[freq].lower()):
            row[freq] = "Biennial-Even"
            row[pr_per_point] = 2.0 * row[pr_per_point]
        if re.search(".*(odd).*", row[freq].lower()):
            row[freq] = "Biennial-Odd"
            row[pr_per_point] = 2.0 * row[pr_per_point]
        if re.search(".*([Aa]nnual).*", row[freq]):
            row[freq] = "Annual"

        # Set MF for resort
        if data.get("maint_fees"):
            maint_fees = float(data.get("maint_fees"))
            mf_per_point = maint_fees / float(row[points])
        else:
            maint_fees = row[maint]
            mf_per_point = row[mf_per_point_loc]
        if (
            int(row[price]) <= max_price
            and row[resort] == tgt_resort
            and int(row[points]) >= data["points"]
            and int(data["beds"]) == int(row[beds])
            and row[pr_per_point] <= data["max_pr_per_point"]
        ):

            row[link] = (
                '=HYPERLINK("' + row[link] + '", "' + data["names"]["display"] + '")'
            )
            purchase_price = row[price] + data["closing_costs"] + data["hilton_fees"]
            purchase_price_per_pt = purchase_price / float(row[points])
            ten_yr_maint = utils.calc_ten_yr_maint(
                maint_fees, row[freq], data["maint_multiplier"]
            )
            ten_yr_cost = purchase_price + ten_yr_maint
            ten_yr_amort = ten_yr_cost / 10.0
            ten_yr_amort_per_pt = ten_yr_amort / float(row[points])

            rows.append(
                [
                    row[link],
                    int(row[beds]),
                    int(row[baths]),
                    row[freq],
                    int(row[points]),
                    float(row[6]) / float(data["max_points"]),
                    purchase_price_per_pt,
                    mf_per_point,
                    ten_yr_amort_per_pt,
                    row[price],
                    data["closing_costs"],
                    data["hilton_fees"],
                    purchase_price,
                    maint_fees,
                    ten_yr_maint,
                    ten_yr_cost,
                    ten_yr_amort,
                ]
            )
    return rows
