import csv
import datetime

TODAY = datetime.datetime.now()
SUBGROUPS = ["ccs", "cdm", "hqt", "jdm", "jmx", "lpx", "lup", "ueh"]

GITLAB_USER_ID = 6032

def get_glance_codes():
    glance_codes = {}
    with open("glance_codes.csv") as f:
        r = csv.reader(f, delimiter=' ')
        for row in r:
            name = row[0]
            code = row[1]
            glance_codes[name] = code
    return glance_codes

MAX_DISK_SPACE = 155 * 1024**3 # in kB
MAX_FILE_NUMBER = int(2.5e6)

REPORT_LIST = ["volker.andreas.austrup@cern.ch"]