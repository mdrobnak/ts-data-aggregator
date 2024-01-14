from bs4 import BeautifulSoup
import requests
import re
import time

import utils


def get_listings():
    url = "https://sellingtimeshares.net/category/listings/hilton/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "lxml")
    table = soup.find("table")
    if table is not None:
        rows = []
        for row in table.select("tr + tr"):
            # Sort through the name / price / maint first...
            resort = row.find(class_="resort_title")
            link = resort.a["href"]
            resort = resort.text.strip()
            price = round(
                float(
                    row.find("td", {"data-title": "Price"})
                    .text.replace("$", "")
                    .replace(",", "")
                    .strip()
                )
            )
            usage = row.find("td", {"data-title": "Usage"}).text.strip()
            points = row.find("td", {"data-title": "Points"}).text.strip()
            season = row.find("td", {"data-title": "Season"}).text.strip()
            size = row.find("td", {"data-title": "Size"}).text.strip()
            if re.search(".*[Ss]tudio.*", size):
                beds = 0
                baths = 1
            elif re.search(".*[Vv]aries.*", size):
                beds = 3
                baths = 2
            else:
                beds = re.search(".*(\d+)\s+[Bb]ed.*", size).group(1)
                baths = beds
            rows.append(
                [
                    0,
                    resort,
                    price,
                    usage,
                    beds,
                    baths,
                    points,
                    season,
                    link,
                    float(price) / float(points),
                ]
            )
        return rows
    else:
        return []


def process_listings(listings, data):
    max_price = int(data["price_factor"] * data["max_points"])
    rows = []
    if data["names"].get("sts"):
        tgt_resort = data["names"]["sts"]
    else:
        tgt_resort = data["names"]["display"]

    resort = 1
    price = 2
    usage = 3
    beds = 4
    baths = 5
    points = 6
    season = 7
    link = 8
    pr_per_point = 9

    for row in listings:
        if re.search(".*(even).*", row[usage].lower()):
            row[usage] = "Biennial-Even"
            row[pr_per_point] = 2.0 * row[pr_per_point]
        if re.search(".*(odd).*", row[usage].lower()):
            row[usage] = "Biennial-Odd"
            row[pr_per_point] = 2.0 * row[pr_per_point]
        if re.search(".*([Aa]nnual).*", row[usage]):
            row[usage] = "Annual"

        # Set MF for resort
        if data.get("maint_fees"):
            maint_fees = data.get("maint_fees")
        else:
            maint_fees = 0
        if (
            row[resort] == tgt_resort
            and int(row[points]) >= int(data["points"])
            and row[beds] == data["beds"]
            and row[price] <= max_price
            and row[pr_per_point] <= data["max_pr_per_point"]
        ):
            row[link] = (
                '=HYPERLINK("' + row[link] + '", "' + data["names"]["display"] + '")'
            )
            purchase_price = row[price] + data["closing_costs"] + data["hilton_fees"]
            purchase_price_per_pt = purchase_price / int(row[points])
            rows.append(
                [
                    row[link],
                    int(row[beds]),
                    int(row[baths]),
                    row[usage],
                    int(row[points]),  # 4
                    float(row[points]) / float(data["max_points"]),
                    purchase_price_per_pt,
                    0,  # mf_per_point - 7
                    0,  # ten_yr_amort_per_pt - 8
                    round(float(row[price])),
                    data["closing_costs"],
                    data["hilton_fees"],
                    purchase_price,  # 12
                    maint_fees,  # 13
                    0,  # ten_yr_maint - 14
                    0,  # ten_yr_cost - 15
                    0,  # ten_yr_amort - 16
                ]
            )
    return rows


def get_maint(final_rows, config):
    baseurl = "https://sellingtimeshares.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }

    for row in final_rows:
        link = row[0].split('"')[1]
        if link.startswith(baseurl):
            if link.startswith(baseurl) and row[13] > 0.0:
                row[7] = float(row[13]) / float(row[4])
            else:
                page = requests.get(link, headers=headers)
                soup = BeautifulSoup(page.text, "html.parser")
                table = soup.find(class_="resort_info")
                rows = table.select("tr + tr")
                details = (
                    rows[8]
                    .find_all("td")[0]
                    .text.strip()
                    .split()[0]
                    .replace("$", "")
                    .replace(",", "")
                )
                maint = float(details)
                row[7] = maint / float(row[4])
                row[13] = maint
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
            time.sleep(0.25)
        else:
            continue
    # Gather Maintenance and Taxes from resulting page, add to spreadsheet.
    return final_rows
