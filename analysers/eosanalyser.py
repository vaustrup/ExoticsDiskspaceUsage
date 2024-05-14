import csv
import os
import subprocess

from helpers.constants import GLANCE_CODES
from helpers.logger import log

class EOSAnalyser:

    def __init__(self, directory: str):
        self._password = os.getenv('PASSWORD')
        self._directory = directory
        self._analyses_without_glance: list[str] = []


    def glance_ref_from_name(self, name: str) -> str:
        '''
        Look up Glance reference code based on analysis/directory name
        Arguments:
            name: str -> analysis name to retrieve Glance reference code for
        Return:
            Glance reference code as string, empty string if analysis name is not in 'glance_codes.csv'
        '''
        if name not in GLANCE_CODES.keys():
            log.warning(f"Could not find Glance reference code for analysis {name}.")
            self._analyses_without_glance.append(name)
            return ""
        return GLANCE_CODES[name].replace(",","/")

    def check_subgroup(self, subgroup: str, sshpass: bool = False) -> None:
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
        COMMAND = f"for dir in {self._directory}/{subgroup}/*/; do find \\$dir -type f | wc -l; du -s -B 1024 \\$dir; done"
        pass_command = f"sshpass -p {self._password} " if sshpass else ""
        ssh_command = f'{pass_command}ssh -o StrictHostKeyChecking=no exowatch@lxplus.cern.ch "{COMMAND}"'
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
        content = [item for item in result.stdout.split("\n") if item!=""]

        i = 0
        analysis_names = []
        sizes = []
        numbers = []
        while i in range(0, len(content)):
            numbers.append(int(content[i]))
            size, name = content[i+1].split('\t')
            sizes.append(int(size))
            analysis_names.append(os.path.basename(os.path.normpath(name)))
            i+=2

        total_size = sum(sizes)
        total_numbers = sum(numbers)
        with open(f'reports/{subgroup}.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(["Analysis Team", "Disk Usage in GB", "Number of files", "Glance code"])
            for i in range(0, len(analysis_names)):
                writer.writerow([analysis_names[i], f'{float(f"{(sizes[i]/1024.**2):.5g}"):g}', numbers[i], self.glance_ref_from_name(analysis_names[i])])

        writer.writerow(["Total Sum", f'{float(f"{(total_size/1024.**2):.5g}"):g}', total_numbers, ""])
