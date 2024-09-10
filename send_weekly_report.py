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
    return f"{sanitised_name} [{", ".join(link_strings)}]"

@lru_cache
def get_finished_analyses():
    analyses = []
    with open("finished_analyses.txt", "r") as f:
        for line in f:
            analyses.append(line.rstrip())
    return analyses 

def analysis_finished(analysis: str):
    xmark = "x"
    checkmark = "\\checkmark"
    glance_code_list = get_glance_codes()
    if analysis not in glance_code_list.keys():
        return xmark
    glance_codes = glance_code_list[analysis].split(",")
    finished_analyses = get_finished_analyses()
    for glance_code in glance_codes:
        if glance_code not in finished_analyses:
            return xmark
    return checkmark

def main():
    subgroup_information = {}
    for subgroup in SUBGROUPS:
        analysis_data = get_data_from_git_history(subgroup=subgroup, days_ago=[0, 6])
        subgroup_information[subgroup] = analysis_data
        print(analysis_data)

    total_size = 0
    total_size_last_week = 0
    total_size_finished = 0
    largest_total_size = 0
    total_number = 0
    total_number_last_week = 0
    total_number_finished = 0
    most_total_number = 0
    largest = []
    largest_change = []
    largest_increase = []
    most = []
    most_change = []
    most_increase = []

    LAST_WEEK = (TODAY - datetime.timedelta(6)).strftime("%Y-%m-%d")
    for subgroup, subgroup_data in subgroup_information.items():
        for analysis, analysis_data in subgroup_data.items():
            available_last_week = LAST_WEEK in analysis_data
            size = analysis_data[TODAY.strftime("%Y-%m-%d")]["size"]
            size_last_week = 0 if not available_last_week else analysis_data[LAST_WEEK]["size"]
            size_increase = size - size_last_week 
            numbers = analysis_data[TODAY.strftime("%Y-%m-%d")]["number_of_files"]
            numbers_last_week = 0 if not available_last_week else analysis_data[LAST_WEEK]["number_of_files"]
            numbers_increase = numbers - numbers_last_week
            total_size += size
            total_size_last_week += size_last_week
            if size/MAX_DISK_SPACE>0.01: 
                largest.append((size, subgroup, analysis))
                largest_total_size += size
            if size_increase > 1024*1024: # only show increases of at least 1GB
                largest_increase.append((size_increase, subgroup, analysis, size))
                largest_increase.sort(reverse=True, key=lambda x: x[0])
                # only show the 10 largest increases
                if len(largest_increase) > 10:
                    largest_increase.pop()
            total_number += numbers
            total_number_last_week += numbers_last_week
            if analysis_finished(analysis) == "\\checkmark":
                total_number_finished += numbers
                total_size_finished += size
            if numbers/MAX_FILE_NUMBER>0.01: 
                most.append((numbers, subgroup, analysis))
                most_total_number += numbers
                if numbers_increase > 0:
                    most_increase.append((numbers_increase, subgroup, analysis, numbers))
                    most_increase.sort(reverse=True, key=lambda x: x[0])
                    if len(most_increase) > 10:
                        most_increase.pop()

    largest.sort(reverse=True, key=lambda x: x[0])
    most.sort(reverse=True, key=lambda x: x[0])

    latex_code = f"""
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
\\huge\\bfseries {TODAY.strftime("%Y-%m-%d")}
\\end{{center}}
This document is automically created once a week by the {link_string(f'https://{os.getenv("CI_SERVER_HOST")}/{os.getenv("CI_PROJECT_PATH")}', "ExoticsDiskspaceUsage monitoring tools")}.
It is meant to give a comprehensive overview of the status of the Exotics diskspace and any changes that have occurred during the previous week.
The current total diskspace used is {convert_units(total_size)}, {round(total_size/MAX_DISK_SPACE*100, 1)}\\% of the {convert_units(MAX_DISK_SPACE)} available to the Exotics group, {"an increase" if total_size>total_size_last_week else "a decrease"} of {round(abs(1-total_size/total_size_last_week)*100, 1)}\\% compared to the previous week. {round(total_size_finished/total_size*100, 1)}\\% of the used space belongs to analyses with their paper accepted by the journal.
A total of {total_number} files is stored in the Exotics diskspace, amounting to {round(total_number/MAX_FILE_NUMBER*100, 1)}\\% of the maximum {MAX_FILE_NUMBER} allowed, {"an increase" if total_number>total_number_last_week else "a decrease"} of {round(abs(1-total_number/total_number_last_week)*100, 1)}\\% compared to the previous week.
More detailed numbers, automatically updated daily, can be found in the {link_string('https://twiki.cern.ch/twiki/bin/viewauth/Sandbox/VolkerAndreasAustrupSandbox', 'Exotics Diskspace TWiki page')}.\\\\
\\\\
\\Cref{{tab:largest_directories}} lists all analysis directories using more than 1\\% of the diskspace available to the Exotics group each.
In total, this list comprises {len(largest)} directories, accounting for {round(largest_total_size/MAX_DISK_SPACE*100, 1)}\\% of the total available diskspace.
\\begin{{table}}[h]
\\centering
\\caption{{Analysis directories using more than 1\\% of the available diskspace. Links in brackets behind the directory names lead to the respective analysis Glance pages.}}
\\label{{tab:largest_directories}}
\\begin{{tabular}}{{cccccc}}
\\toprule
         &          &          &                     & \\multicolumn{{2}}{{c}}{{\\% of all}} \\\\ 
Analysis & Finished & Subgroup & Diskspace used [GB] & used space & space \\\\
\\midrule
"""
    for analysis in largest:
        latex_code += f"""
{analysis_link(analysis[2])} & {analysis_finished(analysis[2])} & {analysis[1].upper()} & {int(analysis[0]/1024**2)} & {round(analysis[0]/total_size*100, 1)} & {round(analysis[0]/MAX_DISK_SPACE*100, 1)}\\\\
    """
    latex_code += f"""
\\bottomrule
\\end{{tabular}}
\\end{{table}}

\\begin{{table}}[h]
\\centering
\\caption{{Analysis directories with the largest changes in diskspace used. Links in brackets behind the directory names lead to the respective analysis Glance pages.}}
\\label{{tab:largest_increase_directories}}
\\begin{{tabular}}{{ccccc}}
\\toprule
        &          &                     & \\multicolumn{{2}}{{c}}{{Increase wrt previous week}} \\\\ 
Analysis & Subgroup & Diskspace used [GB] & in GB & in \\% \\\\
\\midrule
    """
    for analysis in largest_increase:
        latex_code += f"""
{analysis_link(analysis[2])} & {analysis[1].upper()} & {int(analysis[3]/1024**2)} & {int(analysis[0]/1024**2)} & {"$\\infty$" if analysis[3]==analysis[0] else round(analysis[0]/(analysis[3]-analysis[0])*100, 1)}\\\\
    """
    latex_code += f"""
\\bottomrule
\\end{{tabular}}
\\end{{table}}
\\newpage
\\Cref{{tab:most_directories}} lists all analysis directories containing more than 1\\% of the maximum allowed number of files to be stored on the Exotics diskspace.
The list comprises {len(most)} directories, accounting for {round(most_total_number/MAX_FILE_NUMBER*100, 1)}\\% of the total maximum number of files.
\\begin{{table}}[h]
\\centering
\\caption{{Analysis directories containing more than 1\\% of the maximum allowed number of files. Links in brackets behind the directory names lead to the respective analysis Glance pages.}}
\\label{{tab:most_directories}}
\\begin{{tabular}}{{cccccc}}
\\toprule
Analysis & Finished & Subgroup & Number of files & \\% of all files & \\% of all allowed files \\\\
\\midrule
    """
    for analysis in most:
        latex_code += f"""
{analysis_link(analysis[2])} & {analysis_finished(analysis[2])} & {analysis[1].upper()} & {analysis[0]} & {round(analysis[0]/total_number*100, 1)} & {round(analysis[0]/MAX_FILE_NUMBER*100, 1)}\\\\
    """
    latex_code += """
\\bottomrule
\\end{tabular}
\\end{table}
    """
    latex_code += f"""
\\begin{{table}}[h]
\\centering
\\caption{{Analysis directories with the largest increases in numbers of files stored. Links in brackets behind the directory names lead to the respective analysis Glance pages.}}
\\label{{tab:most_increase_directories}}
\\begin{{tabular}}{{ccccc}}
\\toprule
        &          &                 & \\multicolumn{{2}}{{c}}{{Increase wrt previous week}} \\\\          
Analysis & Subgroup & Number of files & absolute & in \\% \\\\
\\midrule
    """
    for analysis in most_increase:
        latex_code += f"""
{analysis_link(analysis[2])} & {analysis[1].upper()} & {analysis[3]} & {analysis[0]} & {"$\\infty$" if analysis[3]==analysis[0] else round(analysis[0]/(analysis[3]-analysis[0])*100, 1)}\\\\
    """
    latex_code += """
\\bottomrule
\\end{tabular}
\\end{table}
\\end{document}
    """
    with open("latex.tex", "w") as f:
        f.write(latex_code)

    # run latex three times to make sure references are properly set
    subprocess.run(["pdflatex", "latex.tex"])
    subprocess.run(["pdflatex", "latex.tex"])
    subprocess.run(["pdflatex", "latex.tex"])


    msg = EmailMessage()
    msg.set_content(f"This is the weekly report on the usage of the Exotics Disk Space. It is automatically generated by the tools in https://{os.getenv("CI_SERVER_HOST")}/{os.getenv("CI_PROJECT_PATH")}. Please see the attachment for details.")
    msg["To"] = ', '.join(REPORT_LIST)
    msg["From"] = "exotics.diskspace.watcher@cern.ch"
    msg["Subject"] = "Weekly Exotics Diskspace Report"
    with open("latex.pdf", "rb") as f:
        attachment = f.read()
        msg.add_attachment(attachment, maintype='application', subtype='pdf', filename=f'exoticsdiskspace_report_{TODAY}.pdf')

    log.info(f"Sending weekly report to {msg['To']}.")

    # this only works from within the CERN network
    # see https://mailservices.docs.cern.ch/Miscellaneous/Anonymous_smtp/
    s = smtplib.SMTP(host='cernmx.cern.ch', port=25)
    s.send_message(msg)
    s.quit()

if __name__ == "__main__":
    main()