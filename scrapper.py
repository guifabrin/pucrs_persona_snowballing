import json

from helper import get_config, write_log, write_file
from extractors import extract

config = get_config()
results = []
for doi in config['starter_set']:
    results.append(extract(doi, True, True))

write_file('results\\scrapper_result.json', json.dumps({
    'results': results
}))
write_log("scrapper_log.txt")

