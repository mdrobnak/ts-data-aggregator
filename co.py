import csv
from datetime import date

import utils


def output_csv(output_data):
    output_filename = "ts-%s.csv" % date.today()
    print("Writing to:", output_filename)
    output_data_file = open(output_filename, "w")
    output_writer = csv.writer(output_data_file)
    output_writer.writerow(utils.get_headers())
    output_writer.writerows(output_data)
    # Close file.
    output_data_file.close()
