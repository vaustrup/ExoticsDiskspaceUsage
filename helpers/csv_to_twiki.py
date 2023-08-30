"""
Convert given CSV file into TWiki table.
TODO: hard-coded to work for the analysis lookup table only so far
"""

import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True, help="Name of input csv file to convert into TWiki table.")
parser.add_argument("--delimiter", default=" ", help="Delimiter used in csv file. Default: ' '")
parser.add_argument("--highlight-header", action="store_true", help="Set flag to highlight the first row of the table.")
args = parser.parse_args()


inputfile = args.file
outputfile = f"reports/{args.file[:-4]}.table"
with open(outputfile, "w") as f_out:
    f_out.write(f"<!-- This file is created automatically from {inputfile}. Do not edit it manually. -->\n")
    with open(inputfile, "r") as f_in:
        reader = csv.reader(f_in, delimiter=args.delimiter)
        first_line = True
        for line in reader:
            scope = line[0]
            keyword = line[1]
            analysis = line[2] if len(line)>2 else ""
            if first_line:
                first_line = False
                if args.highlight_header:
                    f_out.write(f"| * {scope} * | * {keyword} * | * {analysis} * |\n")
                    continue
            f_out.write(f"| {scope} | {keyword} | {analysis} |\n")
        
