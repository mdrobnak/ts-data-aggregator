import pandas
import pprint


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
        print("Points: " + str(points))
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
