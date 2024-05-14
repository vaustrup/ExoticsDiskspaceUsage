import csv
import datetime

TODAY = datetime.datetime.now()
SUBGROUPS = ["cdm", "hqt", "jdm", "lpx", "ueh"]

GLANCE_CODES = {}
with open("glance_codes.csv") as f:
    r = csv.reader(f, delimiter=' ')
    for row in r:
        name = row[0]
        code = row[1]
        GLANCE_CODES[name] = code

MAX_DISK_SPACE = 155 * 1024**3 # in kB
MAX_FILE_NUMBER = int(2.5e6)