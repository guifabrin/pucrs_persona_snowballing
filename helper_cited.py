import helper
import helper_base


def get(starter_doi, __considered):
    total = {}
    considered_doi = {}
    not_considered_doi = {}
    considered_doi[starter_doi] = []
    not_considered_doi[starter_doi] = 0
    citations = helper.get_acm_cited_by(starter_doi)
    citations_count = len(citations)
    total[starter_doi] = citations_count
    for citation in citations:
        if citation["doi"]:
            considered_doi[starter_doi].append(citation)
        else:
            not_considered_doi[starter_doi] += 1
    info_base = helper_base.check_considered_with_doi(considered_doi, __considered)
    info_base["considered_doi"] = considered_doi
    info_base["not_considered_doi"] = not_considered_doi
    info_base["total"] = total
    return info_base
