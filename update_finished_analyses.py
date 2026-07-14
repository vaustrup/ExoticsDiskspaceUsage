from stare import Glance

from analysers.publicationanalyser import PublicationAnalyser
from helpers.constants import get_glance_codes
from helpers.logger import log

FINISHED_ANALYSES_FILE = "finished_analyses.txt"


def main():
    with open(FINISHED_ANALYSES_FILE) as f:
        finished = {line.strip() for line in f if line.strip()}

    glance_codes = get_glance_codes()
    all_codes = set()
    for codes in glance_codes.values():
        if codes == "N/A":
            continue
        all_codes.update(codes.split(","))

    analyser = PublicationAnalyser(Glance())
    newly_finished = analyser.find_newly_finished(all_codes, finished)

    if not newly_finished:
        log.info("No new finished analyses found.")
        return

    finished.update(newly_finished)
    with open(FINISHED_ANALYSES_FILE, "w") as f:
        for code in sorted(finished):
            f.write(f"{code}\n")
    log.info(f"Added {len(newly_finished)} newly finished analyses to {FINISHED_ANALYSES_FILE}.")


if __name__ == "__main__":
    main()
