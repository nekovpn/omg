import datetime
import base64
import logging
import re
import requests
from proxyUtil import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def checkURL(url):
    try:
        r = requests.head(url, timeout=3)
    except:
        return False
    return r.status_code//100 == 2


output = []
proxy = []

with open("nodes.md", encoding="utf8") as file:
    cnt = 0
    while line := file.readline():
        line = line.rstrip()
        if line.startswith("|"):
            if cnt>1 :
                url = line.split('|')[-2]
                for _ in range(3):
                    if status := checkURL(url):
                        break
                status = "✅" if status else "❌"
                p = ScrapURL(url)
                proxy.extend(p)
                line = re.sub(r'^\|+?(.*?)\|+?(.*?)\|+?', f'| {status} | {len(p)} |', line, count=1)
            cnt+=1
        output.append(line)

with open("nodes.md", "w") as f:
    f.write('\n'.join(output))

TAGs = ["4FreeIran", "4Nika", "4Sarina", "4Jadi", "4Kian", "4Mohsen"]
cur_tag = TAGs[datetime.datetime.now().hour % len(TAGs)]

lines = tagsChanger(proxy, cur_tag)
lines = tagsChanger(sorted(set(lines)), cur_tag, True)

# فقط پراکسی‌های ss رو جدا می‌کنیم
ss  = [*filter(lambda s: s.startswith("ss://"), lines)]

# print([*map(len, [ss])]) # برای دیباگ کردن تعداد پراکسی‌های ss

# فایل all که شامل همه پراکسی‌هاست ساخته می‌شه
with open('all', 'wb') as f:
    f.write(base64.b64encode('\n'.join(lines).encode()))

# فقط فایل ss.txt ساخته می‌شه
with open('ss.txt', 'wb') as f:
    f.write(base64.b64encode('\n'.join(ss).encode()))

# بخش‌های مربوط به vmess, vless, trojan حذف شدند
# with open('vmess', 'wb') as f:
#     f.write(base64.b64encode('\n'.join(vmess).encode()))

# with open('vless', 'wb') as f:
#     f.write(base64.b64encode('\n'.join(vless).encode()))

# with open('trojan', 'wb') as f:
#     f.write(base64.b64encode('\n'.join(trojan).encode()))
