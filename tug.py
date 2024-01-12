from bs4 import BeautifulSoup
import requests
import re


def process_listings(data):
    baseurl = "https://www.tug2.com/timesharemarketplace/search?"
    mincost = 1
    max_price = int(data["price_factor"] * data["max_points"])
    baseurl = "https://www.tug2.com/timesharemarketplace/search?PointProgramResortId=15022&ForSale=True&OrderBy=Price&HasPointsOwnership=True&"
    if data["beds"] == 1:
        unit_type = "StudioUnit=True&OneBedroom=True"
    elif data["beds"] == 2:
        unit_type = "TwoBedroom=True"
    elif data["beds"] == 3:
        unit_type = "ThreeBedroom=True"
    else:
        unit_type = "FourBedroom=True"

    url = (
        baseurl
        + "ResortId="
        + str(data["tug_resort_id"])
        + "&"
        + unit_type
        + "&PriceMax="
        + str(max_price)
    )

    # Find unique point levels returned
    # Find unique prices per point level
    # Filter on cost threshold.
    # For remaining,
    # Look up newest listing. Add on number of duplicates.
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "lxml")
    # print(" -------------------------------------- ")
    table = soup.select(".tug-row")
    # python3 just use th.text
    if table is not None:
        rows = []
        for elements in table:
            mf = "-1"
            price = "-1"
            points = "-1"
            season = "unk"
            freq = "unk"
            eid = elements["id"].split("-")[1]
            el = elements.find(class_="col-md-10")
            fp = el.find_all(class_="col-md-8 col-lg-8 col-xl-8")[1].text
            points = int(
                re.search("(\d+,\d+) Hilton Grand Vacation Club HGVC Points", fp)
                .group(1)
                .replace(",", "")
            )
            page_data = el.find_all(class_="col-md-2")[1]
            price = round(
                float(
                    page_data.find("strong")
                    .text.replace("$", "")
                    .replace(",", "")
                    .strip()
                )
            )
            mf = page_data.find("small")
            mf.find("span").decompose()
            mf = float(mf.text.replace("$", "").replace(",", "").strip())
            unit_find = el.find_all("strong")
            for unit in unit_find:
                unit = unit.text.strip()
                if re.search(".*([Gg]old|[Pp]latinum|[Ss]ilver).*", unit):
                    season = (
                        re.search(".*([Gg]old|[Pp]latinum|[Ss]ilver).*", unit)
                        .group(1)
                        .lower()
                    )
                if re.search(".*([Aa]nnual).*", unit):
                    freq = "Annual"
                if re.search(".*(even).*", unit.lower()):
                    freq = "Biennial-Even"
                if re.search(".*(odd).*", unit.lower()):
                    freq = "Biennial-Odd"

                if freq == "unk":
                    fr = elements.find_all(attrs={"id": "Description-" + eid})
                    for fs in fr:
                        fs = fs.text.strip()
                        if re.search(".*(EY).*", fs):
                            freq = "Annual"
                            pr_per_point = 1.0 * float(price) / float(points)
                        if re.search(".*(EOYE).*", fs):
                            freq = "Biennial-Even"
                            pr_per_point = 2.0 * float(price) / float(points)
                        if re.search(".*(EOYO).*", fs):
                            freq = "Biennial-Odd"
                            pr_per_point = 2.0 * float(price) / float(points)

            if mf == "-1" or points == "-1" or freq == "unk":
                print(eid, price, freq, points, mf)

            if (
                mf != "-1"
                and price <= max_price
                and points != "-1"
                and freq != "unk"
                and int(points) >= int(data["points"])
                and pr_per_point <= data["max_pr_per_point"]
            ):
                rows.append(
                    [
                        0,
                        data["names"]["display"],
                        price,
                        freq,
                        data["beds"],
                        data["beds"],
                        points,
                        '=HYPERLINK("' + url + '", "TUG")',
                        pr_per_point,
                        float(mf) / float(points),
                        mf,
                        float(points) / float(data["max_points"]),
                    ]
                )  # 9 items
        return rows
    else:
        return []
