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
            if int(td_array[beds]) == data["beds"]:
                rows.append(
                    [
                        td_array[0],
                        data["names"]["display"],
                        round(float(td_array[price])),
                        td_array[freq],
                        int(td_array[beds]),
                        int(td_array[baths]),
                        int(td_array[points]),
                        td_array[link],
                        float(td_array[price]) / float(td_array[points]),
                        0.0,
                        0.0,
                        float(td_array[points]) / float(data["max_points"]),
                    ]
                )  # 9 temitems
            # Zero holders for Maintenance
        return rows
    else:
        return []


def get_maint(final_rows):
    baseurl = "https://www.timesharebrokersmls.com/"
    for row in final_rows:
        if row[7].startswith(baseurl):
            print(row[7])
            page = requests.get(row[7])
            row[7] = '=HYPERLINK("' + row[7] + '", "TSP")'
            soup = BeautifulSoup(page.text, "html.parser")
            table = soup.find(id="MainContent_DetailsView2")
            if table is not None:
                detail_rows = [
                    [td.text.strip() for td in row.find_all("td")]
                    for row in table.select("tr + tr")
                ]

                for details in detail_rows:
                    if details[0].strip() == "Maintenance":
                        maint = float(details[1])
                    if details[0].strip() == "Taxes":
                        taxes = float(details[1])
                        row[9] = (maint + taxes) / float(row[6])
                        row[10] = maint + taxes
            time.sleep(0.25)
        else:
            continue
    # Gather Maintenance and Taxes from resulting page, add to spreadsheet.
    return final_rows
