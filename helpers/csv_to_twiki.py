"""
Convert given CSV file into TWiki-table syntax.
"""

import argparse
import csv
import pathlib
import sys

import logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)4s]: %(message)s", "%d.%m.%Y %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--file", required=True, help="Name of input csv file to convert into TWiki table.")
parser.add_argument("--delimiter", default=" ", help="Delimiter used in csv file. Default: ' '")
parser.add_argument("--highlight-header", action="store_true", help="Set flag to highlight the first row of the table.")
args = parser.parse_args()

inputfile = pathlib.Path(args.file)
outputfile = f"reports/{inputfile.stem}.table"
log.info(f"Converting csv file {args.file} into TWiki-table syntax. Output stored in {outputfile}.")

with open(outputfile, "w") as f_out:
    with open(inputfile, "r") as f_in:
        log.info(f"Opening input file {args.file}.")
        reader = csv.reader(f_in, delimiter=args.delimiter)

        # find maximum number of columns in file
        # important only when delimiter is whitespace
        # as we then need to fill up shorter rows with empty entries
        max_columns = max([len(line) for line in reader])

        # when we are in the first row, we might want to highlight the headers
        first_line = True

        # csv reader is like generator, i.e. we need to go back to start of file
        f_in.seek(0)

        for line in reader:

            # filling up shorter rows here
            n_missing_columns = max_columns - len(line)
            line.extend(n_missing_columns * [" "])
            
            # need to escape vertical bar characters as they are used in TWiki table syntax
            escaped_line = [l.replace("|", "&#124;") for l in line]
            
            # highlight headers
            if first_line:
                first_line = False
                if args.highlight_header:
                    log.info(f"Highlighting header row.")
                    row = f"| * {' * | * '.join(escaped_line)} * |\n"
                    f_out.write(row)
                    continue

            # else, just write out the line in TWiki table format
            row = f"| {' | '.join(escaped_line)} |\n"
            f_out.write(row)

    f_out.write(f"<!-- This file was created automatically from {inputfile}. Do not edit it manually. -->\n")
 
log.info(f"Closing output file {outputfile}.")
