import datetime
import subprocess

from helpers.logger import log

def get_data_from_git_history(subgroup: str, days_ago: list[int]):
    '''
    read historic analysis data from git history
    Arguments:
        subgroup: str -> name of subgroup to get analysis data for
        days_ago: list[int] -> list of past days to collect information for (0 for today, 1 for yesterday etc.)
    Returns:
        dictionary with analysis names as keys
        and dictionaries {'size': size, 'number_of_files': number_of_files} 
        as values
    '''
    log.info(f"Collecting information for subgroup {subgroup}.")
    TODAY = datetime.datetime.now()
    analysis_data = {}
    for i_day in days_ago:
        date = (TODAY - datetime.timedelta(i_day)).strftime("%Y-%m-%d")
        print(date)
        before_date = (TODAY - datetime.timedelta(i_day-1)).strftime("%Y-%m-%d")
        command = f'git show $(git rev-list -1 --before="{before_date}" HEAD):reports/{subgroup}.csv'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stderr)
        print(result.stdout)
        analyses = [x for x in result.stdout.split("\n") if x!='']
        isInGB = False
        for analysis in analyses:
            # skip header of CSV file
            if "Disk Usage" in analysis:
                isInGB = "Disk Usage in GB" in analysis
                continue
            # Analysis name is first column, disk space second column, and number of files third column
            data = analysis.split(",")
            name = data[0]
            # we do not want to plot the sum of all analyses in a given subgroup
            if name == "Total Sum":
                continue
            # convert back to kB if disk space given in GB
            size = int(float(data[1])*1024**2) if isInGB else int(data[1])
            number_of_files = int(data[2])
            # need to create empty dict for each analysis if it does not exist yet
            if name not in analysis_data:
                analysis_data[name] = {}
            analysis_data[name][date] = {"size": size, "number_of_files": number_of_files}
    return analysis_data