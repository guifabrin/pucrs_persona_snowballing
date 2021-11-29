import hashlib
import json
import re
from urllib import parse

from thefuzz import fuzz

import helper
import validators

config = helper.get_config()

citations_total = 0
references_total = 0


def get_doi_informations(doi, scrapper_references=False):
    if not doi:
        return None
    helper.log("\n[INFO] Getting doi information of", doi)
    global references_total
    informations = helper.get_doi_informations(doi)
    if scrapper_references:
        informations["references"] = []
        references = helper.get_references(informations['link'][0]['URL'])
        references_count = len(references)
        references_total += references_count
        for reference in references:
            md5 = hashlib.md5(reference["title"].replace(" ", "").encode()).hexdigest()
            if md5 in config["manually_doi"]:
                reference_doi = config["manually_doi"][md5]
            else:
                reference_doi = None
                for key, link in reference["links"].items():
                    if key == "google-scholar":
                        query = parse.parse_qsl(parse.urlsplit(link).query)
                        text_ref = list(filter(lambda item: item[0] == "q", query))[0][1]
                        words = text_ref.split(' ')
                        for word in words:
                            word_length = len(word)
                            if word_length > 1:
                                if word[word_length - 1] == '.':
                                    word = word[0:word_length - 2]
                            is_url = validators.url(word)
                            if is_url:
                                pass
                            elif '/' in word and '.' in word:
                                reference_doi = word.replace('doi=', '')
                                break
                    else:
                        print('[WARN] Reference of type', key, link)
                    if reference_doi:
                        break
            if not reference_doi:
                reference_doi = helper.find_doi_by_text(reference['title'])
            info = None
            if reference_doi:
                helper.log("[INFO] Getting informations of: ", reference['title'])
                try:
                    info = get_doi_informations(reference_doi)
                    ratio = fuzz.ratio(reference['title'], info['title']+" "+(' '.join(info['subtitle'])))
                    helper.log("[INFO] DOI Ratio", ratio)
                    if ratio < 50:
                        helper.log("[WARN] Could not be the same: \t", reference['title']," \t", info['title'])
                except Exception as e:
                    helper.log("[ERROR] DOI not working, Title: ", reference['title'], e)
                    helper.log("[INPUT] Manual entry for: ", reference['title'])
                    # input_doi = input()
                    # if input_doi:
                    #     helper.set_config("manually_doi", md5, input_doi)
                    #     reference_doi = input_doi
                    # else:
                    reference_doi = None
                if reference_doi:
                    reference_doi = helper.find_doi_by_text(reference['title'])
                informations["references"].append({
                    "title": reference['title'],
                    "doi": reference_doi,
                    "informations": info
                })
    return informations


considered_references = []
not_considered_references = []
for starter_doi in config['starter_set']:
    starter_info = get_doi_informations(starter_doi, True)
    for reference in starter_info["references"]:
        for item in config["allowed_event"]:
            if "informations" in reference and reference["informations"]:
                if item in reference["informations"]["container-title"]:
                    considered_references.append(reference)
                    break
            else:
                if item in reference["title"]:
                    considered_references.append(reference)
                    break
        if reference not in considered_references:
            not_considered_references.append(reference)

print('\n\n')

considered_references_with_doi = {}
for reference in considered_references:
    considered_references_with_doi[reference["doi"]] = reference

considered_references = []
for key, value in considered_references_with_doi.items():
    considered_references.append(value)

not_considered_references_with_doi = {}
for reference in not_considered_references:
    not_considered_references_with_doi[reference["doi"]] = reference

not_considered_references = []
for key, value in not_considered_references_with_doi.items():
    not_considered_references.append(value)

helper.write_file("back_references.json", json.dumps(considered_references))

considered_citations = []
not_considered_citations = []
for reference in starter_info["references"]:
    if reference["doi"]:
        citations = helper._get_acm_cited_by(reference["doi"])
        citations_count = len(citations)
        citations_total += citations_count
        reference['citations'] = citations
        reference['citations_count'] = citations_count
        helper.log("[INFO] Count citations for:", reference["title"], citations_count)
        for citation in citations:
            for item in config["allowed_event"]:
                if "informations" in citation and citation["informations"]:
                    if item in citation["informations"]["container-title"]:
                        considered_citations.append(citation)
                        break
                else:
                    if item in citation["title"]:
                        considered_citations.append(citation)
                        break
            if citation not in considered_citations:
                not_considered_citations.append(citation)

considered_citations_with_doi = {}
for citation in considered_citations:
    considered_citations_with_doi[citation["doi"]] = citation

considered_citations = []
for key, value in considered_citations_with_doi.items():
    considered_citations.append(value)

not_considered_citations_with_doi = {}
for citation in not_considered_citations:
    not_considered_citations_with_doi[citation["doi"]] = citation

not_considered_citations = []
for key, value in not_considered_citations_with_doi.items():
    not_considered_citations.append(value)

helper.write_file("front_references.json", json.dumps(considered_citations))

helper.log("\n\n[INFO] Considered references:", len(considered_references))
helper.log("[INFO] Not considered references:", len(not_considered_references))
helper.log("[INFO] Duplicates references:", references_total - len(not_considered_references) - len(considered_references))
helper.log("[INFO] Total references", references_total)

helper.log("\n\n[INFO] Considered citations:", len(considered_citations))
helper.log("[INFO] Not considered citations:", len(not_considered_citations))
helper.log("[INFO] Duplicates citations:", citations_total - len(not_considered_citations) - len(considered_citations))
helper.log("[INFO] Total citations", citations_total)

print('\n\n')
for reference in considered_references:
    if reference and reference["informations"]:
        helper.log("[INFO] ",reference["doi"], reference["title"])
for citation in considered_citations:
    if citation and citation["informations"]:
        helper.log("[INFO] ",citation["doi"], citation["title"])