import pandas
import pprint


def get_headers():
    return [
        "MLS",
        "Resort",
        "List Price",
        "Usage",
        "Bed",
        "Bath",
        "Points",
        "Link",
        "$/Point",
        "$ MF/Point",
        "$ Maintenance",
        "% Max Points",
    ]


# Find unique prices per point level
# Filter on cost threshold.
# For remaining,
# Look up newest listing. Add on number of duplicates.
def minimize(rows, max_points):
    final_rows = []
    headers = get_headers()
    df = pandas.DataFrame(rows, columns=headers[0:12])
    df = df.astype({"List Price": "int"})
    #    pprint.pprint(df)
    df.drop_duplicates(
        subset=["Resort", "List Price", "Bed", "Bath", "Points"], inplace=True
    )
    #    pprint.pprint(df)
    for points in df["Points"].unique():
        print("Points: " + str(points))
        # Get just the rows which match the points in question
        #        print("Find the rows with that point value...")
        df_points = df.loc[df["Points"] == points]
        #        pprint.pprint(df_points)
        # Find the lowest cost for that point value.
        l = df_points.loc[df_points["List Price"].idxmin()].to_list()
        #        print("Lowest row:")
        #        pprint.pprint(l)
        # Stupid Datatypes.
        l[0] = int(l[0])
        l[2] = int(l[2])
        l[4] = int(l[4])
        l[5] = int(l[5])
        l[6] = int(l[6])
        l[8] = float(l[8])
        final_rows.append(l)
    #    print("Returned final rows:")
    #   pprint.pprint(final_rows)
    return final_rows
