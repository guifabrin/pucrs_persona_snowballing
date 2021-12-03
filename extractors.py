import hashlib
import traceback

import bs4
import json
from urllib import parse

import validators

from helper import request_cache, log, get_config, set_config, increment_ref, iinput


def _extract_acm_references(parsed_html):
    references = []
    config = get_config()
    li_items = parsed_html.find_all("li", {"class": "references__item"})
    for item in li_items:
        reference_doi = None
        title = item.find('span', {"class": "references__note"}).contents[0]
        md5_hash_title = hashlib.md5(title.replace(" ", "").encode()).hexdigest()
        if md5_hash_title in config["manually_doi"]:
            reference_doi = config["manually_doi"][md5_hash_title]
            if reference_doi != "" and not reference_doi:
                continue
        else:
            for reference_link in item.find('span', {"class": "references__suffix"}).find_all('a'):
                if "google-scholar" in reference_link["class"]:
                    query = parse.parse_qsl(parse.urlsplit(reference_link["href"]).query)
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
        if not reference_doi:
            log("[INPUT] Manual doi entry for: ", title)
            # input_doi = input()
            # if input_doi:
            #     set_config("manually_doi", md5_hash_title, input_doi)
            #     reference_doi = input_doi
            # else:
            #     set_config("manually_doi", md5_hash_title, False)
        if reference_doi:
            references.append(extract(reference_doi))
    return {
        'total': len(li_items),
        'items': references
    }


def _get_acm_cited_by(parent_doi):
    url = "https://dl.acm.org/action/ajaxShowCitedBy?ajax=true&doi=" + parent_doi + "&pbContext=;taxonomy:taxonomy:conference-collections;wgroup:string:ACM Publication Websites;groupTopic:topic:acm-pubtype"
    text = request_cache(url)
    html = bs4.BeautifulSoup(text, features="html.parser")
    html_items = html.find_all('li', 'references__item')

    def map_fn(li):
        doi = None
        doi_el = li.find('span', {"class": "doi"})
        title_el = li.find('span', {"class": "references__article-title"})
        if title_el:
            if doi_el:
                doi = doi_el.text
            if not doi:
                links = list(filter(lambda link: "doi/" in link["href"] or "doi.org" in link["href"], li.find_all('a')))
                if len(links):
                    doi = links[0]["href"].replace('https://doi.org/', '').replace('/doi/', '')
            if not doi:
                doi = _find_doi_by_text(title_el.text)
            return extract(doi) if doi else None

    return {
        'total': len(html_items),
        'items': list(filter(lambda item: item, map(map_fn, html_items)))
    }


