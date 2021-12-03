import hashlib
import json
import os

import requests
from requests_toolbelt.utils import dump
from termcolor import cprint

__config = None
__all_logs = []


def write_file(filename, data):
    if os.path.isfile(filename):
        log("[INFO] Removing file:", filename)
        os.unlink(filename)
    f = open(filename, "a", encoding="utf-8")
    f.write(data)
    f.close()
    return data


def read_file(filename, _default=None):
    if not os.path.isfile(filename):
        return _default
    f = open(filename, "r", encoding="utf-8")
    text = f.read()
    f.close()
    return text


def request_cache(url, method="GET", headers={}, data={}, cookies=False, only_content=True):
    path = "cache\\"
    os.makedirs(path, exist_ok=True)
    filename = method + '_' + url + '_' + json.dumps(headers) + '_' + json.dumps(data)
    filename_md5 = path + hashlib.md5(filename.encode()).hexdigest()
    headers['User-Agent'] = "PostmanRuntime/7.28.4"
    if os.path.isfile(filename_md5):
        log("[INFO] Using cache for:", method, url, headers, data)
        text = read_file(filename_md5)
        json_data = json.loads(text)
        if only_content:
            return json_data['content']
        else:
            return json_data
    else:
        log("[INFO] Requesting:", method, url, headers, data)
        my_cookies = {}
        if cookies:
            r1 = requests.get(url)
            my_cookies = r1.cookies
        response = requests.request(method, url, headers=headers, data=data, cookies=my_cookies, files=[])
        if response.status_code == 200 and response.text:
            result = {
                'content': response.text,
                'response': list(filter(lambda item: item,
                                        dump.dump_all(response, request_prefix=b'', response_prefix=b'').decode(
                                            'utf-8').replace('\r', '').split('\n')))
            }
            write_file(filename_md5, json.dumps(result))
            if only_content:
                return result['content']
            else:
                return result
        else:
            raise Exception('Error getting ' + url)


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
    if key not in __config:
        __config[key] = {}
    if subkey not in __config[key]:
        __config[key][subkey] = {}
    __config[key][subkey] = value
    save_config()

__ref = 0
def increment_ref():
    global __ref
    __ref+=1

def log(*args):
    global __all_logs, __ref
    text = "["+str(__ref)+"]"+(' '.join(map(lambda item: str(item), args)))
    __all_logs.append(text + "\n")
    if "[INFO]" in text:
        print(text)
        pass
    elif "[ERROR]" in text:
        cprint(text, 'red')
    elif "[WARN]" in text:
        cprint(text, 'yellow')
    elif "[SUCCESS]" in text:
        cprint(text, 'green')
    elif "[METRIC]" in text:
        cprint(text, 'blue')
    elif "[DEBUG" in text:
        color = text.split('[DEBUG')[1].split(']')[0].replace('-','')
        if not color:
            color ='cyan'
        cprint(text, color)
    else:
        print(text)


def write_log(filename="log.txt"):
    global __all_logs
    write_file("logs\\"+filename, ''.join(list(filter(lambda item: item.strip(), __all_logs))))


def iinput():
    text = input()
    log("[INPUTED]", text)
    return text