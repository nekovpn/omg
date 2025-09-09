# This code is sourced from https://github.com/mheidari98/proxyUtil
# It is included here to make the project self-contained.

import requests
import re
import base64
import json
import logging

def ScrapS(url):
    try:
        b = requests.get(url).content
        s = base64.b64decode(b).decode()
        return s.splitlines()
    except:
        return []

def ScrapURL(url):
    try:
        s = requests.get(url).text
        return s.splitlines()
    except:
        return []

def decodeJ(j):
    s = ""
    try:
        d = json.loads(j)
        if (protocol := d.get("protocol")):
            if protocol == "vmess":
                s = f"vmess://{base64.b64encode(json.dumps(d['settings']).encode()).decode()}"
            elif protocol == "vless":
                s = f"vless://{d['settings']['vnext'][0]['users'][0]['id']}@{d['settings']['vnext'][0]['address']}:{d['settings']['vnext'][0]['port']}?encryption=none&security=reality&sni={d['streamSettings']['realitySettings']['serverName']}&fp={d['streamSettings']['realitySettings']['fingerprint']}&pbk={d['streamSettings']['realitySettings']['publicKey']}&sid={d['streamSettings']['realitySettings']['shortId']}&type=tcp&headerType=none#{d['remarks']}"
            elif protocol == "trojan":
                s = f"trojan://{d['settings']['servers'][0]['password']}@{d['settings']['servers'][0]['address']}:{d['settings']['servers'][0]['port']}?security=tls&headerType=none&type=tcp#{d['remarks']}"
    except:
        logging.error(f"Error decoding json: {j}")
        pass
    return s

def tagsChanger(p, tag, force=False):
    output = []
    for s in p:
        try:
            if s.startswith("ss://"):
                s = re.sub(r'#.*', f"#{tag}", s, count=1)
            elif s.startswith("vmess://"):
                b = s.replace("vmess://", "")
                j = json.loads(base64.b64decode(b).decode())
                j['ps'] = tag
                if force:
                    output.append(f"vmess://{base64.b64encode(json.dumps(j).encode()).decode()}")
                else:
                    output.append(s)
            elif s.startswith("vless://"):
                s = re.sub(r'#.*', f"#{tag}", s, count=1)
            elif s.startswith("trojan://"):
                s = re.sub(r'#.*', f"#{tag}", s, count=1)
        except:
            logging.error(f"Error in tagsChanger: {s}")
            pass
    if force:
        return output
    return p

class v2rayChecker:
    def __init__(self, proxies_url:str, timeout:int = 1):
        self.proxies_url = proxies_url
        self.timeout = timeout
        self.proxies = []
        self.OKproxies = []

    def getProxies(self):
        self.proxies = ScrapS(self.proxies_url)
        return self.proxies

    def check(self, p:str):
        if (s := self.check_latency(p)):
            self.OKproxies.append((s,p))

    def check_latency(self, p: str):
        pass
