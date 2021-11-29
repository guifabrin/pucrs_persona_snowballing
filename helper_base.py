import helper


def check_considered_with_doi(considered_doi, __considered):
    config = helper.get_config()

    _considered = []
    considered_location = {}
    considered = {}
    not_considered_location = {}
    not_considered_duplicates = {}

    for starter_doi, references in considered_doi.items():
        considered_location[starter_doi] = []
        not_considered_location[starter_doi] = 0
        for reference in references:
            b_considered = False
            for item in config["allowed_event"]:
                if ("informations" in reference and reference["informations"] and item in reference["informations"][
                    "container-title"]) or (item in reference["title"]):
                    b_considered = True
                    considered_location[starter_doi].append(reference)
                    break
            if not b_considered:
                not_considered_location[starter_doi] += 1
    for starter_doi, references in considered_location.items():
        considered[starter_doi] = []
        not_considered_duplicates[starter_doi] = 0
        for reference in references:
            doi = reference["doi"]
            if doi in _considered or doi in __considered:
                not_considered_duplicates[starter_doi] += 1
            else:
                _considered.append(reference)
                considered[starter_doi].append(reference)
    return {
        'considered': considered,
        'considered_location': considered_location,
        'not_considered_location': not_considered_location,
        'not_considered_duplicates': not_considered_duplicates,
    }
