import datetime
import base64
import logging
import re
import requests
from proxyUtil import get_proxies_from_url, tagsChanger # Import specific functions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def checkURL(url):
    try:
        r = requests.head(url, timeout=3)
        return r.status_code // 100 == 2
    except requests.exceptions.RequestException:
        return False


output = []
all_proxies = []

with open("nodes.md", encoding="utf8") as file:
    lines = file.readlines()

# We process the lines in memory to update them
processed_lines = []
header_count = 0
for line in lines:
    line = line.strip()
    if line.startswith("|"):
        if header_count > 1: # Skip header and separator lines
            parts = line.split('|')
            if len(parts) > 3:
                url = parts[3].strip()
                
                status_ok = checkURL(url)
                status_icon = "✅" if status_ok else "❌"
                
                # Scrape proxies only if URL is accessible
                p = []
                if status_ok:
                    p = get_proxies_from_url(url)
                
                all_proxies.extend(p)
                
                # Reconstruct the line with updated info
                parts[1] = f" {status_icon} "
                parts[2] = f" {len(p)} "
                line = "|".join(parts)
        header_count += 1
    processed_lines.append(line)

with open("nodes.md", "w", encoding="utf8") as f:
    f.write('\n'.join(processed_lines))
    f.write('\n') # Add a newline at the end of the file

TAGs = ["4FreeIran", "4Nika", "4Sarina", "4Jadi", "4Kian", "4Mohsen"]
cur_tag = TAGs[datetime.datetime.now().hour % len(TAGs)]

# Remove duplicates and sort
unique_proxies = sorted(list(set(all_proxies)))

# Change tags
lines = tagsChanger(unique_proxies, cur_tag)
lines = tagsChanger(lines, cur_tag, True)

# فقط پراکسی‌های ss رو جدا می‌کنیم
ss  = [*filter(lambda s: s.startswith("ss://"), lines)]

# فایل all که شامل همه پراکسی‌هاست ساخته می‌شه
with open('all', 'wb') as f:
    f.write(base64.b64encode('\n'.join(lines).encode('utf-8')))

# فایل ss ساخته می‌شه (بدون پسوند .txt)
with open('ss', 'wb') as f: # <-- این خط تغییر کرد
    f.write(base64.b64encode('\n'.join(ss).encode('utf-8')))
