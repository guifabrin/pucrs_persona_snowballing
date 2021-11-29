import json

import helper

import helper_cited
import helper_references

config = helper.get_config()

__lines = []
__considered = []

def print_result(doi, key, result):
    global __lines, __considered
    total = result['total'][doi]
    considered_doi = result['considered_doi'][doi]
    not_considered_doi = result['not_considered_doi'][doi]
    considered_location = result['considered_location'][doi]
    not_considered_location = result['not_considered_location'][doi]
    not_considered_duplicates = result['not_considered_duplicates'][doi]
    considered = result['considered'][doi]

    considered_doi_count = len(considered_doi)
    if considered_doi_count + not_considered_doi != total:
        helper.log("[ERROR]", doi, key, "[DOI]", considered_doi_count + not_considered_doi, total)

    helper.log("[METRIC]", doi, key, "[DOI][ OK]", considered_doi_count)
    helper.log("[METRIC]", doi, key, "[DOI][NOK]", not_considered_doi)

    considered_location_count = len(considered_location)
    if considered_location_count + not_considered_location != considered_doi_count:
        helper.log("[ERROR]", doi, key, "[LOCATION]", considered_location_count + not_considered_location, total)

    helper.log("[METRIC]", doi, key, "[LOCATION][ OK]", considered_location_count)
    helper.log("[METRIC]", doi, key, "[LOCATION][NOK]", not_considered_location)

    considered_count = len(considered)
    if considered_count + not_considered_duplicates != considered_location_count:
        helper.log("[ERROR]", doi, key, "[LOCATION]", considered_count + not_considered_duplicates, total)

    helper.log("[METRIC]", doi, key, "[DUPLICATES][NOK]", not_considered_duplicates)
    helper.log("[METRIC]", doi, key, considered_count," of ", total)

    __lines.append(','.join([
        str(doi),
        str(considered_doi_count),
        str(not_considered_doi),
        str(considered_location_count),
        str(not_considered_location),
        str(not_considered_duplicates),
        str(considered_count),
        str(total)
    ]))
    for item in considered:
        __considered.append(item["doi"])
    helper.log("")


for starter_doi in config['starter_set']:
    result_references = helper_references.get(starter_doi, __considered)
    result_citations = helper_cited.get(starter_doi, __considered)
    print_result(starter_doi, '[REFERENCE]', result_references)
    print_result(starter_doi, '[CITATIONS]', result_citations)
    helper.write_file("result_back.json", json.dumps(result_references['considered']))
    helper.write_file("result_front.json", json.dumps(result_citations['considered']))

helper.write_file("result.csv", '\n'.join(__lines))
helper.write_log()
