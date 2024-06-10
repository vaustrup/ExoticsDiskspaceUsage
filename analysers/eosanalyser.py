import csv
import os

from helpers.constants import GLANCE_CODES
from helpers.logger import log

class EOSAnalyser:

    def __init__(self, directory: str):
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

    def check_subgroup(self, subgroup: str) -> None:
        '''
        Compile report for each subgroup, listing disk space and number of files for each analysis in given subgroup.
        The reports are written to one csv file per subgroup and stored in the directory 'reports/'.
        Arguments:
            subgroup: str -> name of subgroup to report on       
        '''
        log.info(f"Checking subgroup {subgroup}.")
        # get the used disk space in units of bytes
        directory = f"{self._directory}/{subgroup}"
        analysis_names = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]
        sizes = []
        numbers = []
        for analysis in analysis_names:
            number_of_files = 0
            size = 0
            for dirpath, _, filenames in os.walk(f"{self._directory}/{subgroup}/{analysis}"):
                number_of_files += len(filenames)
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.isfile(filepath):
                        size += os.path.getsize(filepath)
            numbers.append(number_of_files)
            sizes.append(size)

        total_size = sum(sizes)
        total_numbers = sum(numbers)
        with open(f'reports/{subgroup}.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(["Analysis Team", "Disk Usage in GB", "Number of files", "Glance code"])
            for i in range(0, len(analysis_names)):
                writer.writerow([analysis_names[i], f'{float(f"{(sizes[i]/1024.**3):.5g}"):g}', numbers[i], self.glance_ref_from_name(analysis_names[i])])

            writer.writerow(["Total Sum", f'{float(f"{(total_size/1024.**3):.5g}"):g}', total_numbers, ""])
