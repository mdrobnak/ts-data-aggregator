from bs4 import BeautifulSoup
import requests
import pandas
import pprint
import time


def calc_ten_yr_maint(maint_fee, usage, mm):
    if usage == "Biennial-Even":
        return (
            mm ** 10 * maint_fee
            + mm ** 8 * maint_fee
            + mm ** 6 * maint_fee
            + mm ** 4 * maint_fee
            + mm ** 2 * maint_fee
        )
    elif usage == "Biennial-Odd":
        return (
            mm ** 9 * maint_fee
            + mm ** 7 * maint_fee
            + mm ** 5 * maint_fee
            + mm ** 3 * maint_fee
            + mm ** 1 * maint_fee
        )
    else:
        return (
            mm ** 10 * maint_fee
            + mm ** 9 * maint_fee
            + mm ** 8 * maint_fee
            + mm ** 7 * maint_fee
            + mm ** 6 * maint_fee
            + mm ** 5 * maint_fee
            + mm ** 4 * maint_fee
            + mm ** 3 * maint_fee
            + mm ** 2 * maint_fee
            + mm ** 1 * maint_fee
        )


def get_headers():
    return [
        "Resort",
        "Bed",
        "Bath",
        "Usage",
        "Points",
        "% Max Points",
        "$ Purchase/Point",
        "$ MF/Point",
        "Ten Yr Cost/Point",
        "List Price",
        "Closing Costs",
        "Hilton Fees",
        "Purchase Cost",
        "$ Maintenance",
        "10 Years Maint",
        "10 Year Cost",
        "10 Yr Cost / 10",
    ]


# Find unique prices per point level
# Filter on cost threshold.
# For remaining,
# Look up newest listing. Add on number of duplicates.
def minimize(rows, max_points):
    final_rows = []
    headers = get_headers()
    df = pandas.DataFrame(rows, columns=headers[0:17])
    df = df.astype({"List Price": "int"})
    # pprint.pprint(df)
    df.drop_duplicates(
        subset=["Resort", "List Price", "Usage", "Bed", "Bath", "Points"], inplace=True
    )
    # pprint.pprint(df)
    for points in df["Points"].unique():
        print("  Points: " + str(points))
        for usage in df["Usage"].unique():
            # Get just the rows which match the points in question
            # print("Find the rows with that point value and season...")
            df_points = df.loc[(df["Points"] == points) & (df["Usage"] == usage)]
            # pprint.pprint(df_points)
            # Find the lowest cost for that point value and season.
            if not df_points.empty:
                l = df_points.loc[df_points["List Price"].idxmin()].to_list()
                # print("Lowest row:")
                # pprint.pprint(l)
                # Stupid Datatypes.
                l[1] = int(l[1])
                l[2] = int(l[2])
                l[4] = int(l[4])
                l[7] = float(l[7])
                l[8] = float(l[8])
                l[9] = int(l[9])
                l[10] = int(l[10])
                l[11] = float(l[11])
                l[12] = float(l[12])
                l[13] = int(l[13])
                l[14] = int(l[14])
                l[15] = int(l[15])
                l[16] = float(l[16])
                final_rows.append(l)
    # print("Returned final rows:")
    # pprint.pprint(final_rows)
    return final_rows


def get_sts_maint(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }
    page = requests.get(url, headers=headers)
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
    return maint


def get_tsp_maint(url):
    page = requests.get(url)
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
    else:
        maint = 0
        taxes = 0
    return maint + taxes


def get_tsbs_maint(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0",
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")
    span = soup.find_all("span", style="color:#2A2929;font-size: 14px;")[6].text
    details = span.strip().replace("$", "").replace(",", "")
    maint = float(details)
    return maint


def get_maint(final_rows, config):
    stsurl = "https://sellingtimeshares.net/"
    tspurl = "https://www.timesharebrokersmls.com/"
    tsbsurl = "https://www.timesharebrokersales.com/"

    for row in final_rows:
        link = row[0].split('"')[1]
        if row[13] > 0.0:
            row[7] = float(row[13]) / float(row[4])
        else:
            if link.startswith(stsurl):
                maint = get_sts_maint(link)
            elif link.startswith(tspurl):
                maint = get_tsp_maint(link)
            elif link.startswith(tsbsurl):
                maint = get_tsbs_maint(link)
            row[13] = maint
            row[7] = float(row[13]) / float(row[4])
        ten_yr_maint = calc_ten_yr_maint(row[13], row[3], config["maint_multiplier"])
        ten_yr_cost = row[12] + ten_yr_maint
        ten_yr_amort = ten_yr_cost / 10.0
        ten_yr_amort_per_pt = ten_yr_amort / int(row[4])
        row[8] = ten_yr_amort_per_pt
        row[14] = ten_yr_maint
        row[15] = ten_yr_cost
        row[16] = ten_yr_amort
        time.sleep(0.25)
    return final_rows
