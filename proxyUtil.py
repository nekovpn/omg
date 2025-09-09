# This code is sourced from https://github.com/mheidari98/proxyUtil
# It has been modified to be self-contained and smarter.

import requests
import re
import base64
import json
import logging

def get_proxies_from_url(url):
    """
    Fetches proxies from a URL. It automatically handles both
    plain text and Base64 encoded content.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        content = response.text
        proxies = content.splitlines()

        # Check if it's likely a plain text list of proxies
        if any("://" in p for p in proxies):
            logging.info(f"Successfully scraped {len(proxies)} proxies as plain text from {url}")
            # Filter out any empty lines that might exist
            return [p for p in proxies if p.strip()]

        # If not, try to decode it as Base64
        try:
            # The content might have extra whitespace that needs to be removed
            decoded_content = base64.b64decode(content.strip()).decode('utf-8')
            decoded_proxies = decoded_content.splitlines()
            if any("://" in p for p in decoded_proxies):
                logging.info(f"Successfully scraped {len(decoded_proxies)} proxies as Base64 from {url}")
                return [p for p in decoded_proxies if p.strip()]
        except Exception:
            # It wasn't valid Base64, which is fine. It might just be an empty or invalid file.
            logging.warning(f"Content from {url} is not a valid proxy list or Base64. Skipping.")
            return []

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch URL {url}. Error: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {url}. Error: {e}")
        return []
    
    return [] # Return empty list if no proxies were found

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
