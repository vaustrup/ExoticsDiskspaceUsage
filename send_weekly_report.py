import datetime
from functools import lru_cache
import os
import smtplib
import subprocess

from email.message import EmailMessage

from helpers.constants import get_glance_codes, MAX_DISK_SPACE, MAX_FILE_NUMBER, REPORT_LIST, SUBGROUPS, TODAY
from helpers.git import get_data_from_git_history
from helpers.glance import get_glance_link_from_code
from helpers.logger import log
from helpers.utils import convert_units

CI_URL = f'https://{os.getenv("CI_SERVER_HOST")}/{os.getenv("CI_PROJECT_PATH")}'
TOP_N_INCREASES = 10
MIN_SHARE_TO_LIST = 0.01  # only list analyses using at least 1% of disk space/files
MIN_SIZE_INCREASE_KB = 1024 * 1024  # only show disk space increases of at least 1GB


def sanitise_latex(latex: str):
    return latex.replace("_", "\\_")

def link_string(url, text):
    return f"\\href{{{url}}}{{{text}}}"

def analysis_link(analysis: str):
    sanitised_name = sanitise_latex(analysis)
    glance_code_list = get_glance_codes()
    if analysis not in glance_code_list.keys():
        return sanitised_name
    glance_codes = glance_code_list[analysis].split(",")
    links = [get_glance_link_from_code(glance_code) for glance_code in glance_codes]
    link_strings = [link_string(link, str(i)) for i, link in enumerate(links, start=1)]
    return f"{sanitised_name} [{', '.join(link_strings)}]"

@lru_cache
def get_finished_analyses():
    with open("finished_analyses.txt", "r") as f:
        return [line.rstrip() for line in f]

def analysis_finished(analysis: str):
    xmark = "x"
    checkmark = "\\checkmark"
    glance_code_list = get_glance_codes()
    if analysis not in glance_code_list.keys():
        return xmark
    glance_codes = glance_code_list[analysis].split(",")
    finished_analyses = get_finished_analyses()
    if all(code in finished_analyses for code in glance_codes):
        return checkmark
    return xmark

def change_description(current, previous):
    return "an increase" if current > previous else "a decrease"

def format_increase_percent(current, increase):
    '''percentage increase relative to the value before the increase; "infinite" if there was nothing before'''
    previous = current - increase
    if previous == 0:
        return "$\\infty$"
    return f"{round(increase/previous*100, 1)}"

def render_table(caption, label, column_spec, header, rows):
    body = "\n".join(rows)
    return f"""
\\begin{{table}}[h]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
\\begin{{tabular}}{{{column_spec}}}
\\toprule
{header}
\\midrule
{body}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


def collect_subgroup_information():
    subgroup_information = {}
    for subgroup in SUBGROUPS:
        analysis_data = get_data_from_git_history(subgroup=subgroup, days_ago=[0, 6])
        subgroup_information[subgroup] = analysis_data
        print(analysis_data)
    return subgroup_information


def summarise(subgroup_information):
    '''
    Aggregate per-analysis size/file-count data into the totals and top-N lists
    used to build the report. Mirrors the semantics of the previous inline loop:
    largest_increase/most_increase are independently thresholded, while
    most_increase additionally requires the analysis to already be in "most".
    '''
    today_str = TODAY.strftime("%Y-%m-%d")
    last_week_str = (TODAY - datetime.timedelta(6)).strftime("%Y-%m-%d")

    totals = {
        "size": 0, "size_last_week": 0, "size_finished": 0, "largest_size": 0,
        "number": 0, "number_last_week": 0, "number_finished": 0, "most_number": 0,
    }
    largest = []
    largest_increase = []
    most = []
    most_increase = []

    for subgroup, subgroup_data in subgroup_information.items():
        for analysis, analysis_data in subgroup_data.items():
            available_last_week = last_week_str in analysis_data
            size = analysis_data[today_str]["size"]
            size_last_week = analysis_data[last_week_str]["size"] if available_last_week else 0
            size_increase = size - size_last_week
            numbers = analysis_data[today_str]["number_of_files"]
            numbers_last_week = analysis_data[last_week_str]["number_of_files"] if available_last_week else 0
            numbers_increase = numbers - numbers_last_week

            totals["size"] += size
            totals["size_last_week"] += size_last_week
            totals["number"] += numbers
            totals["number_last_week"] += numbers_last_week

            if analysis_finished(analysis) == "\\checkmark":
                totals["number_finished"] += numbers
                totals["size_finished"] += size

            if size / MAX_DISK_SPACE > MIN_SHARE_TO_LIST:
                largest.append((size, subgroup, analysis))
                totals["largest_size"] += size
            if size_increase > MIN_SIZE_INCREASE_KB:
                largest_increase.append((size_increase, subgroup, analysis, size))

            if numbers / MAX_FILE_NUMBER > MIN_SHARE_TO_LIST:
                most.append((numbers, subgroup, analysis))
                totals["most_number"] += numbers
                if numbers_increase > 0:
                    most_increase.append((numbers_increase, subgroup, analysis, numbers))

    largest.sort(reverse=True, key=lambda x: x[0])
    most.sort(reverse=True, key=lambda x: x[0])
    largest_increase.sort(reverse=True, key=lambda x: x[0])
    most_increase.sort(reverse=True, key=lambda x: x[0])

    return {
        "totals": totals,
        "largest": largest,
        "largest_increase": largest_increase[:TOP_N_INCREASES],
        "most": most,
        "most_increase": most_increase[:TOP_N_INCREASES],
    }


def build_latex(summary):
    totals = summary["totals"]
    largest = summary["largest"]
    largest_increase = summary["largest_increase"]
    most = summary["most"]
    most_increase = summary["most_increase"]
    today_str = TODAY.strftime("%Y-%m-%d")

    intro = f"""
