import hashlib
import json
import os

import bs4
import requests
from termcolor import cprint


def write_file(filename, data):
    f = open(filename, "a")
    f.write(data)
    f.close()
    return data


def read_file(filename):
    f = open(filename, "r")
    text = f.read()
    f.close()
    return text


def request_cache(url, method="GET", headers={}, data={}, cookies=False):
    path = "cache/"
    os.makedirs(path, exist_ok=True)
    filename_hash = url + json.dumps(headers) + json.dumps(data)
    md5 = hashlib.md5(filename_hash.encode())
    filename = path + md5.hexdigest() + ".html"
    if os.path.isfile(filename):
        return read_file(filename)
    else:
        my_cookies = {}
        if cookies:
            r1 = requests.get(url)
            my_cookies = r1.cookies
        response = requests.request(method, url, headers=headers, data=data, cookies=my_cookies, files=[])
        if response.status_code == 200:
            return write_file(filename, response.text)
        else:
            raise Exception('Error getting ' + url)


__config = None


def get_config():
    global __config
    if not __config:
        __config = json.loads(read_file("config.json"))
    return __config


def save_config():
    global __config
    with open("config.json", 'w') as outfile:
        json.dump(__config, outfile, indent=4, sort_keys=True)


def set_config(key, subkey, value):
    global __config
    if not __config:
        get_config()
    if not key in __config:
        __config[key] = {}
    if not subkey in __config[key]:
        __config[key][subkey] = {}
    __config[key][subkey] = value
    save_config()


def _get_acm_references(link):
    log("[INFO] Getting acm references of ", link)
    text = request_cache(link)
    html = bs4.BeautifulSoup(text, features="html.parser")
    references = []
    for item in html.find_all("li", {"class":"references__item"}):
        links = {}
        for reference_link in item.find('span', {"class":"references__suffix"}).find_all('a'):
            links[reference_link["class"][0]] = reference_link["href"]
        references.append({
            'title': item.find('span', {"class":"references__note"}).contents[0],
            'links': links
        })
    return references

def _get_acm_cited_by(dois):
    log("[INFO] Getting cited by:", dois)
    url = "https://dl.acm.org/action/ajaxShowCitedBy?ajax=true&doi=" + dois + "&pbContext=;taxonomy:taxonomy:conference-collections;wgroup:string:ACM Publication Websites;groupTopic:topic:acm-pubtype"
    response = requests.request("GET", url)
    html = bs4.BeautifulSoup(response.text, features="html.parser")
    html_items = html.find_all('li', 'references__item')

    def map_fn(li):
        doi_el = li.find('span', {"class":"doi"})
        title_el = li.find('span', {"class":"references__article-title"})
        info = None
        doi = None
        if title_el:
            if doi_el:
                doi = doi_el.text
            if not doi:
                links = list(filter(lambda link: "doi/" in link["href"] or "doi.org" in link["href"], li.find_all('a')))
                if len(links):
                    doi = links[0]["href"].replace('https://doi.org/','').replace('/doi/','')
            if len(doi)> 15:
                pass
            if not doi:
                doi = find_doi_by_text(title_el.text)
            if doi:
                info = get_doi_informations(doi)
            return {
                'title': title_el.text,
                'doi': doi,
                'informations': info
            }
    return list(filter(lambda item: item, map(map_fn, html_items)))


def get_references(link):
    if 'dl.acm.org' in link:
        return _get_acm_references(link)

def log(*args):
    text = ' '.join(map(lambda item: str(item), args))
    if "[INFO]" in text:
        print(text)
    elif "[ERROR]" in text:
        cprint(text,'red')
    elif "[WARN]" in text:
        cprint(text,'yellow')
    elif "[SUCCESS]" in text:
        cprint(text,'green')
    else:
        print(text)


def get_doi_informations(doi):
    log("[INFO] Getting information by:", doi)
    try:
        text = request_cache("https://doi.org/" + doi, method="GET", headers={
            'Accept': 'application/json'
        })
        log("[SUCCESS] Loaded via DOI", doi)
        return json.loads(text)
    except Exception as e:
        log("[INFO] Trying via ACM", doi)
        try:
            html_response = request_cache("https://dl.acm.org/doi/" + doi, method="GET")
            html = bs4.BeautifulSoup(html_response, features="html.parser")
            event = html.find("span", {"class": "container-title"})
            event_text = event.text if event else ''
            log("[SUCCESS] Loaded via ACM", doi)
            return {
                "container-title": event_text
            }
        except Exception as e:
            log("[ERROR] via ACM", e)
    return None


def find_doi_by_text(text):
    log("[INFO] Trying find doi with text:", text)
    html_response = request_cache("https://apps.crossref.org/SimpleTextQuery", "POST",
                                  data={'freetext': text, 'command': 'Submit'}, cookies=True)
    html = bs4.BeautifulSoup(html_response, features="html.parser")
    links = html.find_all("a")
    links_with_doi = list(filter(lambda link:"doi.org" in link["href"], links))
    doi = None
    if len(links_with_doi):
        protocol, doi = links_with_doi[0]["href"].split('doi.org/')
    if doi:
        log("[SUCCESS] DOI found:", doi, text)
    else:
        log("[WARN] DOI not found:", text)
    return doi
