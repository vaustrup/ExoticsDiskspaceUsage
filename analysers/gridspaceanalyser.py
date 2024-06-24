import csv
import re

from rucio.client import Client

from helpers.logger import log


class GridSpaceAnalyser:

    def __init__(self, rse="CERN-PROD_PHYS-EXOTICS"):
        self._client = Client()
        self._scopes = {}
        self._scopes_not_found = []
        self._analyses = {"uncategorised": {"ntotal": 0, "ntotal_nolimit": 0, "size": 0}}
        self._rse = rse

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
                    self._analyses[analysis_name] = {"ntotal": 0, "ntotal_nolimit": 0, "size": 0}

    def analyse_datasets(self) -> None:
        '''
        Loop over all datasets on the RSE and match them to analyses.
        '''
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

    def replica_lifetime_is_limited(self, scope: str, name: str) -> bool:
        '''
        Check if the lifetime of a given dataset is limited on the group disk
        Arguments:
            scope: str -> scope to check
            name: str -> name of dataset to check
        Return:
            True if lifetime of dataset on group disk is limited, False otherwise
        '''
        try:
            replica_information = next(self._client.list_replication_rules(filters={"scope": scope, "name": name, "rse_expression": self._rse}))
            if replica_information["expires_at"] is None:
                log.debug(f"Rule for file {name} in scope {scope} will never expire.")
                return False
        except StopIteration:
            log.debug(f"Rule for file {name} in scope {scope} for site {self._rse} has been deleted or has never existed in the first place.")
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
            writer.writerow(["Analysis", "Number of Files", "Disk Usage in GB", "Number of Files without Expiration"])
            for name, details in self._analyses.items():
                size = float(f"{(details['size']/1024.**3):.5g}")
                writer.writerow([name, details["ntotal"], f'{size:g}', details["ntotal_nolimit"]])
                log.info(f"{name}  {details['ntotal']} {size:g} {details['ntotal_nolimit']}")