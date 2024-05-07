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
    while x/CONVERSION_FACTOR > CONVERSION_FACTOR and i_unit < len(UNITS):
        x = x/CONVERSION_FACTOR
        i_unit += 1
    return f'{x} {UNITS[i_unit]}'


def check_subgroup(subgroup: str, sshpass: bool = False) -> None:
    '''
    Compile report for each subgroup, listing disk space and number of files for each analysis in given subgroup.
    The reports are written to one csv file per subgroup and stored in the directory 'reports/'.
    Arguments:
        subgroup: str -> name of subgroup to report on
        sshpass: bool -> whether to run commands through sshpass, necessary when not running on lxplus (default: False).
                         if true, log into exowatch lxplus account, using password stored as environment variable        
    '''
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
        writer.writerow(["Analysis Team", "Disk Usage in GB", "Number of files"])
        for i in range(0, len(analysis_names)):
            writer.writerow([analysis_names[i], f'{float(f"{(sizes[i]/1024.**2):.5g}"):g}', numbers[i]])

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