\\documentclass{{article}}
\\usepackage[left=0.8in, right=0.8in, bottom=0.8in, top=0.8in]{{geometry}}
\\usepackage{{booktabs}}
\\usepackage[colorlinks=true, linkcolor=blue, urlcolor=blue]{{hyperref}}
\\usepackage{{placeins}}
\\usepackage{{cleveref}}
\\usepackage{{amssymb}}
\\begin{{document}}
\\begin{{center}}
\\Huge\\bfseries Exotics Diskspace Usage \\\\
\\huge\\bfseries Weekly Report \\\\
\\huge\\bfseries {today_str}
\\end{{center}}
This document is automically created once a week by the {link_string(CI_URL, "ExoticsDiskspaceUsage monitoring tools")}.
It is meant to give a comprehensive overview of the status of the Exotics diskspace and any changes that have occurred during the previous week.
The current total diskspace used is {convert_units(totals["size"])}, {round(totals["size"]/MAX_DISK_SPACE*100, 1)}\\% of the {convert_units(MAX_DISK_SPACE)} available to the Exotics group, {change_description(totals["size"], totals["size_last_week"])} of {round(abs(1-totals["size"]/totals["size_last_week"])*100, 1)}\\% compared to the previous week. {round(totals["size_finished"]/totals["size"]*100, 1)}\\% of the used space belongs to analyses with their paper accepted by the journal.
A total of {totals["number"]} files is stored in the Exotics diskspace, amounting to {round(totals["number"]/MAX_FILE_NUMBER*100, 1)}\\% of the maximum {MAX_FILE_NUMBER} allowed, {change_description(totals["number"], totals["number_last_week"])} of {round(abs(1-totals["number"]/totals["number_last_week"])*100, 1)}\\% compared to the previous week.
More detailed numbers, automatically updated daily, can be found in the {link_string('https://atlas-exot.docs.cern.ch/ExoStorageDocs/', 'Exotics Diskspace Documentation page')}.\\\\
\\\\
\\Cref{{tab:largest_directories}} lists all analysis directories using more than 1\\% of the diskspace available to the Exotics group each.
In total, this list comprises {len(largest)} directories, accounting for {round(totals["largest_size"]/MAX_DISK_SPACE*100, 1)}\\% of the total available diskspace.
"""

    largest_table = render_table(
        caption="Analysis directories using more than 1\\% of the available diskspace. Links in brackets behind the directory names lead to the respective analysis Glance pages.",
        label="tab:largest_directories",
        column_spec="cccccc",
        header="         &          &          &                     & \\multicolumn{2}{c}{\\% of all} \\\\\nAnalysis & Finished & Subgroup & Diskspace used [GB] & used space & space \\\\",
        rows=[
            f"{analysis_link(a[2])} & {analysis_finished(a[2])} & {a[1].upper()} & {int(a[0]/1024**2)} & {round(a[0]/totals['size']*100, 1)} & {round(a[0]/MAX_DISK_SPACE*100, 1)}\\\\"
            for a in largest
        ],
    )

    largest_increase_table = render_table(
        caption="Analysis directories with the largest changes in diskspace used. Links in brackets behind the directory names lead to the respective analysis Glance pages.",
        label="tab:largest_increase_directories",
        column_spec="ccccc",
        header="        &          &                     & \\multicolumn{2}{c}{Increase wrt previous week} \\\\\nAnalysis & Subgroup & Diskspace used [GB] & in GB & in \\% \\\\",
        rows=[
            f"{analysis_link(a[2])} & {a[1].upper()} & {int(a[3]/1024**2)} & {int(a[0]/1024**2)} & {format_increase_percent(a[3], a[0])}\\\\"
            for a in largest_increase
        ],
    )

    middle = f"""
