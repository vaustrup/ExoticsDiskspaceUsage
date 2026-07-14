from stare import Glance

from helpers.logger import log


class PublicationAnalyser:

    def __init__(self, client: Glance | None = None):
        self._client = client or Glance()

    def is_accepted_by_journal(self, glance_code: str) -> bool:
        '''
        Check whether the paper linked to the given analysis has been accepted by a journal.
        Arguments:
            glance_code: str -> analysis reference code, e.g. "ANA-EXOT-2019-35"
        Return:
            True if a paper is linked to the analysis and has a recorded journal acceptance date, False otherwise
        '''
        analysis = self._client.analyses.get(glance_code)
        for related in analysis.related_publications:
            if related.type != "Paper" or not related.reference_code:
                continue
            paper = self._client.papers.get(related.reference_code)
            if paper.publication_phase and paper.publication_phase.journal_acceptance_date:
                return True
        return False

    def find_newly_finished(self, glance_codes: set[str], already_finished: set[str]) -> list[str]:
        '''
        Check publication status for every glance code not yet marked as finished.
        Arguments:
            glance_codes: set[str] -> all known analysis reference codes
            already_finished: set[str] -> reference codes already marked as finished
        Return:
            list of reference codes whose paper has newly been accepted by a journal
        '''
        newly_finished = []
        for code in sorted(glance_codes - already_finished):
            try:
                if self.is_accepted_by_journal(code):
                    log.info(f"{code} has been accepted by a journal.")
                    newly_finished.append(code)
            except Exception as e:
                log.warning(f"Could not determine publication status for {code}: {e}")
        return newly_finished
