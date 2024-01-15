import re
import requests
import time
from bs4 import BeautifulSoup

# Find unique point levels returned
# Find unique prices per point level
# Filter on cost threshold.
# For remaining,
# Look up newest listing. Add on number of duplicates.
def process_listings(data):
    baseurl = "https://www.timesharebrokersmls.com/"
    mincost = 1
    max_price = int(data["price_factor"] * data["max_points"])
    if data["beds"] == 0:
        beds_param = "N"
    else:
        beds_param = str(data["beds"])
    url = (
        baseurl
        + "Search/N/"
        + data["names"]["tsp"]
        + "/N/gt/"
        + str(data["points"])
        + "/"
        + str(mincost)
        + "/"
        + str(max_price)
        + "/"
        + str(data["season"])
        + "/N/N/N/N/"
        + beds_param
        + "/N/Results.html"
    )
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    table = soup.find(id="MainContent_GridView1")

    # Mappings to keep sanity
    price = 2
    freq = 3
    beds = 5
    baths = 6
    points = 9
    link = 10

    # python3 just use th.text
    if table is not None:
        rows = []
        for row in table.select("tr + tr"):
            td_array = []
            for td in row.find_all("td"):
                if td.text.strip() != "View Listing":
                    td_array.append(td.text.strip())
                else:
                    td_array.append(
                        str(td.a["href"]).replace(
                            "../../../../../../../../../../../../../../../", baseurl
                        )
                    )
            # URL has filtering already in it, no need to check before appending. Except for Studios, so filter on that.
            # print(td_array)
            if td_array[baths] == "":
                td_array[baths] = td_array[beds]
            if re.search(".*(even).*", td_array[freq].lower()):
                td_array[freq] = "Biennial-Even"
                pr_per_point = 2.0 * float(td_array[price]) / float(td_array[points])
            if re.search(".*(odd).*", td_array[freq].lower()):
                td_array[freq] = "Biennial-Odd"
                pr_per_point = 2.0 * float(td_array[price]) / float(td_array[points])
            if re.search(".*([Aa]nnual).*", td_array[freq]):
                td_array[freq] = "Annual"
                pr_per_point = 1.0 * float(td_array[price]) / float(td_array[points])
            # Set MF for resort
            if data.get("maint_fees"):
                maint_fees = data.get("maint_fees")
            else:
                maint_fees = 0.0
            if (
                int(td_array[beds]) == data["beds"]
                and pr_per_point <= data["max_pr_per_point"]
            ):
                formatted_link = (
                    '=HYPERLINK("'
                    + td_array[link]
                    + '", "'
                    + data["names"]["display"]
                    + '")'
                )
                purchase_price = (
                    round(float(td_array[price]))
                    + data["closing_costs"]
                    + data["hilton_fees"]
                )
                purchase_price_per_pt = purchase_price / int(td_array[points])
                rows.append(
                    [
                        formatted_link,
                        int(td_array[beds]),
                        int(td_array[baths]),
                        td_array[freq],
                        int(td_array[points]),
                        float(td_array[points]) / float(data["max_points"]),
                        purchase_price_per_pt,
                        0,  # mf_per_point - 7
                        0,  # ten_yr_amort_per_pt - 8
                        round(float(td_array[price])),
                        data["closing_costs"],
                        data["hilton_fees"],
                        purchase_price,  # 12
                        maint_fees,  # 13
                        0,  # ten_yr_maint - 14
                        0,  # ten_yr_cost - 15
                        0,  # ten_yr_amort - 16
                    ]
                )  # 9 items
            # Zero holders for Maintenance
        return rows
    else:
        return []