\\newpage
\\Cref{{tab:most_directories}} lists all analysis directories containing more than 1\\% of the maximum allowed number of files to be stored on the Exotics diskspace.
The list comprises {len(most)} directories, accounting for {round(totals["most_number"]/MAX_FILE_NUMBER*100, 1)}\\% of the total maximum number of files.
"""

    most_table = render_table(
        caption="Analysis directories containing more than 1\\% of the maximum allowed number of files. Links in brackets behind the directory names lead to the respective analysis Glance pages.",
        label="tab:most_directories",
        column_spec="cccccc",
        header="Analysis & Finished & Subgroup & Number of files & \\% of all files & \\% of all allowed files \\\\",
        rows=[
            f"{analysis_link(a[2])} & {analysis_finished(a[2])} & {a[1].upper()} & {a[0]} & {round(a[0]/totals['number']*100, 1)} & {round(a[0]/MAX_FILE_NUMBER*100, 1)}\\\\"
            for a in most
        ],
    )

    most_increase_table = render_table(
        caption="Analysis directories with the largest increases in numbers of files stored. Links in brackets behind the directory names lead to the respective analysis Glance pages.",
        label="tab:most_increase_directories",
        column_spec="ccccc",
        header="        &          &                 & \\multicolumn{2}{c}{Increase wrt previous week} \\\\\nAnalysis & Subgroup & Number of files & absolute & in \\% \\\\",
        rows=[
            f"{analysis_link(a[2])} & {a[1].upper()} & {a[3]} & {a[0]} & {format_increase_percent(a[3], a[0])}\\\\"
            for a in most_increase
        ],
    )

    return intro + largest_table + largest_increase_table + middle + most_table + most_increase_table + "\n\\end{document}\n"


def compile_pdf():
    # run latex three times to make sure references are properly set
    for _ in range(3):
        subprocess.run(["pdflatex", "latex.tex"])


def send_email():
    msg = EmailMessage()
    msg.set_content(f"This is the weekly report on the usage of the Exotics Disk Space. It is automatically generated by the tools in {CI_URL}. Please see the attachment for details.")
    msg["To"] = ', '.join(REPORT_LIST)
    msg["From"] = "exotics.diskspace.watcher@cern.ch"
    msg["Subject"] = "Weekly Exotics Diskspace Report"
    with open("latex.pdf", "rb") as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=f'exoticsdiskspace_report_{TODAY}.pdf')

    log.info(f"Sending weekly report to {msg['To']}.")

    # this only works from within the CERN network
    # see https://mailservices.docs.cern.ch/Miscellaneous/Anonymous_smtp/
    s = smtplib.SMTP(host='cernmx.cern.ch', port=25)
    s.send_message(msg)
    s.quit()


def main():
    subgroup_information = collect_subgroup_information()
    summary = summarise(subgroup_information)
    latex_code = build_latex(summary)

    with open("latex.tex", "w") as f:
        f.write(latex_code)

    compile_pdf()
    send_email()

if __name__ == "__main__":
    main()
