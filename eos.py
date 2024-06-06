import argparse

from analysers.eosanalyser import EOSAnalyser
from helpers.constants import SUBGROUPS
from helpers.logger import log
from helpers.gitlab import report_missing_glance_code

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--subgroups", nargs="+", default=SUBGROUPS, help="Specify subgroups to check.")
parser.add_argument("--sshpass", action="store_true", help="Use 'sshpass' utility for ssh password.")
parser.add_argument("--report-in-gitlab", action="store_true", help="Automatically report findings (missing information, ...) in Gitlab issue.")
args = parser.parse_args()

for s in args.subgroups:
    if s not in SUBGROUPS:
        log.warning(f"Subgroup {s} was not found in list of subgroups.")
        args.subgroups.remove(s)

analyser = EOSAnalyser(directory="/eos/atlas/atlascerngroupdisk/phys-exotics/")

for subgroup in args.subgroups:
    analyser.check_subgroup(subgroup, sshpass=args.sshpass)

if args.report_in_gitlab:
    report_missing_glance_code(analyser._analyses_without_glance)
