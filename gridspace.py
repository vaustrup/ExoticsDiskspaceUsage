import csv

with open('lookup_table.csv') as f:
    r = csv.reader(f, delimiter=' ')
    for row in r:
        if len(row) < 3:
            print(row, "missing analysis reference")
