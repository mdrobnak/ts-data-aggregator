from bs4 import BeautifulSoup
import requests
import re
import time

import utils


def process_listings(data):
    baseurl = "https://www.timesharebrokersales.com/hilton-timeshare/"
    mincost = 1
    max_price = int(data["price_factor"] * data["max_points"])
    if data["beds"] == 1:
        unit_type = "StudioUnit=True&OneBedroom=True"
    elif data["beds"] == 2:
        unit_type = "TwoBedroom=True"
    elif data["beds"] == 3:
        unit_type = "ThreeBedroom=True"
    else:
        unit_type = "FourBedroom=True"

    if data["names"].get("tsbs") is None:
        return []
    url = baseurl + str(data["names"]["tsbs"])
    rows = []
    # Find unique point levels returned
    # Find unique prices per point level
    # Filter on cost threshold.
    # For remaining,
    # Look up newest listing. Add on number of duplicates.
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "lxml")
    table = soup.find(class_="container-fluid")
    # python3 just use th.text
    if table is not None:
        data_rows = table.find_all("tr")
        for row in data_rows:
            mf = "-1"
            price = -1
            points = "-1"
            season = "unk"
            freq = "unk"
            count = 0
            spec_rows = row.find_all("div", class_="row")
            for sr in spec_rows:
                spec_data = sr.find_all("tr")[1]
                specs = spec_data.find_all("td")
                if len(specs) == 6:
                    season = specs[0].text
                    bed_text = specs[1].text.split()[0]
                    if bed_text == "Studio":
                        beds = 1
                    elif bed_text == "Other":
                        beds = 1
                    else:
                        beds = int(bed_text)
                    baths = int(specs[2].text)
                    points = int(specs[4].text.split()[0].replace(",", ""))
                    usage = specs[5].text
            price_row = row.find_all("td", class_="col-lg-4 col-md-4 col-sm-12")
            #        price_rows = price_row.find_all("div")
            #        print(len(price_rows))
            if len(price_row) > 0:
                price_text = (
                    price_row[0].text.split()[2].replace("$", "").replace(",", "")
                )
                for r in price_row:
                    if r.a is not None:
                        link = r.a["href"].strip()
                if price_text == "Price":
                    continue
                else:
                    price = round(float(price_text))
            #        for pr in price_rows:
            #            print("Count: " + str(count))
            #            print(pr)
            #            count += 1
            if re.search(".*(even).*", usage.lower()):
                usage = "Biennial-Even"
                pr_per_point = 2.0 * float(price) / float(points)
            if re.search(".*(odd).*", usage.lower()):
                usage = "Biennial-Odd"
                pr_per_point = 2.0 * float(price) / float(points)
            if re.search(".*([Aa]nnual).*", usage):
                usage = "Annual"
                pr_per_point = 1.0 * float(price) / float(points)
            # Set MF for resort
            if data.get("maint_fees"):
                maint_fees = data.get("maint_fees")
            else:
                maint_fees = 0.00
            if (
                price != -1
                and price <= max_price
                and points != "-1"
                and season != "unk"
                and data["beds"] == int(beds)
                and points >= data["points"]
                and pr_per_point <= data["max_pr_per_point"]
            ):
                purchase_price = price + data["closing_costs"] + data["hilton_fees"]
                purchase_price_per_pt = purchase_price / points
                rows.append(
                    [
                        '=HYPERLINK("'
                        + link
                        + '", "'
                        + data["names"]["display"]
                        + '")',
                        beds,
                        baths,
                        usage,
                        points,
                        float(points) / float(data["max_points"]),
                        purchase_price_per_pt,
                        0,  # mf_per_point - 7
                        0,  # ten_yr_amort_per_pt - 8
                        round(float(price)),
                        data["closing_costs"],
                        data["hilton_fees"],
                        purchase_price,  # 12
                        maint_fees,  # 13
                        0,  # ten_yr_maint - 14
                        0,  # ten_yr_cost - 15
                        0,  # ten_yr_amort - 16
                    ]
                )

    # for row in rows:
    #    print("New Row")
    #    for item in row:
    #        print(type(item))
    #    print("End Row")
    return rows


def get_maint(final_rows, config):
    baseurl = "https://www.timesharebrokersales.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }
    for row in final_rows:
        link = row[0].split('"')[1]
        if link.startswith(baseurl):
            if link.startswith(baseurl) and row[13] > 0.0:
                row[7] = float(row[13]) / float(row[4])
            else:
                print(link)
                page = requests.get(link, headers=headers)
                soup = BeautifulSoup(page.text, "html.parser")
                span = soup.find_all("span", style="color:#2A2929;font-size: 14px;")[
                    6
                ].text
                details = span.strip().replace("$", "").replace(",", "")
                maint = float(details)
                row[7] = maint / float(row[4])
                row[13] = maint
                time.sleep(0.25)
            ten_yr_maint = utils.calc_ten_yr_maint(
                row[13], row[3], config["maint_multiplier"]
            )
            ten_yr_cost = row[12] + ten_yr_maint
            ten_yr_amort = ten_yr_cost / 10.0
            ten_yr_amort_per_pt = ten_yr_amort / int(row[4])
            row[8] = ten_yr_amort_per_pt
            row[14] = ten_yr_maint
            row[15] = ten_yr_cost
            row[16] = ten_yr_amort
        else:
            continue
    # Gather Maintenance and Taxes from resulting page, add to spreadsheet.
    return final_rows
