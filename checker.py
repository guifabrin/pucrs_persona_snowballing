import json
import os

import helper

__considered = {}


def process_list(ref, r_accepted=[], r_rejected = []):
    total_ok = len(list(filter(lambda i: i, ref['items'])))
    duplicates = 0
    location_ok = 0
    location_manually_ok = 0
    location_manually_false = 0
    r_doi_accepted = list(map(lambda i:i['doi'], r_accepted))
    r_doi_rejected = list(map(lambda i:i['doi'], r_rejected))
    for item in ref['items']:
        if not item:
            continue
        title_1 = ''
        location_1 = ''
        location_2 = ''
        if item['doi'] in __considered:
            duplicates += 1
            continue
        if item['doi'] in config['starter_set']:
            duplicates+=1
            continue
        if 'doi_reference' in item:
            if 'title' in item['doi_reference']:
                title_1 = item['doi_reference']['title']
            if 'container-title' in item['doi_reference']:
                location_1 = item['doi_reference']['container-title']
        if 'location' in item:
            location_2 = item['location']
        for event in config['allowed_event']:
            l_event = event.lower()
            if l_event in title_1 or l_event in location_1 or l_event in location_2:
                location_ok += 1
                __considered[item['doi']] = item
                if item['doi'] in r_doi_accepted:
                    location_manually_ok+=1
                if item['doi'] in r_doi_rejected:
                    location_manually_false+=1
                break
    return [str(ref['total']), str(total_ok), str(duplicates), str(location_ok), str(location_manually_ok), str(location_manually_false)]


config = helper.get_config()
json_results = json.loads(helper.read_file('results\\scrapper_result.json'))
metrics = ['doi,total,ref_total_with_doi,ref_duplicates,ref_auto_location,manual_location,ref_manual_location_false,cit_total,cit_total_with_doi,cit_duplicates,cit_auto_location,cit_manual_location,cit_manual_location_false']
for starter_doi in config['starter_set']:
    for result in json_results['results']:
        if starter_doi == result['doi']:
            metrics.append(result['doi'] + "," + ','.join(process_list(result['references'])) + "," + ','.join(
                process_list(result['citations'])))
helper.write_file("results\\screpper_metrics.csv", '\n'.join(metrics))

temp_accepted = json.loads(helper.read_file('results\\manually_location_accepted.json', '{"results":[]}'))['results']
temp_rejected = json.loads(helper.read_file('results\\manually_location_rejected.json', '{"results":[]}'))['results']
scores = list(map(lambda i: [i['doi'],i['score']], temp_accepted))
scores.extend(list(map(lambda i: [i['doi'],i['score']], temp_rejected)))
json_scores = {}
for item in scores:
    json_scores[item[0]] = item[1]

for time in range(0, 3):
    for doi, item in __considered.items():
        if json_scores[doi] == -3 or json_scores[doi] == 3:
            item['score'] = json_scores[doi]
            continue
        if 'score' not in item:
            item['score'] = 0
        title_1 = ''
        location_1 = ''
        location_2 = ''
        abstract = ''
        if 'doi_reference' in item:
            if 'title' in item['doi_reference']:
                title_1 = item['doi_reference']['title']
            if 'container-title' in item['doi_reference']:
                location_1 = ''.join(item['doi_reference']['container-title'])
        if 'location' in item:
            location_2 = item['location']
        if 'abstract' in item:
            abstract = item['abstract']
        if len(abstract) > 3000:
            abstract = 'error'
        input_val = None
        while True:
            print("\n" * 150)
            helper.log("[DEBUG] '' or 0 - accept, 1-rejected location")
            helper.log("[DEBUG] title_1:", title_1.strip())
            helper.log("[DEBUG] location_1", location_1.strip())
            helper.log("[DEBUG] location_2", location_2.strip())
            input_val = helper.iinput()
            if input_val in ['', '0', '1']:
                break

        if input_val == '' or input_val == '0':
            item['score'] += 1
        else:
            item['score'] -= 1

accepted = []
rejected = []
for doi, item in __considered.items():
    if item['score'] > 0:
        accepted.append(item)
    else:
        rejected.append(item)

helper.write_file("results\\manually_location_accepted.json", json.dumps({
    'results': accepted
}))
helper.write_file("results\\manually_location_rejected.json", json.dumps({
    'results': rejected
}))

__considered = {}
metrics = ['doi,total,ref_total_with_doi,ref_duplicates,ref_auto_location,manual_location,ref_manual_location_false,cit_total,cit_total_with_doi,cit_duplicates,cit_auto_location,cit_manual_location,cit_manual_location_false']
for starter_doi in config['starter_set']:
    for result in json_results['results']:
        if starter_doi == result['doi']:
            metrics.append(result['doi'] + "," + ','.join(process_list(result['references'], accepted, rejected)) + "," + ','.join(
                process_list(result['citations'], accepted, rejected)))
helper.write_file("results\\metrics_manually_location.csv", '\n'.join(metrics))

for item in accepted:
    if 'doi_reference' in item and 'link' in item['doi_reference']:
        helper.log("[INFO]", item['doi_reference']['link'][0]['URL'])
    else:
        helper.log("[INFO]", item['doi'])

helper.write_log("checker_log.txt")
