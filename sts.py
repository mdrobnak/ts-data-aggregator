from bs4 import BeautifulSoup
import requests
import re
import time


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
                beds = 1
            elif re.search(".*[Vv]aries.*", size):
                beds = 3
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
    if data["name"] == "Elara, A Hilton Grand Vacations Club":
        tgt_resort = "Hilton Elara"
    elif data["name"] == "HGV Club on the Boulevard":
        tgt_resort = "Hilton Las Vegas Strip"
    elif data["name"] == "The Grand Islander by Hilton Grand Vacations":
        tgt_resort = "Hilton Grand Islander"
    elif data["name"] == "Kings Land By Hilton Grand Vacations":
        tgt_resort = "Hilton King’s Land"
    elif data["name"] == "Ocean Tower at Hilton Waikoloa Village":
        tgt_resort = "Hilton Ocean Tower"
    else:
        tgt_resort = data["name"]

    resort = 1
    price = 2
    usage = 3
    beds = 4
    baths = 5
    points = 6
    season = 7
    link = 8
    pr_points = 9

    for row in listings:
        if re.search(".*(even).*", row[usage].lower()):
            row[usage] = "Even Years"
        if re.search(".*(odd).*", row[usage].lower()):
            row[usage] = "Odd Years"
        if re.search(".*([Aa]nnual).*", row[usage]):
            row[usage] = "Annual"

        if (
            row[resort] == tgt_resort
            and int(row[points]) >= int(data["points"])
            and row[beds] == data["beds"]
            and row[price] <= max_price
        ):
            rows.append(
                [
                    0,
                    data["name"],
                    round(float(row[price])),
                    row[usage],
                    int(row[beds]),
                    int(row[baths]),
                    int(row[points]),
                    row[link],
                    row[pr_points],
                    0,
                    0,
                    float(row[points]) / float(data["max_points"]),
                ]
            )
    return rows


def get_maint(final_rows):
    baseurl = "https://sellingtimeshares.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }
    for row in final_rows:
        if row[7].startswith(baseurl):
            page = requests.get(row[7], headers=headers)
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
            row[9] = maint / float(row[6])
            row[10] = maint
            time.sleep(1)
        else:
            continue
    # Gather Maintenance and Taxes from resulting page, add to spreadsheet.
    return final_rows
