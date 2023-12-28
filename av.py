from bs4 import BeautifulSoup
import requests
import re
import pprint


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
    if data["name"] == "HGV Club on the Boulevard":
        tgt_resort = "Hilton Grand Vacations Club on the Las Vegas Strip"
    elif data["name"] == "The Grand Islander by Hilton Grand Vacations":
        tgt_resort = (
            "Hilton Grand Vacations Club at Hilton Hawaiian Village-Grand Islander"
        )
    elif data["name"] == "Kings Land By Hilton Grand Vacations":
        tgt_resort = "Hilton Grand Vacations Club at Kings Land"
    else:
        tgt_resort = data["name"]

    resort = 1
    price = 2
    freq = 3
    beds = 5
    baths = 5
    points = 6
    link = 7
    maint = 10

    for row in listings:
        if re.search(".*(even).*", row[freq].lower()):
            row[freq] = "Even Years"
        if re.search(".*(odd).*", row[freq].lower()):
            row[freq] = "Odd Years"
        if re.search(".*([Aa]nnual).*", row[freq]):
            row[freq] = "Annual"

        if (
            int(row[2]) <= max_price
            and row[1] == tgt_resort
            and row[freq] == "Annual"
            and int(row[6]) >= data["points"]
            and data["beds"] == row[beds]
        ):
            rows.append(
                [
                    0,
                    data["name"],
                    row[price],
                    row[freq],
                    int(row[beds]),
                    int(row[baths]),
                    int(row[points]),
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    float(row[6]) / float(data["max_points"]),
                ]
            )
    return rows
