import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator

from helpers.constants import SUBGROUPS, TODAY
from helpers.git import get_data_from_git_history
from helpers.logger import log




def sort_analyses(analyses):
    '''
    sort analyses by their total size
    returns list of sorted analysis names
    TODO
    '''
    analysis_names = analyses.keys()
    return analysis_names


NUMBER_OF_DAYS = 100
for subgroup in SUBGROUPS:
    log.info(f"Creating summary plot for subgroup {subgroup}.")
    analysis_data = get_data_from_git_history(subgroup, days_ago=list(range(0, NUMBER_OF_DAYS)))
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
