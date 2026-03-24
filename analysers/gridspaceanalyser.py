import csv
import math
import pandas as pd
import pathlib
import re
from datetime import datetime, timezone

from rucio.client import Client

from helpers.logger import log


class GridSpaceAnalyser:

    def __init__(self, rse="CERN-PROD_PHYS-EXOTICS", date: str|None = None):
        self._client = Client()
        self._scopes = {}
        self._scopes_not_found = []
        self._analyses = {"uncategorised": {"ntotal": 0, "ntotal_nolimit": 0, "ntotal_old": 0, "size": 0}}
        self._rse = rse
        self._date = date
        self.report_path = pathlib.Path("/eos/atlas/atlascerngroupdisk/data-adc/rucio-analytix/reports/")

    @property
    def date(self):
        if self._date is not None:
            return self._date
        pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
        latest_dir = max(d.name for d in self.report_path.iterdir() if d.is_dir() and pattern.match(d.name))
        return latest_dir

    def load_lookup_table(self) -> None:
        '''
        Tags matched to specific analyses are listed in 'lookup_table.csv' as '<scope> <tag> <glance-code>'.
        These are loaded into self._scopes in order to match files on the group disk to analyses.
        '''
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
                    self._analyses[analysis_name] = {"ntotal": 0, "ntotal_nolimit": 0, "ntotal_old": 0, "size": 0}

    def analyse_datasets(self) -> None:
        '''
        Loop over all datasets on the RSE and match them to analyses.
        '''
        header = ['RSE', 'scope', 'name', 'account', 'size', 'created', 'updated', 'accessed', 'ruleid', 'state']

        f = self.report_path / self.date / "datasets_per_rse" / f"{self._rse}.datasets_per_rse.{self.date}.csv.bz2"
        reader = pd.read_csv(f, header=None, names=header, compression='bz2', delimiter="\t")
        for line in reader.itertuples(index=False):
            scope = line.scope
            if not self.scope_is_valid(scope):
                continue            
            name = line.name
            size = line.size
            limited = self.replica_lifetime_is_limited(line.ruleid)
            old = self.replica_is_old(line.created, line.updated, line.accessed)
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
                if old:
                    self._analyses[analysis_name]["ntotal_old"] += 1
        self.check_obsolete_tags()

    def scope_is_valid(self, scope: str) -> bool:
        '''
        Check if a given scope is available in the lookup table.
        Arguments:
            scope: str -> scope to check
        Return:
            True if scope is in the lookup table, False otherwise
        '''
        if scope not in self._scopes:
            if scope not in self._scopes_not_found:
                log.warning(f"Could not find scope {scope} in list of scopes.")
                self._scopes_not_found.append(scope)
            return False
        return True

    def match_tags(self, scope: str, name: str) -> list:
        '''
        Match dataset names in a given scope to the tags in the lookup table.
        Arguments:
            scope: str -> scope to match
            name: str -> name of dataset to match
        Return:
            list of tags matching given name in the given scope
        '''
        matching_tags = []
        for tag in self._scopes[scope]:
            if re.search(tag, name) is not None:
                matching_tags.append(tag)
                self._scopes[scope][tag]["tag_found"] = True
        if len(matching_tags) == 0:
            log.warning(f"Could not find any tags for file {name} in scope {scope}.")
            return []
        if len(matching_tags) > 1:
            log.warning(f"Found multiple tags matching file {name} in scope {scope}.")
        return matching_tags

    def replica_is_old(self, created, updated, accessed,threshold: int = 365*24*60*60) ->bool:
        def parse_time(t):
            if t is None or pd.isna(t):
                return None
            return datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()
        
        times = [parse_time(created), parse_time(updated), parse_time(accessed)]
        times = [t for t in times if t is not None]
        if not times:
            return False
        maxtime = max(times)
        return (datetime.now(timezone.utc).timestamp() - maxtime) > threshold
        
    def replica_lifetime_is_limited(self, ruleid: str) -> bool:
        '''
        Check if the lifetime of a given dataset is limited on the group disk
        Arguments:
            scope: str -> scope to check
            name: str -> name of dataset to check
        Return:
            True if lifetime of dataset on group disk is limited, False otherwise
        '''
        if isinstance(ruleid, float) and math.isnan(ruleid):
            return False
        
        ids = ruleid.split(",")
        for i in ids:
            rule = self._client.get_replication_rule(i)
            if rule["expires_at"] is None:
                return False
        return True

    def check_obsolete_tags(self) -> None:
        '''
        Print a warning if a tag in the lookup table was not found in any of the samples.
        This can mean it is obsolete and should be removed from the lookup table, or it points to a typo. 
        Either way, make sure to check if this warning is raised in order to keep things organised.
        '''
        for _, tags in self._scopes.items():
            for tag, details in tags.items():
                if not details["tag_found"]:
                    log.warning(f"Tag {tag} was not found in any of the samples. Maybe it is obsolete?")

    def report(self) -> None:
        '''
        Create report for each RSE, stored as CSV file in 'reports/'
        '''
        log.info(f"Creating report for {self._rse}.")
        with open(f'reports/{self._rse}.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(["Analysis", "Number of Files", "Disk Usage in GB", "Number of Files without Expiration", "Number of Files accessed >1 year ago"])
            for name, details in self._analyses.items():
                size = float(f"{(details['size']/1024.**3):.5g}")
                writer.writerow([name, details["ntotal"], f'{size:g}', details["ntotal_nolimit"], details["ntotal_old"]])
                log.info(f"{name}  {details['ntotal']} {size:g} {details['ntotal_nolimit']} {details['ntotal_old']}")