def _hindawi_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    h4s_abstracts = list(filter(lambda h4: h4.text == "Abstract", parsed_html.find_all('h4')))
    if len(h4s_abstracts):
        reference['abstract'] = h4s_abstracts[0].parent.contents[1]
    if extract_references:
        raise Exception('hindawi extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('hindawi extractor does not have extraction of citations')
    return reference

def _tandfonline_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    el_abstract = parsed_html.find('div',{'class':'abstractSection'})
    if len(el_abstract):
        reference['abstract'] = el_abstract.text
    if extract_references:
        raise Exception('tandfonline extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('tandfonline extractor does not have extraction of citations')
    return reference

def _intechopen_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    h2s_abstracts = list(filter(lambda h2: h2.text == "Abstract", parsed_html.find_all('h2')))
    if len(h2s_abstracts):
        reference['abstract'] = h2s_abstracts[0].parent.contents[1].text
    if extract_references:
        raise Exception('iopscience extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('iopscience extractor does not have extraction of citations')
    return reference

def _iopscience_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    el_abstract = parsed_html.find_all('div', {"class": "article-text"})
    if el_abstract:
        reference['abstract'] = el_abstract.text
    el_conference = parsed_html.find_all('div', {"class": "event_breadcrumb"})
    if el_conference:
        reference['location'] = el_conference.text
    if extract_references:
        raise Exception('iopscience extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('iopscience extractor does not have extraction of citations')
    return reference


def _iospress_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    spans_abstracts = list(filter(lambda span: span.text == "Abstract: ", parsed_html.find_all('span')))
    if len(spans_abstracts):
        reference['abstract'] = spans_abstracts[0].parent.contents[1].text
    spans_journals = list(filter(lambda span: span.text == "Journal: ", parsed_html.find_all('span')))
    if len(spans_journals):
        reference['location'] = spans_journals[0].parent.contents[1].text
    if extract_references:
        raise Exception('iospress extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('iospress extractor does not have extraction of citations')
    return reference


def _morganclaypool_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    el_abstract = parsed_html.find('div', {'class', 'hlFld-Abstract'})
    if el_abstract:
        reference['abstract'] = el_abstract.text
    if extract_references:
        raise Exception('morganclaypool researchgate does not have extraction of references')
    if extract_citated_by:
        raise Exception('morganclaypool researchgate does not have extraction of citations')
    return reference


def _sciencedirect_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    el_abstract = parsed_html.find('div', {'class', 'abstract'})
    if el_abstract:
        reference['abstract'] = el_abstract.text
    if extract_references:
        raise Exception('researchgate researchgate does not have extraction of references')
    if extract_citated_by:
        raise Exception('researchgate researchgate does not have extraction of citations')
    return reference


def _elsevier_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    url = parsed_html.find_all('link')[1]["href"]
    return extract(doi, extract_references, extract_citated_by, url)


def _researchgate_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    el_abstract = parsed_html.find('div', {'itemprop': 'description'})
    if el_abstract:
        reference['abstract'] = el_abstract.text
    el_conference = parsed_html.find('div', {'class': 'research-detail-header-section__metadata'})
    if el_conference:
        reference['location'] = el_conference.text
    if extract_references:
        raise Exception('researchgate researchgate does not have extraction of references')
    if extract_citated_by:
        raise Exception('researchgate researchgate does not have extraction of citations')
    return reference


def _sciendo_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    el_abstract = parsed_html.find('div', {'id': 'pane-2'})
    reference = {}
    if el_abstract:
        reference['abstract'] = el_abstract.text
    el_conference = parsed_html.find('h6')
    if el_conference:
        reference['location'] = el_conference.text
    if extract_references:
        raise Exception('sciendo extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('sciendo extractor does not have extraction of citations')
    return reference


def _springer_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    el_conference = parsed_html.find('a', {'data-test': 'ConfSeriesLink'})
    el_abstract = parsed_html.find('section', {'class': 'Abstract'})
    el_boot_title = parsed_html.find('span', {'class': 'BookTitle'})
    reference['location'] = ''
    if el_conference:
        reference['location'] += el_conference.text + " "
    elif el_boot_title:
        reference['location'] += el_boot_title.text + " "
    if el_abstract:
        reference['abstract'] = el_abstract.text
    if extract_references:
        raise Exception('springer extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('springer extractor does not have extraction of citations')
    return reference


def _igi_global_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    reference = {}
    h2s_abstracts = list(filter(lambda h2: h2.text == "Abstract", parsed_html.find_all('h2')))
    if len(h2s_abstracts):
        reference['abstract'] = h2s_abstracts[0].parent.contents[1].text
    spans_sources = list(filter(lambda h2: h2.text == "Source Title: ", parsed_html.find_all('span')))
    if len(spans_sources):
        reference['location'] = spans_sources[0].parent.contents[1].text
    if extract_references:
        raise Exception('igi_global extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('igi_global extractor does not have extraction of citations')
    return reference


def _ietresearch_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    abstract = parsed_html.find("div", {"class": "section__content"})
    reference = {}
    if abstract:
        reference['abstract'] = abstract.text
    details = parsed_html.find("div", {"class": "issue-item__detail"})
    if details:
        reference['location'] = details.text
    if extract_references:
        raise Exception('ietresearch extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('ietresearch extractor does not have extraction of citations')
    return reference


def _acm_extractor(doi, url, extract_references=False, extract_citated_by=False):
    html_response = request_cache(url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    abstract = parsed_html.find("div", {"class": "abstractInFull"})
    reference = {}
    if abstract:
        reference['abstract'] = abstract.text
    details = parsed_html.find("div", {"class": "issue-item__detail"})
    if details:
        reference['location'] = details.text
    if extract_references:
        reference['references'] = _extract_acm_references(parsed_html)
    if extract_citated_by:
        reference['citations'] = _get_acm_cited_by(doi)
    return reference


def _ieee_extractor(doi, url, extract_references=False, extract_citated_by=False):
    if 'xplorestaging' in url:
        basename = 'xplorestaging'
    elif 'ieeexplore' in url:
        basename = 'ieeexplore'
    else:
        raise Exception('basename is undefined')
    url_parts = url.split('/')
    main_url = "https://" + basename + ".ieee.org/document/" + str(url_parts[len(url_parts) - 1])
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Referer': main_url
    }
    html_response = request_cache(main_url)
    parsed_html = bs4.BeautifulSoup(html_response, features="html.parser")
    abstract_response = request_cache(main_url + "/snippet", headers=headers)
    parsed_abstract = bs4.BeautifulSoup(abstract_response, features="html.parser")
    reference = {
        'abstract': parsed_abstract.text
    }
    script_tags = parsed_html.find_all("script")
    script_with_info = list(filter(lambda el: "xplGlobal.document.metadata" in el.text, script_tags))
    try:
        text_info = script_with_info[0].text.split('xplGlobal.document.metadata=')[1].replace(';', '')
        json_info = json.loads(text_info)
        reference['location'] = json_info['publicationTitle']
    except:
        raise Exception('ieee extractor error parsing')
    if extract_references:
        raise Exception('ieee extractor does not have extraction of references')
    if extract_citated_by:
        raise Exception('ieee extractor does not have extraction of citations')
    return reference


def _find_doi_by_text(text):
    doi = None
    log("[INFO] Trying find doi with text:", text)
    html_response = request_cache("https://apps.crossref.org/SimpleTextQuery", "POST",
                                  data={'freetext': text, 'command': 'Submit'}, cookies=True)
    html = bs4.BeautifulSoup(html_response, features="html.parser")
    links = html.find_all("a")
    links_with_doi = list(filter(lambda link: "doi.org" in link["href"], links))
    if len(links_with_doi):
        protocol, doi = links_with_doi[0]["href"].split('doi.org/')
    if doi:
        log("[SUCCESS] DOI found:", doi, text)
    else:
        log("[WARN] DOI not found:", text)
    return doi


def _get_doi_reference(doi):
    try:
        text = request_cache("https://doi.org/" + doi, method="GET", headers={
            'Accept': 'application/json'
        })
        log("[SUCCESS] Loaded via DOI", doi)
        return json.loads(text)
    except:
        log("[WARN] Not loaded via DOI", doi)
        return {}


def _resolve_url(doi):
    config = get_config()
    if "resolved_uri" not in config:
        config["resolved_uri"] = {}
    if doi in config["resolved_uri"]:
        return config["resolved_uri"][doi]
    url = ''
    doi_reference = _get_doi_reference(doi)
    if 'link' in doi_reference:
        if len(doi_reference['link']):
            url = doi_reference['link'][0]['URL']

    if 'link.springer.com' in url:
        url = "https://link.springer.com/" + doi
    elif 'xplorestaging.ieee.org' in url:
        query = parse.parse_qsl(parse.urlsplit(url).query)
        number = list(filter(lambda q: q[0] == "arnumber", query))[0][1]
        url = "https://ieeexplore.ieee.org/document/" + str(number)
    elif 'onlinelibrary.wiley.com' in url:
        url = 'https://ietresearch.onlinelibrary.wiley.com/doi/' + doi
    elif 'hindawi.com' in url:
        url = url.replace('downloads.', '').replace('.pdf', '')
    elif 'dl.acm.org' in url:
        url = 'https://dl.acm.org/doi/' + doi
    elif 'tandfonline.com' in url:
        url = 'https://www.tandfonline.com/doi/abs/'+doi
    if not url:
        raise Exception('URL not defined for', doi)
    return url


def extract(doi, extract_references=False, extract_citated_by=False, resolved_uri=None, tries=0):
    if tries==0:
        increment_ref()
    url = ''
    try:
        if resolved_uri:
            url = resolved_uri
        else:
            url = _resolve_url(doi)
        if url != "" and not url:
            return None
        if 'ieeexplore.ieee.org' in url:
            reference = _ieee_extractor(doi, url, extract_references, extract_citated_by)
        elif 'dl.acm.org' in url:
            reference = _acm_extractor(doi, url, extract_references, extract_citated_by)
        elif 'ietresearch.onlinelibrary.wiley.com' in url:
            reference = _ietresearch_extractor(doi, url, extract_references, extract_citated_by)
        elif 'igi-global.com' in url:
            reference = _igi_global_extractor(doi, url, extract_references, extract_citated_by)
        elif 'springer.com' in url:
            reference = _springer_extractor(doi, url, extract_references, extract_citated_by)
        elif 'hindawi.com' in url:
            reference = _hindawi_extractor(doi, url, extract_references, extract_citated_by)
        elif 'sciendo.com' in url:
            reference = _sciendo_extractor(doi, url, extract_references, extract_citated_by)
        elif 'researchgate.net' in url:
            reference = _researchgate_extractor(doi, url, extract_references, extract_citated_by)
        elif 'elsevier.com' in url:
            reference = _elsevier_extractor(doi, url, extract_references, extract_citated_by)
        elif 'sciencedirect' in url:
            reference = _sciencedirect_extractor(doi, url, extract_references, extract_citated_by)
        elif 'morganclaypool.com' in url:
            reference = _morganclaypool_extractor(doi, url, extract_references, extract_citated_by)
        elif 'iospress.com' in url:
            reference = _iospress_extractor(doi, url, extract_references, extract_citated_by)
        elif 'iopscience.iop.org' in url:
            reference = _iopscience_extractor(doi, url, extract_references, extract_citated_by)
        elif 'intechopen.com' in url:
            reference = _intechopen_extractor(doi, url, extract_references, extract_citated_by)
        elif 'tandfonline.com' in url:
            reference = _tandfonline_extractor(doi, url, extract_references, extract_citated_by)
        else:
            raise Exception('Extractor not defined', doi, url)
        reference['doi'] = doi
        reference['doi_reference'] = _get_doi_reference(doi)
        set_config("resolved_uri", doi, url)
        return reference
    except Exception as e:
        log("[WARN]", doi, "error at extractor", url, e)
        if 'dl.acm.org' not in url:
            log("[INFO]", doi, "trying with ACM")
            return extract(doi, extract_references, extract_citated_by, "https://dl.acm.org/doi/" + doi)
        else:
            log("[ERROR]", doi, "not works.", traceback.print_exc())
            if tries == 0:
                log("[INPUT]", "Manual url entry for:", doi)
                input_url = iinput()
                if input_url:
                    set_config("resolved_uri", doi, input_url)
                    extract(doi, tries=tries + 1)
                else:
                    set_config("resolved_uri", doi, False)
