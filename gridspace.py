import argparse
import csv
import logging
import re
import sys

from typing import List

from rucio.client import Client

log = logging.getLogger("gridspace")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)4s]: %(message)s", "%d.%m.%Y %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)


class GridSpaceAnalyser:

    def __init__(self, rse="CERN-PROD_PHYS-EXOTICS"):
        self._client = Client()
        self._scopes = {}
        self._scopes_not_found = []
        self._analyses = {"uncategorised": {"ntotal": 0, "ntotal_nolimit": 0, "size": 0}}
        self._rse = rse

    def load_lookup_table(self) -> None:
        with open('lookup_table.csv') as f:
            r = csv.reader(f, delimiter=' ')
            for row in r:
                scope = row[0]
                if scope not in self._scopes:
                    self._scopes[scope] = {}
                tag = row[1]
                self._scopes[scope][tag] = {"analysis": "", "tag_found": False}
                if len(row) < 3:
                    log.warning(f"Tag {tag} in scope {scope} is missing analysis reference.")
                else:
                    analysis_name = row[2]
                    self._scopes[scope][tag]["analysis"] = analysis_name
                    self._analyses[analysis_name] = {"ntotal": 0, "ntotal_nolimit": 0, "size": 0}

    def analyse_datasets(self) -> None:
        for line in self._client.list_datasets_per_rse(rse=self._rse):
            scope = line["scope"]
            if not self.scope_is_valid(scope):
                continue            
            name = line["name"]
            size = 0
            content = self._client.list_content(scope, name)
            for f in content:
                size += f["bytes"]
            limited = self.replica_lifetime_is_limited(scope, name)
            matching_tags = self.match_tags(scope, name) 
            if matching_tags is None:
                continue
            for tag in matching_tags:
                analysis_name = self._scopes[scope][tag]["analysis"]
                if analysis_name == "":
                    analysis_name = "uncategorised"
                self._analyses[analysis_name]["ntotal"] += 1
                self._analyses[analysis_name]["size"] += size
                if not limited:
                    self._analyses[analysis_name]["ntotal_nolimit"] += 1
        self.check_obsolete_tags()

    def scope_is_valid(self, scope: str) -> bool:
        if scope not in self._scopes:
            if scope not in self._scopes_not_found:
                log.warning(f"Could not find scope {scope} in list of scopes.")
                self._scopes_not_found.append(scope)
            return False
        return True

    def match_tags(self, scope: str, name: str) -> List:
        matching_tags = []
        for tag in self._scopes[scope]:
            if re.search(tag, name) is not None:
                matching_tags.append(tag)
                self._scopes[scope][tag]["tag_found"] = True
        if len(matching_tags) == 0:
            log.warning(f"Could not find any tags for file {name} in scope {scope}.")
            return
        if len(matching_tags) > 1:
            log.warning(f"Found multiple tags matching file {name} in scope {scope}.")
        return matching_tags

    def replica_lifetime_is_limited(self, scope: str, name: str) -> bool:
        try:
            replica_information = next(self._client.list_replication_rules(filters={"scope": scope, "name": name, "rse_expression": self._rse}))
            if replica_information["expires_at"] is None:
                log.info(f"Rule for file {name} in scope {scope} will never expire.")
                return False
        except StopIteration:
            log.debug(f"Rule for file {name} in scope {scope} for site {self._rse} has been deleted or has never existed in the first place.")
        return True

    def check_obsolete_tags(self) -> None:
        for scope, tags in self._scopes.items():
            for tag, details in tags.items():
                if not details["tag_found"]:
                    log.warning(f"Tag {tag} was not found in any of the samples. Maybe it is obsolete?")

    def report(self) -> None:
        log.info(f"Creating report for {self._rse}.")
        with open(f'reports/{self._rse}.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            for name, details in self._analyses.items():
                writer.writerow([name, details["ntotal"], details["size"], details["ntotal_nolimit"]])
                log.info(f"{name}  {details['ntotal']} {details['size']} {details['ntotal_nolimit']}")

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--rse", default="CERN-PROD_PHYS-EXOTICS", choices=["CERN-PROD_PHYS-EXOTICS", "TOKYO-LCG2_PHYS-EXOTICS"], help="RSE to check")
    args = parser.parse_args()

    analyser = GridSpaceAnalyser(rse=args.rse)
    analyser.load_lookup_table()
    analyser.analyse_datasets()
    analyser.report()

if __name__ == "__main__":
    main()
 