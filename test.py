import csv
import os
import subprocess

import logging
log = logging.getLogger(__name__)

PASSWORD = os.getenv('PASSWORD')
DIRECTORY = "/eos/atlas/atlascerngroupdisk/phys-exotics/"


def check_subgroup(subgroup):
    log.info(f"Checking subgroup {subgroup}.")
    COMMAND = f"for dir in {DIRECTORY}/{subgroup}/*/; do find \$dir -type f | wc -l; du -sh \$dir; done"
    ssh_command = f'sshpass -p {PASSWORD} ssh -o StrictHostKeyChecking=no vaustrup@lxplus.cern.ch "{COMMAND}"'
    result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
    content = [item for item in result.stdout.split("\n") if item!=""]

    i = 0
    analysis_names = []
    sizes = []
    numbers = []
    while i in range(0, len(content)):
        numbers.append(content[i])
        size, name = content[i+1].split('\t')
        sizes.append(size)
        analysis_names.append(os.path.basename(os.path.normpath(name)))
        i+=2

    with open(f'reports/{subgroup}.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for i in range(0, len(analysis_names)):
            writer.writerow([analysis_names[i], sizes[i], numbers[i]])


subgroups = ["cdm", "hqt", "jdm", "lpx", "ueh"]
for subgroup in subgroups:
    check_subgroup(subgroup)
