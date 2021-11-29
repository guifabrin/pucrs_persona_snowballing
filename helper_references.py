import hashlib
from urllib import parse

import validators
from thefuzz import fuzz

import helper
import helper_base


def get_doi_informations(doi, scrapper_references=False):
    if not doi:
        return None
    config = helper.get_config()
    helper.log("\n[INFO] Getting doi information of", doi)
    informations = helper.get_doi_informations(doi)
    if scrapper_references:
        informations["references"] = []
        references = helper.get_references(informations['link'][0]['URL'])
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
                        helper.log('[WARN] Reference of type', key, link)
                    if reference_doi:
                        break
            if not reference_doi:
                reference_doi = helper.find_doi_by_text(reference['title'])
            info = None
            if reference_doi:
                helper.log("[INFO] Getting informations of: ", reference['title'])
                try:
                    info = get_doi_informations(reference_doi)
                    ratio = fuzz.ratio(reference['title'], info['title'] + " " + (' '.join(info['subtitle'])))
                    helper.log("[INFO] DOI Ratio", ratio)
                    if ratio < 50:
                        helper.log("[WARN] Could not be the same: \t", reference['title'], " \t", info['title'])
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


def get(starter_doi, __considered):
    total = {}
    considered_doi = {}
    not_considered_doi = {}
    considered_doi[starter_doi] = []
    not_considered_doi[starter_doi] = 0
    starter_info = get_doi_informations(starter_doi, True)
    total[starter_doi] = len(starter_info["references"])
    for reference in starter_info["references"]:
        if reference["doi"]:
            considered_doi[starter_doi].append(reference)
        else:
            not_considered_doi[starter_doi] += 1
    info_base = helper_base.check_considered_with_doi(considered_doi, __considered)
    info_base["considered_doi"] = considered_doi
    info_base["not_considered_doi"] = not_considered_doi
    info_base["total"] = total
    return info_base
