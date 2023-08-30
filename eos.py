import argparse
import csv
import os
import subprocess

import logging
log = logging.getLogger(__name__)

PASSWORD = os.getenv('PASSWORD')
DIRECTORY = "/eos/atlas/atlascerngroupdisk/phys-exotics/"


def convert_units(size: int):
    '''
    Converts size given in kB into more adequate units
    Arguments:
        size: int -> size to convert, given in kB
    Return:
        string consisting of number and unit
    '''
    CONVERSION_FACTOR = 1024
    UNITS = ['kB', 'MB', 'GB', 'TB', 'PB']
    x = size
    i_unit = 0
    while x/CONVERSION_FACTOR > CONVERSION_FACTOR:
        x = x/CONVERSION_FACTOR
        i_unit += 1
    return f'{x} {UNITS[i_unit]}'


def check_subgroup(subgroup, sshpass=False):
    log.info(f"Checking subgroup {subgroup}.")
    # get the used disk space in units of kilobytes
    COMMAND = f"for dir in {DIRECTORY}/{subgroup}/*/; do find \$dir -type f | wc -l; du -s -B 1024 \$dir; done"
    pass_command = f"sshpass -p {PASSWORD} " if sshpass else ""
    ssh_command = f'{pass_command}ssh -o StrictHostKeyChecking=no exowatch@lxplus.cern.ch "{COMMAND}"'
    result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
    content = [item for item in result.stdout.split("\n") if item!=""]

    i = 0
    analysis_names = []
    sizes = []
    numbers = []
    while i in range(0, len(content)):
        numbers.append(content[i])
        size, name = content[i+1].split('\t')
        sizes.append(int(size))
        analysis_names.append(os.path.basename(os.path.normpath(name)))
        i+=2

    with open(f'reports/{subgroup}.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(["Analysisi Team", "Disk Usage in kB", "Number of files"])
        for i in range(0, len(analysis_names)):
            writer.writerow([analysis_names[i], sizes[i], numbers[i]])

    with open(f'reports/{subgroup}.table', 'w') as f:
        f.write('| *Analysis Team* | *Disk Usage* | *Number of Files* |')
        for i in range(0, len(analysis_names)):
            f.write(f'\n| {analysis_names[i]} | {convert_units(sizes[i])} | {numbers[i]} |')

subgroups = ["cdm", "hqt", "jdm", "lpx", "ueh"]
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--subgroups", nargs="+", default=subgroups, help="Specify subgroups to check")
parser.add_argument("--sshpass", action="store_true", help="Use 'sshpass' utility for ssh password.")
args = parser.parse_args()

for s in args.subgroups:
    if s not in subgroups:
        log.warning(f"Subgroup {s} was not found in list of subgroups.")
        args.subgroups.remove(s)

for subgroup in args.subgroups:
    check_subgroup(subgroup, sshpass=args.sshpass)
