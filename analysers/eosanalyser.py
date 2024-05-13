import csv
import os
import subprocess

from helpers.logger import log

class EOSAnalyser:

    def __init__(self, directory: str):
        self._password = os.getenv('PASSWORD')
        self._directory = directory
       
        self._glance_codes = {}
        with open("glance_codes.csv") as f:
            r = csv.reader(f, delimiter=' ')
            for row in r:
                name = row[0]
                code = row[1]
                self._glance_codes[name] = code

        self._analyses_without_glance: list[str] = []


    def glance_ref_from_name(self, name: str) -> str:
        '''
        Look up Glance reference code based on analysis/directory name
        Arguments:
            name: str -> analysis name to retrieve Glance reference code for
        Return:
            Glance reference code as string, empty string if analysis name is not in 'glance_codes.csv'
        '''
        if name not in self._glance_codes.keys():
            log.warning(f"Could not find Glance reference code for analysis {name}.")
            self._analyses_without_glance.append(name)
            return ""
        return self._glance_codes[name].replace(",","/")

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
            numbers.append(content[i])
            size, name = content[i+1].split('\t')
            sizes.append(int(size))
            analysis_names.append(os.path.basename(os.path.normpath(name)))
            i+=2

        with open(f'reports/{subgroup}.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(["Analysis Team", "Disk Usage in GB", "Number of files", "Glance code"])
            for i in range(0, len(analysis_names)):
                writer.writerow([analysis_names[i], f'{float(f"{(sizes[i]/1024.**2):.5g}"):g}', numbers[i], self.glance_ref_from_name(analysis_names[i])])