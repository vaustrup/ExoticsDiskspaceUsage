import datetime
import matplotlib.pyplot as plt
import subprocess
import sys

from matplotlib.dates import DateFormatter, DayLocator

import logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)4s]: %(message)s", "%d.%m.%Y %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)


SUBGROUPS = ["cdm", "hqt", "jdm", "lpx", "ueh"]
TODAY = datetime.datetime.now()
NUMBER_OF_DAYS = 100

def sort_analyses(analyses):
    '''
    sort analyses by their total size
    returns list of sorted analysis names
    TODO
    '''
    analysis_names = analyses.keys()
    return analysis_names

def get_data_from_git_history(subgroup: str):
    '''
    read historic analysis data from git history
    Arguments:
        subgroup: str -> name of subgroup to get analysis data for
    Returns:
        dictionary with analysis names as keys
        and dictionaries {'size': size, 'number_of_files': number_of_files} 
        as values
    '''
    log.info(f"Collecting information for subgroup {subgroup}.")
    analysis_data = {}
    for i_day in range(-1,NUMBER_OF_DAYS):
        date = (TODAY - datetime.timedelta(i_day)).strftime("%Y-%m-%d")
        command = f'git show $(git rev-list -1 --before="{date}" HEAD):reports/{subgroup}.csv'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        analyses = [x for x in result.stdout.split("\n") if x!='']
        for analysis in analyses:
            # skip header of CSV file
            if "Number of files" in analysis:
                continue
            # Analysis name is first column, disk space second column, and number of files third column
            data = analysis.split(",")
            name = data[0]
            size = int(data[1])
            number_of_files = int(data[2])
            # need to create empty dict for each analysis if it does not exist yet
            if name not in analysis_data:
                analysis_data[name] = {}
            analysis_data[name][date] = {"size": size, "number_of_files": number_of_files}
    return analysis_data

for subgroup in SUBGROUPS:
    log.info(f"Creating summary plot for subgroup {subgroup}.")
    analysis_data = get_data_from_git_history(subgroup)
    plt.figure(figsize=(10,6))
    sorted_analysis_names = sort_analyses(analysis_data)
    for name in sorted_analysis_names:
        information = analysis_data[name]
        dates = [datetime.datetime.strptime(date, "%Y-%m-%d") for date in information.keys()]
        sizes = [s["size"] for s in information.values()]
        numbers = [n["number_of_files"] for n in information.values()]
        plt.plot(dates, sizes, label=name)
    date_formatter = DateFormatter('%Y-%m-%d')
    plt.gca().xaxis.set_major_formatter(date_formatter)
    plt.gca().xaxis.set_major_locator(DayLocator(interval=int(NUMBER_OF_DAYS/10)))
    plt.xlabel("Date")
    plt.ylabel("Disk Space [kB]")
    plt.xticks(rotation=90)
    legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    legend.set_bbox_to_anchor((1.02, 0.5))
    plt.figtext(0.15, 0.96, f'{subgroup.upper()}, last updated: {TODAY.strftime("%Y-%m-%d")}', fontsize=12, ha='left')
    plt.tight_layout()
    plt.savefig(f"reports/{subgroup}.pdf")
